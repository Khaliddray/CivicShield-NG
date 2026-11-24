"""Claim Extraction Engine for CivicShield NG (Section 3).

Isolates factual claims from citizen submissions, identifies Nigerian electoral entities
(INEC, states, LGAs, dates, events), classifies claim types, and preserves original text
without fabricating missing details.
"""

import re
from typing import List, Dict, Any, Optional
from backend.app.modules.ai_engine.schemas import ExtractedClaimItem, ClaimExtractionResponse
from backend.app.common.geo import ALL_NIGERIAN_STATES as NIGERIAN_STATES

# Well-known Nigerian electoral entities and acronyms
ORGANIZATION_ENTITIES = [
    "INEC", "Independent National Electoral Commission",
    "Police", "NPF", "Nigeria Police Force", "Army", "Nigerian Army",
    "EFCC", "ICPC", "Civil Defence", "NSCDC", "DSS", "SSS",
    "CDD", "YIAGA", "Transition Monitoring Group", "TMG", "EU EOM",
    "Returning Officer", "Resident Electoral Commissioner", "REC",
]

# Common Nigerian cities / LGAs for entity spotting
NOTABLE_PLACES = [
    "Nsukka", "Ikeja", "Alimosho", "Port Harcourt", "Warri", "Calabar",
    "Kaduna", "Maiduguri", "Benin City", "Enugu", "Ibadan", "Jos",
    "Aba", "Onitsha", "Owerri", "Uyo", "Asaba", "Akure", "Abeokuta",
    "Lokoja", "Minna", "Bauchi", "Gombe", "Yola", "Sokoto", "Katsina",
    "Zaria", "FCT", "Abuja", "Gwagwalada", "Kuje", "Bwari",
]

