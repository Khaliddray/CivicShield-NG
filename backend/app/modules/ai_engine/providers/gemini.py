"""Gemini Cloud AI Provider for Advanced Misinformation Analysis and Claim Grounding.

Uses Google Gemini API via HTTPX with zero-configuration fallback to LocalHeuristicAIProvider
when offline, unconfigured, or experiencing API rate limits.
"""

import json
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.common.enums import ClaimCategory, VerificationDecision
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.providers.local_heuristic import LocalHeuristicAIProvider

GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-1.5-flash"


class GeminiAIProvider(BaseAIProvider):
    """
    Production-grade AI provider leveraging Google's Gemini models for deep electoral analysis.
    Implements automatic and resilient fallback to LocalHeuristicAIProvider for 100% test & offline reliability.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        timeout_seconds: float = 8.0,
        fallback_provider: Optional[BaseAIProvider] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback_provider or LocalHeuristicAIProvider()

    @property
    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is present."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def _call_gemini_json(self, system_instruction: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Execute a generation call to Gemini REST API requesting structured JSON."""
        if not self.is_configured:
            return None

        url = f"{GEMINI_API_ENDPOINT}/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, json=payload)
                if response.status_code != 200:
                    logger.warning(
                        f"Gemini API returned status {response.status_code}: {response.text[:200]}. Falling back."
                    )
                    return None

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return None

                text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if not text_content:
                    return None

                return json.loads(text_content)
        except Exception as exc:
            logger.warning(f"Gemini API invocation failed ({exc}). Gracefully degrading to heuristic provider.")
            return None

    def extract_atomic_claims(self, text: str) -> List[str]:
        """Isolate discrete factual electoral statements from raw user narrative."""
        if not self.is_configured:
            return self.fallback.extract_atomic_claims(text)

        system_instruction = (
            "You are an electoral fact-checking analyst for CivicShield NG in Nigeria. "
            "Given citizen narrative text, extract 1 to 5 discrete, checkable atomic factual claims. "
            "Output JSON with schema: {\"claims\": [\"claim1\", \"claim2\"]}"
        )
        prompt = f"Extract atomic electoral factual claims from this text:\n\n{text}"

        result = self._call_gemini_json(system_instruction, prompt)
        if result and "claims" in result and isinstance(result["claims"], list) and result["claims"]:
            return [str(c).strip() for c in result["claims"] if str(c).strip()][:5]

        return self.fallback.extract_atomic_claims(text)

    def classify_electoral_category(self, claim_text: str) -> Dict[str, Any]:
        """Classify statement into electoral taxonomy with confidence score."""
        if not self.is_configured:
            return self.fallback.classify_electoral_category(claim_text)

        valid_categories = [c.value for c in ClaimCategory]
        system_instruction = (
            f"You are the classification component of CivicShield NG. "
            f"Allowed categories: {valid_categories}. "
            f"Classify the electoral claim. Output JSON schema: "
            f'{{"category": "CATEGORY_NAME", "confidence": 0.85, "matched_keywords": ["keyword1"]}}'
        )
        prompt = f"Classify this electoral claim:\n\n{claim_text}"

        result = self._call_gemini_json(system_instruction, prompt)
        if (
            result
            and result.get("category") in valid_categories
            and isinstance(result.get("confidence"), (int, float))
        ):
            return {
                "category": result["category"],
                "confidence": round(float(result["confidence"]), 2),
                "matched_keywords": result.get("matched_keywords", []),
            }

        return self.fallback.classify_electoral_category(claim_text)

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate semantic similarity score between two texts (0.0 to 1.0).
        Leverages fallback heuristic engine for instant, deterministic velocity computation.
        """
        # For clustering speed and high-throughput real-time polling, the local algorithm is optimal
        return self.fallback.calculate_similarity(text_a, text_b)

    def evaluate_claim_against_sources(
        self,
        claim_text: str,
        official_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate a claim against a reference set of official documents.
        Enforces strict nonpartisanship, human-in-the-loop requirement, and explicit uncertainty.
        """
        if not self.is_configured or not official_sources:
            return self.fallback.evaluate_claim_against_sources(claim_text, official_sources)

        sources_summary = [
            {
                "document_code": s.get("document_code"),
                "title": s.get("title"),
                "summary": s.get("summary"),
                "content_excerpt": (s.get("content_text") or "")[:300],
                "issuing_institution": s.get("issuing_institution"),
            }
            for s in official_sources[:10]
        ]

        system_instruction = (
            "You are CivicShield NG's evidence-grounding engine for Nigerian elections. "
            "Analyze the citizen claim strictly against the provided certified official documents. "
            "NON-NEGOTIABLE RULES:\n"
            "1. Strictly nonpartisan. Zero political bias.\n"
            "2. Never declare an authoritative final ruling - all claims require human Verification Officer review.\n"
            "3. If certified documents assert the opposite, set contradiction_suspected=true and ai_suggested_status='UNDER_REVIEW'.\n"
            "4. If no certified document matches, admit uncertainty, set ai_suggested_status='UNVERIFIED' or 'INSUFFICIENT_EVIDENCE'.\n"
            "5. Never hallucinate electoral dates, times, or guidelines.\n"
            "Output JSON schema:\n"
            "{\n"
            '  "extracted_claim": "...",\n'
            '  "category": "INEC_OPERATIONS",\n'
            '  "category_confidence": 0.9,\n'
            '  "ai_confidence_score": 0.8,\n'
            '  "ai_suggested_status": "UNDER_REVIEW",\n'
            '  "analysis_summary": "...",\n'
            '  "contradiction_suspected": false,\n'
            '  "top_matching_document_code": "INEC-...",\n'
            '  "recommended_next_action": "..."\n'
            "}"
        )

        prompt = (
            f"Claim to evaluate:\n{claim_text}\n\n"
            f"Certified Official Documents in Registry:\n{json.dumps(sources_summary, indent=2)}"
        )

        result = self._call_gemini_json(system_instruction, prompt)
        if (
            result
            and "ai_suggested_status" in result
            and "analysis_summary" in result
        ):
            # Resolve matched sources metadata
            top_code = result.get("top_matching_document_code")
            matched_sources = []
            for src in official_sources:
                sim = self.fallback.calculate_similarity(claim_text, src.get("title", ""))
                if src.get("document_code") == top_code:
                    sim = max(sim, float(result.get("ai_confidence_score", 0.75)))
                if sim > 0.15:
                    matched_sources.append({
                        "document_code": src.get("document_code"),
                        "title": src.get("title"),
                        "issuing_institution": src.get("issuing_institution"),
                        "similarity_score": round(sim, 2),
                    })
            matched_sources.sort(key=lambda x: x["similarity_score"], reverse=True)

            return {
                "extracted_claim": result.get("extracted_claim") or claim_text,
                "category": result.get("category") or ClaimCategory.GENERAL_ELECTORAL.value,
                "category_confidence": round(float(result.get("category_confidence", 0.75)), 2),
                "ai_confidence_score": round(float(result.get("ai_confidence_score", 0.50)), 2),
                "ai_suggested_status": result.get("ai_suggested_status") or VerificationDecision.UNDER_REVIEW.value,
                "analysis_summary": result.get("analysis_summary"),
                "sources_consulted": matched_sources[:5],
                "contradiction_suspected": bool(result.get("contradiction_suspected", False)),
                "recommended_next_action": result.get("recommended_next_action") or "Assign to Verification Officer for priority review.",
                "requires_human_review": True,  # Hard Invariant
            }

        return self.fallback.evaluate_claim_against_sources(claim_text, official_sources)
