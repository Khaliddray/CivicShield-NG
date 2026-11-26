"""Isolated Development & Test Adapter for AI Engine (Section 11).

Provides:
- Fully deterministic response mocking for test isolation
- Simulation of provider timeouts and malformed responses
- Explicitly blocked from running in production environments
- Clearly labelled as a test adapter per AGENT.md Section 11/12
"""

from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.exceptions import ValidationException
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.safety import ResponsibleAISafetyEngine


class DevelopmentAdapterAIProvider(BaseAIProvider):
    """
    Test and development AI adapter.
    Never used in production; ensures zero external dependencies during automated CI/CD.
    """

    def __init__(
        self,
        simulate_timeout: bool = False,
        simulate_malformed: bool = False,
        forced_status: Optional[str] = None,
    ):
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "CRITICAL SECURITY VIOLATION: DevelopmentAdapterAIProvider cannot be loaded in a production environment!"
            )
        self.simulate_timeout = simulate_timeout
        self.simulate_malformed = simulate_malformed
        self.forced_status = forced_status

    def extract_atomic_claims(self, text: str) -> List[str]:
        if self.simulate_timeout:
            raise TimeoutError("Simulated AI Provider API timeout.")
        if self.simulate_malformed:
            return []
        return [text[:120]] if text else []

    def classify_electoral_category(self, claim_text: str) -> Dict[str, Any]:
        return {
            "category": "INEC_OPERATIONS",
            "confidence": 0.85,
            "matched_keywords": ["test", "simulation"],
        }

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        if text_a == text_b:
            return 1.0
        return 0.50

    def evaluate_claim_against_sources(
        self,
        claim_text: str,
        official_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if self.simulate_timeout:
            raise TimeoutError("Simulated AI Provider API timeout during evidence evaluation.")

        if self.simulate_malformed:
            return {"malformed_key": None}

        status = self.forced_status or "UNDER_REVIEW"
        contra = (status == "CONTRADICTED")

        raw = {
            "extracted_claim": claim_text,
            "category": "INEC_OPERATIONS",
            "category_confidence": 0.85,
            "ai_confidence_score": 0.80,
            "ai_suggested_status": status,
            "analysis_summary": f"SIMULATED TEST ASSESSMENT: Claim evaluated under test harness (Status: {status}).",
            "sources_consulted": [
                {
                    "document_code": s.get("document_code", "SIM-TEST-001"),
                    "title": s.get("title", "Simulated Official Notice"),
                    "issuing_institution": s.get("issuing_institution", "INEC"),
                    "similarity_score": 0.80,
                }
                for s in official_sources[:2]
            ],
            "contradiction_suspected": contra,
            "recommended_next_action": "Proceed with test verification officer review.",
            "requires_human_review": True,
            "classification": status,
            "evidence": [],
            "limitations": ["SIMULATION ADAPTER ONLY — NEVER FOR PRODUCTION USE."],
            "reasoning": "Controlled test response for automated evaluation suite.",
        }

        return ResponsibleAISafetyEngine.enforce_assessment_invariants(raw)