# Temporal regex patterns
DATE_TIME_PATTERNS = [
    re.compile(r"\b(today|tomorrow|yesterday|next\s+month|next\s+week|this\s+saturday|saturday|sunday|monday|tuesday|wednesday|thursday|friday)\b", re.IGNORECASE),
    re.compile(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?(,\s*\d{4})?\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}(st|nd|rd|th)?\s+of\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\b"),  # Years like 2026, 2027
    re.compile(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", re.IGNORECASE),
]

# Opinion markers indicating subjective commentary rather than factual assertions
OPINION_MARKERS = [
    re.compile(r"\b(i\s+think|in\s+my\s+opinion|i\s+feel|i\s+believe|probably|maybe|god\s+forbid|na\s+wah|it\s+seems)\b", re.IGNORECASE),
    re.compile(r"\b(who\s+knows|nobody\s+cares|just\s+saying|my\s+view)\b", re.IGNORECASE),
]

# Claim type detection rules
CLAIM_TYPE_RULES = [
    (
        "ELECTION_DATE_OR_POSTPONEMENT",
        {"postpone", "postponed", "postponement", "reschedule", "rescheduled", "cancel", "cancelled", "halt", "halted", "new date", "extended", "suspended"},
    ),
    (
        "RESULTS_OR_WINNER_DECLARATION",
        {"winner", "won", "declared", "victory", "vote count", "tally", "margin", "leading", "landslide", "elected", "collation", "results"},
    ),
    (
        "VOTER_SUPPRESSION_OR_INTIMIDATION",
        {"thugs", "snatched", "disenfranchised", "intimidation", "turned away", "scared", "locked out", "ballot snatching", "tear gas", "intimidated", "suppression"},
    ),
    (
        "INEC_OPERATIONS_AND_BVAS",
        {"bvas", "irev", "polling unit", "relocated", "moved", "ad-hoc", "pvc", "accreditation", "registration", "officials", "polling"},
    ),
    (
        "SECURITY_INCIDENT_OR_CURFEW",
        {"police", "soldiers", "army", "military", "gunfire", "violence", "curfew", "attack", "clash", "clashes", "armed", "checkpoint", "shooting", "protesters"},
    ),
    (
        "LOGISTICS_OR_MATERIALS_DELAY",
        {"late arrival", "materials missing", "no ink", "officials absent", "late opening", "delayed opening", "no ballot papers", "delayed", "delays"},
    ),
    (
        "IMPERSONATION_OR_FORGERY",
        {"fake letter", "forged circular", "impersonation", "fake press release", "cloned website", "deepfake"},
    ),
]


class ClaimExtractionEngine:
    """Extracts factual claims and entities from civic and electoral narratives."""

    @classmethod
    def extract_entities(cls, text: str, context_state: Optional[str] = None) -> List[str]:
        """Extract electoral institutions, locations, and temporal markers from text."""
        entities: List[str] = []

        # 1. Organizations
        for org in ORGANIZATION_ENTITIES:
            pattern = rf"\b{re.escape(org)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                if org not in entities:
                    entities.append(org)

        # 2. Nigerian States
        for state in NIGERIAN_STATES:
            pattern = rf"\b{re.escape(state)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                if state not in entities:
                    entities.append(state)

        # 3. Notable Cities / LGAs
        for place in NOTABLE_PLACES:
            pattern = rf"\b{re.escape(place)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                if place not in entities:
                    entities.append(place)

        # 4. Dates & Times
        for pat in DATE_TIME_PATTERNS:
            for match in pat.finditer(text):
                matched_val = match.group(0).strip()
                # Ignore isolated 1-2 digit numbers that aren't times or years
                if matched_val.isdigit() and len(matched_val) < 4:
                    continue
                if matched_val and matched_val not in entities:
                    entities.append(matched_val)

        # 5. Inject context state if provided and not already present
        if context_state and context_state in NIGERIAN_STATES and context_state not in entities:
            entities.append(context_state)

        return entities

    @classmethod
    def detect_claim_type(cls, claim_text: str) -> str:
        """Classify statement into granular electoral claim type using weighted keyword matching."""
        words = set(re.findall(r"\b[a-zA-Z-]{3,}\b", claim_text.lower()))

        best_type = "GENERAL_CIVIC_CLAIM"
        best_count = 0

        for claim_type, keywords in CLAIM_TYPE_RULES:
            matches = len(words.intersection(keywords))
            if matches > best_count:
                best_count = matches
                best_type = claim_type

        return best_type

    @classmethod
    def is_opinion_statement(cls, text: str) -> bool:
        """Determine if statement expresses personal opinion rather than factual assertion."""
        for pattern in OPINION_MARKERS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def extract_claims(
        cls,
        text: str,
        context_state: Optional[str] = None,
    ) -> ClaimExtractionResponse:
        """
        Accept citizen-submitted text, extract factual claims, detect entities,
        and preserve original submission text.
        """
        if not text or not text.strip():
            return ClaimExtractionResponse(
                original_text=text or "",
                claims=[],
            )

        original_text = text.strip()

        # Split into sentences or clauses
        raw_sentences = [
            s.strip() for s in re.split(r"(?<=[.!?\n])\s+", original_text)
            if len(s.strip()) > 5
        ]

        # If splitting yielded nothing, fall back to entire text
        if not raw_sentences:
            raw_sentences = [original_text]

        claims: List[ExtractedClaimItem] = []

        # Assertion keywords that indicate an informative or electoral factual statement
        assertion_markers = {
            "announced", "cancelled", "postponed", "moved", "relocated", "won", "declared",
            "results", "prohibited", "banned", "delayed", "closed", "attacked", "voters",
            "polling", "materials", "bvas", "inec", "police", "curfew", "halted", "rescheduled",
            "arrived", "commenced", "suspended", "extended", "tally", "confirm", "confirms"
        }

        for sentence in raw_sentences:
            words = set(re.findall(r"\b[a-zA-Z]{3,}\b", sentence.lower()))
            is_opinion = cls.is_opinion_statement(sentence)
            has_markers = bool(words.intersection(assertion_markers))
            is_long_enough = len(words) >= 3

            # Determine entities in this specific sentence
            sentence_entities = cls.extract_entities(sentence, context_state=context_state)
            claim_type = cls.detect_claim_type(sentence)

            # A factual claim requiring verification has electoral markers or entities and is not purely opinion
            requires_verification = not is_opinion and (has_markers or len(sentence_entities) > 0)

            if is_long_enough and (has_markers or len(sentence_entities) > 0 or len(raw_sentences) == 1):
                claims.append(
                    ExtractedClaimItem(
                        claim_text=sentence,
                        entities=sentence_entities,
                        claim_type=claim_type,
                        is_opinion=is_opinion,
                        requires_verification=requires_verification,
                        confidence=0.88 if has_markers else 0.70,
                    )
                )

        # Fallback if no specific claims matched criteria: preserve first sentence or whole text
        if not claims and raw_sentences:
            first_s = raw_sentences[0]
            entities = cls.extract_entities(first_s, context_state=context_state)
            claims.append(
                ExtractedClaimItem(
                    claim_text=first_s,
                    entities=entities,
                    claim_type=cls.detect_claim_type(first_s),
                    is_opinion=cls.is_opinion_statement(first_s),
                    requires_verification=True,
                    confidence=0.60,
                )
            )

        return ClaimExtractionResponse(
            original_text=original_text,
            detected_language="en",
            is_translated=False,
            claims=claims,
        )
