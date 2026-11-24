"""Similarity Detection and Duplicate Report Identification Engine (Section 7).

Provides text normalization, exact duplicate detection (SHA-256 normalized hash),
and multi-tier semantic similarity (Jaccard + Word Bigrams + Character 3-grams)
without requiring heavy external vector databases.
"""

import re
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Any
from backend.app.modules.ai_engine.schemas import (
    SimilarReportMatch,
    SimilarityDetectionResponse,
)

# Crucial electoral stopwords to filter during lexical matching,
# while carefully preserving polarity/negation markers (e.g. 'not', 'no', 'cancelled').
ELECTORAL_STOP_WORDS = {
    "the", "in", "and", "has", "been", "that", "all", "on", "as", "according",
    "to", "for", "at", "with", "by", "of", "is", "a", "an", "this", "are",
    "will", "from", "be", "were", "was", "or", "so", "it", "its", "their",
    "they", "there", "have", "had", "would", "should", "could", "about",
    "into", "than", "then", "very", "just", "also", "these", "those"
}


class SimilarityEngine:
    """Text normalization, exact duplicate detection, and semantic similarity calculation."""

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalize text for consistent comparison:
        - Lowercase
        - Remove URLs and structural delimiters
        - Strip punctuation
        - Collapse whitespace
        """
        if not text:
            return ""

        # Remove URLs
        cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
        # Lowercase
        cleaned = cleaned.lower()
        # Keep alphanumeric, hyphens, and whitespace
        cleaned = re.sub(r"[^a-z0-9\s-]", " ", cleaned)
        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def compute_text_hash(cls, text: str) -> str:
        """Compute SHA-256 hash of normalized text for instant exact-duplicate detection."""
        normalized = cls.normalize_text(text)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def tokenize(cls, text: str, filter_stopwords: bool = True) -> List[str]:
        """Extract clean words from normalized text."""
        norm = cls.normalize_text(text)
        tokens = [w for w in re.findall(r"\b[a-z0-9-]{2,}\b", norm)]
        if filter_stopwords:
            tokens = [w for w in tokens if w not in ELECTORAL_STOP_WORDS]
        return tokens

    @classmethod
    def make_word_bigrams(cls, tokens: List[str]) -> Set[str]:
        """Generate adjacent word bigrams for phrase structure comparison."""
        if len(tokens) < 2:
            return set()
        return {f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)}

    @classmethod
    def make_char_trigrams(cls, text: str) -> Dict[str, int]:
        """Generate character 3-grams frequency map for subword typo resilience."""
        norm = cls.normalize_text(text).replace(" ", "_")
        trigrams: Dict[str, int] = {}
        for i in range(len(norm) - 2):
            tri = norm[i:i+3]
            trigrams[tri] = trigrams.get(tri, 0) + 1
        return trigrams

    @classmethod
    def calculate_char_trigram_cosine(cls, text_a: str, text_b: str) -> float:
        """Cosine similarity over character trigram frequency vectors."""
        tri_a = cls.make_char_trigrams(text_a)
        tri_b = cls.make_char_trigrams(text_b)

        if not tri_a or not tri_b:
            return 0.0

        common_keys = set(tri_a.keys()).intersection(tri_b.keys())
        dot_product = sum(tri_a[k] * tri_b[k] for k in common_keys)

        mag_a = sum(v * v for v in tri_a.values()) ** 0.5
        mag_b = sum(v * v for v in tri_b.values()) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot_product / (mag_a * mag_b)

    @classmethod
    def calculate_similarity(cls, text_a: str, text_b: str) -> float:
        """
        Calculate semantic and lexical similarity score between two texts (0.0 to 1.0).
        Tier 1: Exact hash match -> 1.0
        Tier 2: Multi-layer hybrid (Jaccard + Word Bigrams + Char Trigrams)
        """
        if not text_a or not text_b:
            return 0.0

        norm_a = cls.normalize_text(text_a)
        norm_b = cls.normalize_text(text_b)

        if not norm_a or not norm_b:
            return 0.0

        # Exact match
        if norm_a == norm_b:
            return 1.0

        tokens_a = cls.tokenize(text_a, filter_stopwords=True)
        tokens_b = cls.tokenize(text_b, filter_stopwords=True)

        set_a = set(tokens_a)
        set_b = set(tokens_b)

        # Token Jaccard
        if not set_a or not set_b:
            jaccard = 0.0
        else:
            jaccard = len(set_a.intersection(set_b)) / len(set_a.union(set_b))

        # Word Bigram overlap
        bigrams_a = cls.make_word_bigrams(tokens_a)
        bigrams_b = cls.make_word_bigrams(tokens_b)
        if not bigrams_a or not bigrams_b:
            bigram_sim = 0.0
        else:
            bigram_sim = len(bigrams_a.intersection(bigrams_b)) / len(bigrams_a.union(bigrams_b))

        # Char trigram cosine
        trigram_sim = cls.calculate_char_trigram_cosine(text_a, text_b)

        # Weighted blend
        # If words match well, weight token + bigram; if slight typos, trigram catches it
        combined = (jaccard * 0.45) + (bigram_sim * 0.30) + (trigram_sim * 0.25)

        # Slight scaling for non-empty intersections
        if jaccard > 0.20:
            combined = min(combined * 1.25, 1.0)

        return round(float(combined), 3)

    @classmethod
    def find_similar_reports(
        cls,
        target_text: str,
        candidate_reports: List[Dict[str, Any]],
        target_report_id: Optional[str] = None,
        threshold: float = 0.70,
    ) -> SimilarityDetectionResponse:
        """
        Compare target text against candidate reports and return structured results.
        Safeguard: Never treat similarity as proof of common authorship.
        """
        similar_reports: List[SimilarReportMatch] = []
        top_score = 0.0

        for cand in candidate_reports:
            cand_id = cand.get("id") or cand.get("report_id") or "unknown"
            if target_report_id and cand_id == target_report_id:
                continue

            cand_text = cand.get("text") or cand.get("content_text") or cand.get("title") or ""
            score = cls.calculate_similarity(target_text, cand_text)

            if score > top_score:
                top_score = score

            if score >= threshold:
                similar_reports.append(
                    SimilarReportMatch(
                        report_id=cand_id,
                        similarity_score=score,
                        matching_reason=(
                            "Exact content duplicate" if score >= 0.98
                            else f"High semantic text overlap ({score:.0%})"
                        ),
                    )
                )

        # Sort matches descending by score
        similar_reports.sort(key=lambda x: x.similarity_score, reverse=True)

        return SimilarityDetectionResponse(
            report_id=target_report_id,
            similar_reports=similar_reports,
            requires_cluster_review=len(similar_reports) > 0,
            top_similarity_score=top_score,
        )
