"""Abstract Base Class for AI Misinformation Intelligence Providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAIProvider(ABC):
    """Modular AI Provider Interface enabling pluggable Local and Cloud-backed models."""

    @abstractmethod
    def extract_atomic_claims(self, text: str) -> List[str]:
        """Isolate discrete factual electoral statements from raw user narrative."""
        pass

    @abstractmethod
    def classify_electoral_category(self, claim_text: str) -> Dict[str, Any]:
        """Classify statement into electoral taxonomy with confidence score."""
        pass

    @abstractmethod
    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate semantic and lexical similarity score between two texts (0.0 to 1.0)."""
        pass

    @abstractmethod
    def evaluate_claim_against_sources(
        self,
        claim_text: str,
        official_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate a claim against a reference set of official documents.
        Returns structured analysis adhering to responsible AI invariants.
        """
        pass
