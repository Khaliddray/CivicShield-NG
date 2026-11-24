"""Electoral Information Classification Engine (Section 4).

Classifies electoral claims against the certified evidence base into:
- POTENTIALLY_MISLEADING
- UNSUPPORTED
- CONTRADICTED
- SUPPORTED
- IMPERSONATION
- OUTDATED_INFORMATION
- INSUFFICIENT_EVIDENCE
- OPINION_BASED

Strict Invariant: The system NEVER labels a claim as misinformation or false
merely because supporting evidence cannot be found. Where evidence is missing,
the classification strictly returns INSUFFICIENT_EVIDENCE.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.common.enums import VerificationDecision, ClaimCategory
from backend.app.modules.ai_engine.similarity import SimilarityEngine
from backend.app.modules.ai_engine.claim_extractor import ClaimExtractionEngine
from backend.app.modules.ai_engine.evidence_retrieval import EvidenceRetrievalEngine

# Impersonation indicators
IMPERSONATION_SIGNATURES = [
    re.compile(r"\b(signed\s+by\s+(the\s+)?(inec\s+chairman|commissioner|returning\s+officer))\b", re.IGNORECASE),
    re.compile(r"\b(official\s+press\s+release\s+ref\s*(no|#|:))\b", re.IGNORECASE),
    re.compile(r"\b(forward\s+this\s+to\s+all\s+groups|broadcast\s+urgently|share\s+before\s+it\s+is\s+deleted)\b", re.IGNORECASE),
    re.compile(r"\b(internal\s+memo\s+leaked\s+from\s+inec)\b", re.IGNORECASE),
]


class ElectoralInformationClassifier:
    """Classifies electoral claims in accordance with evidence sufficiency and safety standards."""

    @classmethod
    def detect_impersonation_markers(cls, text: str) -> bool:
        """Check for suspicious phrasing typical of forged or impersonated official circulars."""
        for pattern in IMPERSONATION_SIGNATURES:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def check_temporal_currency(cls, doc_pub_date_str: Optional[str]) -> bool:
        """Check if document is from an outdated electoral cycle (e.g. > 18 months old)."""
        if not doc_pub_date_str:
            return True  # Assume current if no date
        try:
            # Handle ISO string with or without timezone
            pub_dt = datetime.fromisoformat(doc_pub_date_str.replace("Z", "+00:00"))
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            now_dt = datetime.now(timezone.utc)
            days_diff = (now_dt - pub_dt).days
            # If older than 540 days (~1.5 years), flag as outdated
            return days_diff < 540
        except Exception:
            return True

    @classmethod
    def classify_claim(
        cls,
        claim_text: str,
        evidence_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produce a grounded electoral classification based on claim text and evidence.
        Returns:
            {
                "classification": str,
                "ai_suggested_status": str,  # maps to VerificationDecision
                "confidence": float,
                "reasoning": str,
                "category": str,             # maps to ClaimCategory
                "category_confidence": float,
            }
        """
        # 1. Determine electoral domain category
        claim_type = ClaimExtractionEngine.detect_claim_type(claim_text)
        category_map = {
            "ELECTION_DATE_OR_POSTPONEMENT": ClaimCategory.INEC_OPERATIONS.value,
            "RESULTS_OR_WINNER_DECLARATION": ClaimCategory.RESULTS_ANNOUNCEMENT.value,
            "VOTER_SUPPRESSION_OR_INTIMIDATION": ClaimCategory.VOTER_SUPPRESSION.value,
            "INEC_OPERATIONS_AND_BVAS": ClaimCategory.INEC_OPERATIONS.value,
            "SECURITY_INCIDENT_OR_CURFEW": ClaimCategory.SECURITY_INCIDENT.value,
            "LOGISTICS_OR_MATERIALS_DELAY": ClaimCategory.LOGISTICS_DELAY.value,
            "IMPERSONATION_OR_FORGERY": ClaimCategory.DISINFORMATION_CAMPAIGN.value,
            "GENERAL_CIVIC_CLAIM": ClaimCategory.GENERAL_ELECTORAL.value,
            "OPINION_OR_SPECULATION": ClaimCategory.GENERAL_ELECTORAL.value,
        }
        category = category_map.get(claim_type, ClaimCategory.GENERAL_ELECTORAL.value)

        # 2. Check if statement is purely opinion
        if ClaimExtractionEngine.is_opinion_statement(claim_text):
            return {
                "classification": "OPINION_BASED",
                "ai_suggested_status": VerificationDecision.UNVERIFIED.value,
                "confidence": 0.85,
                "reasoning": "Statement expresses personal sentiment, prediction, or subjective viewpoint rather than an empirical factual assertion.",
                "category": category,
                "category_confidence": 0.80,
                "requires_human_review": True,
            }

        # 3. Check for impersonation markers
        is_impersonation_suspected = cls.detect_impersonation_markers(claim_text)
        if is_impersonation_suspected and not evidence_result.get("is_sufficient"):
            return {
                "classification": "IMPERSONATION",
                "ai_suggested_status": VerificationDecision.UNDER_REVIEW.value,
                "confidence": 0.80,
                "reasoning": "Statement exhibits stylistic signatures of a fabricated official circular (e.g. claiming unverified signing or urgent forwarding) with no matching gazette in the official registry.",
                "category": ClaimCategory.DISINFORMATION_CAMPAIGN.value,
                "category_confidence": 0.85,
                "requires_human_review": True,
            }

        # 4. Evidence-based classification
        is_sufficient = evidence_result.get("is_sufficient", False)
        has_contradiction = evidence_result.get("has_contradiction", False)
        has_support = evidence_result.get("has_support", False)
        highest_sim = evidence_result.get("highest_similarity", 0.0)
        top_doc = evidence_result.get("top_document")

        if is_sufficient and top_doc:
            # Check temporal currency
            is_current = cls.check_temporal_currency(top_doc.get("publication_date"))
            if not is_current:
                return {
                    "classification": "OUTDATED_INFORMATION",
                    "ai_suggested_status": VerificationDecision.UNDER_REVIEW.value,
                    "confidence": round(highest_sim, 2),
                    "reasoning": f"Claim references an older electoral release ('{top_doc.get('title')}') which may no longer reflect the active 2026 electoral schedule.",
                    "category": category,
                    "category_confidence": 0.75,
                    "requires_human_review": True,
                }

            if has_contradiction:
                return {
                    "classification": "CONTRADICTED",
                    "ai_suggested_status": VerificationDecision.UNDER_REVIEW.value,
                    "confidence": round(highest_sim, 2),
                    "reasoning": f"Claim directly contradicts authenticated official release '{top_doc.get('title')}' issued by {top_doc.get('issuing_institution')}.",
                    "category": category,
                    "category_confidence": 0.88,
                    "requires_human_review": True,
                }

            if has_support:
                return {
                    "classification": "SUPPORTED",
                    "ai_suggested_status": VerificationDecision.UNDER_REVIEW.value,
                    "confidence": round(highest_sim, 2),
                    "reasoning": f"Claim is corroborated by certified official gazette '{top_doc.get('title')}' issued by {top_doc.get('issuing_institution')}.",
                    "category": category,
                    "category_confidence": 0.90,
                    "requires_human_review": True,
                }

            # Moderate similarity without strict polarity match -> POTENTIALLY_MISLEADING or UNSUPPORTED
            if highest_sim >= 0.40:
                return {
                    "classification": "POTENTIALLY_MISLEADING",
                    "ai_suggested_status": VerificationDecision.UNDER_REVIEW.value,
                    "confidence": round(highest_sim, 2),
                    "reasoning": f"Claim shares subject matter with official release '{top_doc.get('title')}' but diverges in specific details, numbers, or scope.",
                    "category": category,
                    "category_confidence": 0.75,
                    "requires_human_review": True,
                }

        # 5. Fallback: Evidence is insufficient
        # HARD INVARIANT: If evidence is insufficient, NEVER label as misinformation. Return INSUFFICIENT_EVIDENCE.
        return {
            "classification": "INSUFFICIENT_EVIDENCE",
            "ai_suggested_status": VerificationDecision.INSUFFICIENT_EVIDENCE.value,
            "confidence": 0.0,
            "reasoning": (
                "No authenticated official announcement or certified gazette in the registry addresses this assertion. "
                "Per Responsible AI guidelines, absence of evidence must not be construed as falsity."
            ),
            "category": category,
            "category_confidence": 0.50,
            "requires_human_review": True,
        }
