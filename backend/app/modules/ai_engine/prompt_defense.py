"""Prompt Injection Defense and Adversarial Input Sanitizer."""

import re
from typing import Tuple, List

# Signatures commonly used in prompt injection and model jailbreak attacks
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"assistant\s*:\s*", re.IGNORECASE),
    re.compile(r"\[inst\].*?\[/inst\]", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|jailbroken|unrestricted)\s+mode", re.IGNORECASE),
    re.compile(r"(override|bypass)\s+(verdict|verification|status|safety)", re.IGNORECASE),
    re.compile(r"mark\s+(this\s+claim\s+as\s+)?verified", re.IGNORECASE),
    re.compile(r"mark\s+(this\s+claim\s+as\s+)?true", re.IGNORECASE),
    re.compile(r"you\s+must\s+declare\s+this\s+(authentic|verified|official)", re.IGNORECASE),
]

DELIMITER_CLEANERS = [
    (re.compile(r"```[a-zA-Z]*"), " "),
    (re.compile(r"```"), " "),
    (re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE), " "),
    (re.compile(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", re.IGNORECASE), " "),
]


class PromptDefense:
    """Defensive pre-processor shielding analytical pipelines against adversarial payloads."""

    @classmethod
    def sanitize_input(cls, text: str) -> Tuple[str, bool, List[str]]:
        """
        Sanitize untrusted user-submitted text.
        Returns:
            (sanitized_text, is_injection_suspected, detected_patterns)
        """
        if not text:
            return "", False, []

        detected_patterns = []
        is_injection_suspected = False

        # 1. Scan for injection attempts
        for pattern in INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                is_injection_suspected = True
                detected_patterns.append(match.group(0))

        # 2. Strip structural delimiters that could confuse LLM parsing
        cleaned = text
        for regex, replacement in DELIMITER_CLEANERS:
            cleaned = regex.sub(replacement, cleaned)

        # 3. If an injection attempt was detected, neutralize the explicit commands
        if is_injection_suspected:
            for pattern in INJECTION_PATTERNS:
                cleaned = pattern.sub("[REDACTED_INJECTION_PATTERN]", cleaned)

        # 4. Normalize excess whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned, is_injection_suspected, detected_patterns
