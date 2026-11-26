"""Deterministic, zero-dependency NLP and heuristic AI Provider for offline and baseline operation."""

import re
from typing import Any, Dict, List, Optional
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.claim_extractor import ClaimExtractionEngine
from backend.app.modules.ai_engine.similarity import SimilarityEngine
from backend.app.modules.ai_engine.evidence_retrieval import EvidenceRetrievalEngine
from backend.app.modules.ai_engine.classifier import ElectoralInformationClassifier
from backend.app.modules.ai_engine.safety import ResponsibleAISafetyEngine
from backend.app.common.enums import ClaimCategory, VerificationDecision


class LocalHeuristicAIProvider(BaseAIProvider):
    """Reliable, fast heuristic NLP processor requiring no external GPU or cloud API keys."""

    def extract_atomic_claims(self, text: str) -> List[str]:
        """Extract atomic claims preserving backwards compatibility with legacy List[str] contract."""
        res = ClaimExtractionEngine.extract_claims(text)
        return [c.claim_text for c in res.claims if c.claim_text]

    def extract_claims_structured(self, text: str, context_state: Optional[str] = None) -> Dict[str, Any]:
        """Extract discrete factual claims with entity tagging and claim type detection."""
        res = ClaimExtractionEngine.extract_claims(text, context_state=context_state)
        return res.model_dump()

    def classify_electoral_category(self, claim_text: str) -> Dict[str, Any]:
        """Determine domain category based on lexical taxonomy and entity spotting."""
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

        # Keyword matching for backward compatibility
        words = set(re.findall(r"\b[a-zA-Z-]{3,}\b", claim_text.lower()))
        confidence = 0.85 if claim_type != "GENERAL_CIVIC_CLAIM" else 0.40

        return {
            "category": category,
            "confidence": round(confidence, 2),
            "matched_keywords": list(words)[:5],
        }

    def _normalize_token(self, token: str) -> str:
        """Apply light stemming and electoral synonym normalization."""
        synonyms = {
            "postponed": "postpone", "postponement": "postpone", "postponing": "postpone", "moved": "postpone",
            "delayed": "delay", "delays": "delay", "delaying": "delay",
            "voting": "vote", "elections": "vote", "election": "vote", "polls": "vote", "polling": "vote", "voters": "vote",
            "circular": "notice", "circulars": "notice", "announcement": "notice", "announcements": "notice",
        }
        w = synonyms.get(token, token)
        w = re.sub(r"(ing|ment|tion|ted|ed|es|s)$", "", w)
        return synonyms.get(w, w)

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity after local electoral token normalization."""
        normalize = lambda text: re.sub(
            r"\b[a-zA-Z0-9]{3,}\b",
            lambda match: self._normalize_token(match.group(0).lower()),
            text,
        )
        return SimilarityEngine.calculate_similarity(normalize(text_a), normalize(text_b))

    def evaluate_claim_against_sources(
        self,
        claim_text: str,
        official_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze claim against reference dataset of authenticated documents.
        Enforces evidence-grounding and responsible AI invariants.
        """
        # 1. Compare against sources
        evidence_result = EvidenceRetrievalEngine.compare_claim_against_sources(
            claim_text=claim_text,
            official_documents=official_sources,
        )

        # 2. Classify claim
        classification = ElectoralInformationClassifier.classify_claim(
            claim_text=claim_text,
            evidence_result=evidence_result,
        )

        # 3. Build summary and recommendation
        top_doc = evidence_result.get("top_document")
        highest_similarity = evidence_result.get("highest_similarity", 0.0)
        has_contradiction = evidence_result.get("has_contradiction", False)
        sources_consulted = [s.model_dump() for s in evidence_result.get("matched_sources", [])]

        class_type = classification.get("classification")
        if class_type == "OPINION_BASED":
            summary = (
                "Statement expresses personal opinion or subjective sentiment rather than an empirical factual assertion. "
                "Per Responsible AI rules, opinion statements are flagged for reviewer triage."
            )
            rec_action = "Mark as opinion / non-factual content during human officer review."
        elif class_type == "IMPERSONATION":
            summary = (
                "Statement exhibits stylistic signatures of a fabricated official circular or impersonation attempt with no matching certified announcement in the registry."
            )
            rec_action = "Escalate to Lead Officer for immediate clarification advisory and threat incident logging."
        elif class_type == "OUTDATED_INFORMATION" and top_doc:
            summary = (
                f"Claim references an older electoral release '{top_doc.get('title')}' which may no longer reflect the active electoral cycle."
            )
            rec_action = "Review whether claim cites a superseded announcement."
        elif has_contradiction and top_doc:
            summary = (
                f"Preliminary analysis identified potential contradiction with official release '{top_doc.get('title')}' "
                f"issued by {top_doc.get('issuing_institution')} (Similarity: {highest_similarity:.0%}). "
                f"Official gazette asserts the opposite of the submitted claim."
            )
            rec_action = "Assign to Verification Officer for priority human review and candidate clarification advisory."
        elif evidence_result.get("has_support") and top_doc:
            summary = (
                f"Claim exhibits strong similarity ({highest_similarity:.0%}) to certified announcement '{top_doc.get('title')}' "
                f"issued by {top_doc.get('issuing_institution')}."
            )
            rec_action = "Review whether claim is an accurate quote or partial excerpt of the official statement."
        else:
            summary = (
                f"No strongly matching certified announcements found in the reference registry (Max similarity: {highest_similarity:.0%}). "
                f"Per Responsible AI guidelines, absence of evidence must not be construed as falsity."
            )
            rec_action = "Seek primary confirmation from the relevant state electoral authority."

        raw_assessment = {
            "extracted_claim": claim_text,
            "category": classification["category"],
            "category_confidence": classification["category_confidence"],
            "ai_confidence_score": classification["confidence"],
            "ai_suggested_status": classification["ai_suggested_status"],
            "analysis_summary": summary,
            "sources_consulted": sources_consulted,
            "contradiction_suspected": has_contradiction,
            "recommended_next_action": rec_action,
            "requires_human_review": True,
            "classification": classification["classification"],
            "evidence": [e.model_dump() for e in evidence_result.get("structured_evidence", [])],
            "limitations": evidence_result.get("limitations", []),
            "reasoning": classification.get("reasoning", ""),
        }

        # 4. Enforce Responsible AI Guardrails
        return ResponsibleAISafetyEngine.enforce_assessment_invariants(raw_assessment)
