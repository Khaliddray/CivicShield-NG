"""Multilingual civic information processing prioritizing English and Nigerian Pidgin.

Adheres strictly to AGENT.md Section 3.4:
- Prioritize English and Nigerian Pidgin.
- All machine translations must be clearly labeled:
  "Machine Translation (Nigerian Pidgin) — Official source is in English"
- Official legal gazettes must retain their canonical English text alongside any localized translations.
"""

import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

OFFICIAL_SOURCE_DISCLAIMER = (
    "Machine Translation (Nigerian Pidgin) — Official source is in English"
)

# Characteristic Nigerian Pidgin markers & lexical tokens
PIDGIN_MARKERS = {
    "wetin", "dey", "dem", "una", "abi", "sha", "wahala", "abeg", "commot",
    "sef", "oya", "kwanu", "pikin", "fit", "make", "waka", "na", "don",
    "no", "go", "sabi", "chook", "tori", "gist", "kpatakpata", "baff",
    "scatter", "chop", "dash", "palava", "shey", "yarn", "wetin", "which",
}

# Bidirectional phrase dictionaries for civic electoral communication
PIDGIN_TO_ENGLISH_PHRASES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bdem\s+don\s+postpone\b", re.IGNORECASE), "elections have been postponed"),
    (re.compile(r"\bdem\s+don\s+cancel\b", re.IGNORECASE), "elections have been cancelled"),
    (re.compile(r"\bdem\s+don\s+shift\b", re.IGNORECASE), "elections have been rescheduled"),
    (re.compile(r"\bvoting\s+don\s+start\b", re.IGNORECASE), "voting has commenced"),
    (re.compile(r"\bbvas\s+no\s+dey\s+work\b", re.IGNORECASE), "BVAS devices are malfunctioning"),
    (re.compile(r"\bbvas\s+dey\s+work\s+well\b", re.IGNORECASE), "BVAS devices are operating normally"),
    (re.compile(r"\bno\s+wahala\b", re.IGNORECASE), "no disruption or incident"),
    (re.compile(r"\bwetin\s+dey\s+happen\b", re.IGNORECASE), "what is happening"),
    (re.compile(r"\bmake\s+una\s+go\s+vote\b", re.IGNORECASE), "citizens should go and vote"),
    (re.compile(r"\bmake\s+una\s+no\s+panic\b", re.IGNORECASE), "citizens should remain calm and not panic"),
    (re.compile(r"\bna\s+fake\s+news\b", re.IGNORECASE), "this is unverified or fabricated information"),
    (re.compile(r"\binec\s+never\s+announce\b", re.IGNORECASE), "INEC has not announced"),
    (re.compile(r"\bthugs\s+don\s+scatter\b", re.IGNORECASE), "thugs have disrupted"),
    (re.compile(r"\bballot\s+box\s+snatcher\b", re.IGNORECASE), "ballot box snatchers"),
    (re.compile(r"\buna\s+vote\b", re.IGNORECASE), "your votes"),
    (re.compile(r"\bdem\s+dey\s+count\b", re.IGNORECASE), "counting is underway"),
]

ENGLISH_TO_PIDGIN_PHRASES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\belections?\s+have\s+been\s+postponed\b", re.IGNORECASE), "election don shift"),
    (re.compile(r"\belections?\s+have\s+been\s+cancelled\b", re.IGNORECASE), "dem don cancel election"),
    (re.compile(r"\bvoting\s+has\s+commenced\b", re.IGNORECASE), "voting don start"),
    (re.compile(r"\bvoting\s+is\s+proceeding\s+normally\b", re.IGNORECASE), "voting dey go on normal normal"),
    (re.compile(r"\bdo\s+not\s+panic\b", re.IGNORECASE), "make una no panic"),
    (re.compile(r"\bremain\s+calm\b", re.IGNORECASE), "make everybody keep calm"),
    (re.compile(r"\bthis\s+is\s+false\s+information\b", re.IGNORECASE), "na lie and fake news be this"),
    (re.compile(r"\bofficial\s+notice\b", re.IGNORECASE), "kpatakpata official announcement from INEC"),
    (re.compile(r"\ball\s+polling\s+units\b", re.IGNORECASE), "all polling units"),
    (re.compile(r"\bpolling\s+is\s+active\b", re.IGNORECASE), "polling units dey open and active"),
    (re.compile(r"\bbvas\s+devices\s+are\s+mandatory\b", re.IGNORECASE), "BVAS must be used for accreditation, no alternative"),
]


class LanguageDetectionResult(BaseModel):
    """Payload returning language detection breakdown."""

    text: str
    detected_language: str = Field(description="'en' for English, 'pcm' for Nigerian Pidgin")
    confidence: float
    is_pidgin: bool
    matched_markers: List[str] = Field(default_factory=list)


class TranslationResponse(BaseModel):
    """Localized civic translation payload with legal nonpartisanship disclaimer."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    disclaimer: str = OFFICIAL_SOURCE_DISCLAIMER
    canonical_source_language: str = "en"
    requires_human_review: bool = True


class MultilingualService:
    """Civic translation and localized language processing engine."""

    @classmethod
    def detect_language(cls, text: str) -> LanguageDetectionResult:
        """
        Detect whether citizen submission or civic advisory is in Nigerian Pidgin or standard English.
        """
        if not text:
            return LanguageDetectionResult(
                text="",
                detected_language="en",
                confidence=1.0,
                is_pidgin=False,
                matched_markers=[],
            )

        words = set(re.findall(r"\b[a-zA-Z]{2,}\b", text.lower()))
        matched = list(words.intersection(PIDGIN_MARKERS))

        # Check for characteristic Pidgin bigram patterns (e.g. "make una", "no dey", "dem don")
        bigram_pidgin = bool(re.search(r"\b(make una|no dey|dem don|na fake|wetin dey|una go|don start)\b", text, re.IGNORECASE))

        is_pidgin = len(matched) >= 2 or bigram_pidgin
        confidence = min(0.50 + (len(matched) * 0.15), 0.95) if is_pidgin else 0.85
        lang = "pcm" if is_pidgin else "en"

        return LanguageDetectionResult(
            text=text,
            detected_language=lang,
            confidence=round(confidence, 2),
            is_pidgin=is_pidgin,
            matched_markers=matched,
        )

    @classmethod
    def translate_to_english(cls, text: str) -> TranslationResponse:
        """
        Convert Nigerian Pidgin narrative into standard English for claim extraction & registry indexing.
        """
        translated = text
        for pattern, replacement in PIDGIN_TO_ENGLISH_PHRASES:
            translated = pattern.sub(replacement, translated)

        return TranslationResponse(
            original_text=text,
            translated_text=translated,
            source_language="pcm",
            target_language="en",
            disclaimer=OFFICIAL_SOURCE_DISCLAIMER,
        )

    @classmethod
    def translate_to_pidgin(cls, text: str) -> TranslationResponse:
        """
        Convert certified official English debunks / advisories into accessible Nigerian Pidgin.
        Enforces mandatory disclaimer to preserve official legal primacy.
        """
        translated = text
        for pattern, replacement in ENGLISH_TO_PIDGIN_PHRASES:
            translated = pattern.sub(replacement, translated)

        return TranslationResponse(
            original_text=text,
            translated_text=translated,
            source_language="en",
            target_language="pcm",
            disclaimer=OFFICIAL_SOURCE_DISCLAIMER,
        )
