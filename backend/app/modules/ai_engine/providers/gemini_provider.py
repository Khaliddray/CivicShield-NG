"""Google Gemini Cloud AI Provider for CivicShield NG (Section 11).

Provides integration with Google Gemini Generative Language REST API via httpx.
Features:
- Configurable via environment variable GEMINI_API_KEY
- Robust timeout handling (10s default)
- Exponential backoff retry on transient errors (HTTP 429 / 503)
- Defensive pre-processing via PromptDefense
- Strict Responsible AI system instructions
- Graceful degraded fallback to LocalHeuristicAIProvider on failure
"""

import json
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.providers.local_heuristic import LocalHeuristicAIProvider
from backend.app.modules.ai_engine.prompt_defense import PromptDefense
from backend.app.modules.ai_engine.safety import ResponsibleAISafetyEngine

GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini Provider with automatic failover to LocalHeuristicAIProvider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._fallback = LocalHeuristicAIProvider()

    def _call_gemini_api(self, prompt: str, system_instruction: str) -> Optional[str]:
        """Execute HTTP request to Gemini API with retry and timeout management."""
        if not self.api_key:
            return None

        url = f"{GEMINI_API_ENDPOINT}/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.post(url, json=payload, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return None
                elif resp.status_code in [429, 503] and attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(f"Gemini API returned {resp.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini API returned error HTTP {resp.status_code}: {resp.text[:200]}")
                    return None
            except Exception as exc:
                logger.error(f"Gemini API request failed on attempt {attempt + 1}: {exc}")
                if attempt < self.max_retries:
                    time.sleep(1.0)
                else:
                    return None

        return None

    def extract_atomic_claims(self, text: str) -> List[str]:
        """Extract atomic claims using Gemini when available, otherwise local heuristic."""
        sanitized, _, _ = PromptDefense.sanitize_input(text)

        if not self.api_key:
            return self._fallback.extract_atomic_claims(sanitized)

        system_prompt = (
            "You are an NLP Claim Extraction Engine for CivicShield NG. "
            "Extract discrete atomic factual electoral assertions. Return JSON: {\"claims\": [\"claim 1\", \"claim 2\"]}. "
            "Do not invent facts or alter original phrasing."
        )

        response_text = self._call_gemini_api(f"Text: {sanitized}", system_prompt)
        if response_text:
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, dict) and "claims" in parsed and isinstance(parsed["claims"], list):
                    return parsed["claims"]
            except Exception:
                pass

        return self._fallback.extract_atomic_claims(sanitized)

    def classify_electoral_category(self, claim_text: str) -> Dict[str, Any]:
        """Classify electoral category with fallback."""
        return self._fallback.classify_electoral_category(claim_text)

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate similarity using hybrid algorithm."""
        return self._fallback.calculate_similarity(text_a, text_b)

    def evaluate_claim_against_sources(
        self,
        claim_text: str,
        official_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate claim against official sources with prompt injection sanitization,
        responsible AI enforcement, and automatic fallback.
        """
        sanitized_claim, injection_detected, _ = PromptDefense.sanitize_input(claim_text)

        if not self.api_key:
            res = self._fallback.evaluate_claim_against_sources(sanitized_claim, official_sources)
            res["adversarial_injection_detected"] = injection_detected
            return res

        # If API key is present, attempt LLM-assisted verification
        system_prompt = (
            "You are an AI Threat Intelligence Analyst for CivicShield NG. "
            "Evaluate the submitted electoral claim strictly against the provided reference documents. "
            "RESPONSIBLE AI RULES:\n"
            "1. NEVER declare a claim definitively false or verified autonomously.\n"
            "2. If reference documents do not match or are insufficient, return classification 'INSUFFICIENT_EVIDENCE'.\n"
            "3. If evidence is contradictory, return classification 'CONTRADICTED'.\n"
            "4. If evidence affirms the claim, return classification 'SUPPORTED'.\n"
            "5. Requires human review is ALWAYS true.\n"
            "Return JSON matching:\n"
            "{\"extracted_claim\": str, \"classification\": str, \"ai_suggested_status\": str, "
            "\"ai_confidence_score\": float, \"analysis_summary\": str, \"recommended_next_action\": str, "
            "\"contradiction_suspected\": bool, \"limitations\": [str]}"
        )

        prompt = (
            f"Submitted Claim: {sanitized_claim}\n\n"
            f"Available Official Documents:\n{json.dumps(official_sources[:5], indent=2)}"
        )

        response_text = self._call_gemini_api(prompt, system_prompt)
        if response_text:
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, dict) and "analysis_summary" in parsed:
                    parsed["requires_human_review"] = True
                    parsed["adversarial_injection_detected"] = injection_detected
                    # Reconcile source models
                    fallback_res = self._fallback.evaluate_claim_against_sources(sanitized_claim, official_sources)
                    parsed["sources_consulted"] = fallback_res.get("sources_consulted", [])
                    parsed["evidence"] = fallback_res.get("evidence", [])
                    parsed["category"] = fallback_res.get("category", "GENERAL_ELECTORAL")
                    parsed["category_confidence"] = fallback_res.get("category_confidence", 0.8)
                    return ResponsibleAISafetyEngine.enforce_assessment_invariants(parsed)
            except Exception as exc:
                logger.error(f"Error parsing Gemini response: {exc}")

        # Fallback to local heuristic
        res = self._fallback.evaluate_claim_against_sources(sanitized_claim, official_sources)
        res["adversarial_injection_detected"] = injection_detected
        return res
