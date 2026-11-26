"""Multilingual Processing Engine for CivicShield NG (Section 9).

Supports:
- Language identification (English, Nigerian Pidgin, Hausa, Yoruba, Igbo)
- Text normalization
- Translation between English and Nigerian Pidgin
- Preserving original user narrative alongside machine translations
- Extensible architecture for Hausa, Yoruba, and Igbo
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from backend.app.modules.ai_engine.schemas import (
    LanguageDetectionResponse,
    TranslationResponse,
)

# Diagnostic lexicon for Nigerian Pidgin
PIDGIN_LEXICON = {
    "dey", "wetin", "na lie", "no fit", "dem say", "abeg", "oya", "una",
    "don happen", "wahala", "gbege", "pikin", "sef", "kwanu", "abi", "baff",
    "carry go", "make una", "no be so", "commot", "chop", "waka", "na true",
    "dem don", "wetin dey happen", "comot", "shishi", "shey", "palava",
    "fit", "go fit", "no dey", "don spoil", "snatch"
}

# Diagnostic lexicon for Hausa
HAUSA_LEXICON = {
    "bayan", "amma", "wannan", "sarkin", "zaɓe", "kuri'a", "gwamnati",
    "jami'an", "yau", "ina", "hukumar", "mutane", "shugaban", "tare", "sai", "zabe"
}

# Diagnostic lexicon for Yoruba
YORUBA_LEXICON = {
    "awon", "idibo", "ijoba", "nigba", "pelu", "sugbon", "gege", "fun",
    "ati", "olopa", "eniyan", "orile-ede", "abajade"
}

# Diagnostic lexicon for Igbo
IGBO_LEXICON = {
    "ndi", "nhoputa", "ochichi", "anyi", "mana", "maka", "nke", "onye",
    "ulo", "oge", "obodo", "ndu", "ndị", "ọchịchị"
}

# Phrase translation dictionary for Nigerian Pidgin -> English
PIDGIN_TO_ENGLISH_PHRASES = [
    (r"\bdem don postpone (election|voting)\b", "the election has been postponed"),
    (r"\bdem say inec (don )?cancel\b", "it is claimed that INEC has cancelled"),
    (r"\bno fit vote\b", "cannot vote"),
    (r"\bbvas (machine )?don spoil\b", "BVAS machines have malfunctioned"),
    (r"\bwahala dey for\b", "there is unrest at"),
    (r"\bgbege don burst for\b", "conflict has erupted at"),
    (r"\bthugs don snatch\b", "thugs have stolen"),
    (r"\bpolice dey everywhere for\b", "police are deployed at"),
    (r"\bna lie\b", "it is untrue"),
    (r"\bna true\b", "it is true"),
    (r"\bmake una hear\b", "please note"),
    (r"\bdem say\b", "they claim that"),
    (r"\bno dey work\b", "is not working"),
    (r"\bdem don announce\b", "they have announced"),
]

# Phrase translation dictionary for English -> Nigerian Pidgin (approved clarifications)
ENGLISH_TO_PIDGIN_PHRASES = [
    (
        r"INEC confirms all voting activities proceed normally as scheduled\.",
        "INEC don confirm say voting dey go on well as dem schedule am.",
    ),
    (
        r"This claim is contradicted by certified official documentation\.",
        "Official paper from INEC show say this talk no be true.",
    ),
    (
        r"No certified announcements match this claim in the official registry\.",
        "Official paper never dey for registry to confirm this matter.",
    ),
    (
        r"Assign to Verification Officer for priority review\.",
        "Make Verification Officer check this matter sharp-sharp.",
    ),
]


class MultilingualEngine:
    """Multilingual language detection, normalization, and translation."""

    @classmethod
    def detect_language(cls, text: str) -> LanguageDetectionResponse:
        """
        Detect whether submitted text is in English, Nigerian Pidgin, Hausa, Yoruba, or Igbo.
        Returns confidence score and whether the language is supported for translation.
        """
        if not text or not text.strip():
            return LanguageDetectionResponse(
                text=text or "",
                detected_language="en",
                language_name="English",
                confidence=1.0,
                is_supported=True,
                message="Defaulted to English for empty or whitespace input.",
            )

        norm_text = text.lower()
        words = set(re.findall(r"\b[a-zA-Z-]{2,}\b", norm_text))

        # Check for phrase or keyword hits
        pidgin_hits = len([p for p in PIDGIN_LEXICON if f" {p} " in f" {norm_text} " or p in words])
        hausa_hits = len(words.intersection(HAUSA_LEXICON))
        yoruba_hits = len(words.intersection(YORUBA_LEXICON))
        igbo_hits = len(words.intersection(IGBO_LEXICON))

        total_words = max(len(words), 1)

        # Evaluate Pidgin
        if pidgin_hits >= 2 or (pidgin_hits == 1 and total_words <= 6):
            conf = min(0.60 + (pidgin_hits * 0.15), 0.98)
            return LanguageDetectionResponse(
                text=text,
                detected_language="pcm",
                language_name="Nigerian Pidgin",
                confidence=round(conf, 2),
                is_supported=True,
                message="Detected Nigerian Pidgin dialect.",
            )

        # Evaluate Hausa
        if hausa_hits >= 2 or (hausa_hits == 1 and total_words <= 6):
            conf = min(0.60 + (hausa_hits * 0.15), 0.95)
            return LanguageDetectionResponse(
                text=text,
                detected_language="ha",
                language_name="Hausa",
                confidence=round(conf, 2),
                is_supported=False,
                message="Detected Hausa. Native model translation pipeline queued for future release.",
            )

        # Evaluate Yoruba
        if yoruba_hits >= 2 or (yoruba_hits == 1 and total_words <= 6):
            conf = min(0.60 + (yoruba_hits * 0.15), 0.95)
            return LanguageDetectionResponse(
                text=text,
                detected_language="yo",
                language_name="Yoruba",
                confidence=round(conf, 2),
                is_supported=False,
                message="Detected Yoruba. Native model translation pipeline queued for future release.",
            )

        # Evaluate Igbo
        if igbo_hits >= 2 or (igbo_hits == 1 and total_words <= 6):
            conf = min(0.60 + (igbo_hits * 0.15), 0.95)
            return LanguageDetectionResponse(
                text=text,
                detected_language="ig",
                language_name="Igbo",
                confidence=round(conf, 2),
                is_supported=False,
                message="Detected Igbo. Native model translation pipeline queued for future release.",
            )

        # Default to English
        return LanguageDetectionResponse(
            text=text,
            detected_language="en",
            language_name="English",
            confidence=0.92,
            is_supported=True,
            message="Standard English input detected.",
        )

    @classmethod
    def translate_pidgin_to_english(cls, text: str) -> TranslationResponse:
        """
        Translate Nigerian Pidgin submission into standard English for claim matching,
        while preserving original user content.
        """
        translated = text
        for pattern, replacement in PIDGIN_TO_ENGLISH_PHRASES:
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)

        # Common single word mappings
        word_subs = {
            "una": "you all",
            "wetin": "what",
            "sef": "even",
            "abeg": "please",
            "oya": "now",
            "dey": "is",
            "don": "has",
        }
        tokens = translated.split()
        normalized_tokens = [word_subs.get(t.lower(), t) for t in tokens]
        translated = " ".join(normalized_tokens)

        return TranslationResponse(
            original_text=text,
            translated_text=translated,
            source_language="pcm",
            target_language="en",
            translation_label="Machine Translation (Nigerian Pidgin to English) — Original narrative preserved.",
            is_machine_translated=True,
        )

    @classmethod
    def translate_english_to_pidgin(cls, text: str) -> TranslationResponse:
        """
        Translate an official approved clarification or advisory into Nigerian Pidgin
        for accessible citizen consumption and audio read-aloud.
        """
        translated = text
        for pattern, replacement in ENGLISH_TO_PIDGIN_PHRASES:
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)

        return TranslationResponse(
            original_text=text,
            translated_text=translated,
            source_language="en",
            target_language="pcm",
            translation_label="Machine Translation (Nigerian Pidgin) — Official source is in English.",
            is_machine_translated=True,
        )
