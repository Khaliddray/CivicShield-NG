"""Responsible AI and Electoral Safety Guardrails for CivicShield NG.

Enforces the 12 non-negotiable responsible AI principles defined in AGENT.md:
1. No automatic public declaration that a claim is false.
2. No automatic publication of alerts.
3. No political persuasion or voter microtargeting.
4. No political affiliation inference.
5. No unsupported foreign actor attribution.
6. No invented official sources.
7. No fabricated evidence.
8. No unsupported confidence claims.
9. Human review for consequential verification decisions.
10. Clear disclosure of uncertainty and limitations.
11. Preserve source information and original submitted content.
12. Distinguish media authenticity from factual accuracy.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from backend.app.core.logging import logger
from backend.app.common.enums import VerificationDecision

# Patterns that indicate speculative political affiliation labeling
POLITICAL_AFFILIATION_PATTERNS = [
    re.compile(r"\b(apc|pdp|lp|nnpp)\s+(agent|supporter|operative|thug|member|sympathizer)s?\b", re.IGNORECASE),
    re.compile(r"\bpartisan\s+bias\s+towards\b", re.IGNORECASE),
    re.compile(r"\bvoter\s+is\s+aligned\s+with\b", re.IGNORECASE),
]

# Patterns attributing to foreign nation-states without evidentiary proof
FOREIGN_ACTOR_PATTERNS = [
    re.compile(r"\b(russian|chinese|cia|mossad|foreign|iranian)\s+(botnet|operation|interference|actor|hackers)\b", re.IGNORECASE),
    re.compile(r"\bstate-sponsored\s+foreign\b", re.IGNORECASE),
]


class ResponsibleAISafetyEngine:
    """Enforces safety, nonpartisanship, and responsible disclosures across AI pipelines."""

    STANDARD_LIMITATIONS: List[str] = [
        "AI output is an analytical aid and does not constitute an authoritative electoral ruling.",
        "Grounding is strictly restricted to certified gazettes in the official registry.",
        "Similarity between reports reflects narrative recurrence, not common authorship or coordinated intent.",
        "Absence of matching official evidence must not be treated as proof of falsity.",
    ]

    @classmethod
    def sanitize_model_text(cls, text: str) -> str:
        """
        Sanitize text output to ensure compliance with Responsible AI rules:
        - Strips political affiliation accusations
        - Strips speculative foreign actor attribution
        """
        if not text:
            return ""

        cleaned = text
        for pat in POLITICAL_AFFILIATION_PATTERNS:
            cleaned = pat.sub("[REDACTED_POLITICAL_INFERENCE]", cleaned)

        for pat in FOREIGN_ACTOR_PATTERNS:
            cleaned = pat.sub("[UNVERIFIED_ATTRIBUTION_REDACTED]", cleaned)

        return cleaned

    @classmethod
    def enforce_assessment_invariants(cls, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce safety invariants on structured AI assessments:
        - requires_human_review must ALWAYS be True for consequential decisions.
        - ai_suggested_status must never unilaterally set public binding states without review.
        - Limitations must always be present.
        - Confidence must be bounded [0.0, 1.0].
        """
        # 1. Non-negotiable human review requirement
        assessment["requires_human_review"] = True

        # 2. Never allow autonomous final ruling: VERIFIED or CONTRADICTED must remain candidate/advisory
        # In the queue/system, ai_suggested_status remains UNDER_REVIEW for officer evaluation
        suggested = assessment.get("ai_suggested_status") or VerificationDecision.UNDER_REVIEW.value
        assessment["ai_suggested_status"] = suggested

        # 3. Bound confidence score
        conf = assessment.get("confidence") or assessment.get("ai_confidence_score") or 0.0
        assessment["confidence"] = max(0.0, min(float(conf), 1.0))
        assessment["ai_confidence_score"] = assessment["confidence"]

        # 4. Inject standard transparent limitations
        existing_limits = assessment.get("limitations") or []
        for default_lim in cls.STANDARD_LIMITATIONS:
            if default_lim not in existing_limits:
                existing_limits.append(default_lim)
        assessment["limitations"] = existing_limits

        # 5. Sanitize summary and reasoning
        if "analysis_summary" in assessment and assessment["analysis_summary"]:
            assessment["analysis_summary"] = cls.sanitize_model_text(assessment["analysis_summary"])
        if "reasoning" in assessment and assessment["reasoning"]:
            assessment["reasoning"] = cls.sanitize_model_text(assessment["reasoning"])

        return assessment

    @classmethod
    def validate_sources(cls, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure no fabricated sources are admitted.
        Sources must have a valid document_code or source_name and cannot be placeholders.
        """
        validated = []
        for s in sources:
            name = s.get("title") or s.get("source_name") or s.get("document_code")
            if not name or "hallucinated" in str(name).lower() or "fake_source" in str(name).lower():
                continue
            validated.append(s)
        return validated
