"""Deterministic, zero-dependency NLP and heuristic AI Provider for offline and baseline operation."""

import re
from typing import Any, Dict, List, Set
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.common.enums import ClaimCategory, VerificationDecision

STOP_WORDS = {
    "the", "in", "and", "has", "been", "that", "all", "on", "as", "according",
    "to", "for", "at", "with", "by", "of", "is", "a", "an", "this", "are",
    "will", "from", "be", "were", "was", "or", "so", "it", "its"
}

ELECTORAL_TAXONOMY = {
    ClaimCategory.RESULTS_ANNOUNCEMENT.value: {
        "winner", "declared", "results", "vote count", "won", "leading", "margin", "tally", "landslide", "elected", "collation"
    },
    ClaimCategory.VOTER_SUPPRESSION.value: {
        "thugs", "snatched", "disenfranchised", "prevented", "intimidation", "turned away", "scared", "suppression", "locked out"
    },
    ClaimCategory.INEC_OPERATIONS.value: {
        "bvas", "ad-hoc", "polling unit", "relocated", "moved", "inec circular", "cancelled", "postponed", "registration", "pvc"
    },
    ClaimCategory.SECURITY_INCIDENT.value: {
        "police", "soldiers", "gunfire", "violence", "tear gas", "attack", "curfew", "clash", "security checkpoint", "armed"
    },
    ClaimCategory.LOGISTICS_DELAY.value: {
        "late arrival", "delayed", "materials missing", "no ink", "officials absent", "late opening", "transport", "stranded"
    },
    ClaimCategory.DISINFORMATION_CAMPAIGN.value: {
        "deepfake", "manipulated audio", "fake letter", "forged circular", "impersonation", "fake press release", "cloned website"
    },
}

CONTRADICTION_PAIRS = [
    ({"cancelled", "postponed", "halted", "suspended"}, {"proceed", "scheduled", "ongoing", "active", "normal"}),
    ({"relocated", "moved to", "changed location"}, {"original location", "gazetted center", "remain at", "unchanged"}),
    ({"bvas banned", "no bvas", "manual voting only"}, {"bvas mandatory", "accreditation only with bvas"}),
]


class LocalHeuristicAIProvider(BaseAIProvider):
    """Reliable, fast heuristic NLP processor requiring no external GPU or cloud API keys."""

    def extract_atomic_claims(self, text: str) -> List[str]:
        """Split text into sentences and isolate discrete electoral assertions."""
        if not text:
            return []

        raw_sentences = re.split(r"[.!?\n]+", text)
        claims = []

        assertion_markers = {
            "announced", "cancelled", "postponed", "moved", "relocated", "won", "declared",
            "results", "prohibited", "banned", "delayed", "closed", "attacked", "voters", "polling"
        }

        for sentence in raw_sentences:
            s = sentence.strip()
            words = set(re.findall(r"\b[a-zA-Z]{3,}\b", s.lower()))
            if len(words) >= 4 and any(marker in words for marker in assertion_markers):
                claims.append(s)

        if not claims:
            first_sentence = raw_sentences[0].strip() if raw_sentences else text.strip()
            if first_sentence:
                claims.append(first_sentence[:255])

        return claims[:5]

    def classify_electoral_category(self, claim_text: str) -> Dict[str, Any]:
        """Determine domain category based on weighted keyword presence."""
        words = set(re.findall(r"\b[a-zA-Z-]{3,}\b", claim_text.lower()))

        best_category = ClaimCategory.GENERAL_ELECTORAL.value
        best_score = 0
        matched_keywords = []

        for category, lexicon in ELECTORAL_TAXONOMY.items():
            matches = words.intersection(lexicon)
            if len(matches) > best_score:
                best_score = len(matches)
                best_category = category
                matched_keywords = list(matches)

        confidence = min(0.40 + (best_score * 0.15), 0.95) if best_score > 0 else 0.35

        return {
            "category": best_category,
            "confidence": round(confidence, 2),
            "matched_keywords": matched_keywords,
        }

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Compute stop-word filtered Jaccard token similarity with bigram reinforcement."""
        if not text_a or not text_b:
            return 0.0

        words_a = {w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", text_a.lower()) if w not in STOP_WORDS}
        words_b = {w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", text_b.lower()) if w not in STOP_WORDS}

        if not words_a or not words_b:
            return 0.0

        jaccard = len(words_a.intersection(words_b)) / len(words_a.union(words_b))

        # Bigram overlap
        def make_bigrams(words: Set[str]) -> Set[str]:
            sorted_w = sorted(list(words))
            return {f"{sorted_w[i]}_{sorted_w[i+1]}" for i in range(len(sorted_w)-1)}

        bi_a = make_bigrams(words_a)
        bi_b = make_bigrams(words_b)
        bigram_overlap = len(bi_a.intersection(bi_b)) / len(bi_a.union(bi_b)) if (bi_a and bi_b) else 0.0

        combined = (jaccard * 0.75) + (bigram_overlap * 0.25)
        return round(min(combined * 1.5, 1.0), 3)

    def evaluate_claim_against_sources(
        self,
        claim_text: str,
        official_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze claim against reference dataset of authenticated documents."""
        classification = self.classify_electoral_category(claim_text)
        claim_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", claim_text.lower()))

        matched_sources = []
        highest_similarity = 0.0
        top_match_doc = None
        is_contradiction_suspected = False

        for doc in official_sources:
            title_sim = self.calculate_similarity(claim_text, doc.get("title", ""))
            content_sim = self.calculate_similarity(claim_text, doc.get("content_text", ""))
            summary_sim = self.calculate_similarity(claim_text, doc.get("summary", ""))

            best_doc_sim = max(title_sim, content_sim, summary_sim)

            if best_doc_sim > 0.15:
                matched_sources.append({
                    "document_code": doc.get("document_code"),
                    "title": doc.get("title"),
                    "issuing_institution": doc.get("issuing_institution"),
                    "similarity_score": best_doc_sim,
                })
            if best_doc_sim > highest_similarity:
                highest_similarity = best_doc_sim
                top_match_doc = doc

        # Check for semantic contradiction with top matching document
        if top_match_doc and highest_similarity >= 0.15:
            doc_content = f"{top_match_doc.get('title', '')} {top_match_doc.get('content_text', '')}".lower()
            doc_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", doc_content))

            for neg_set, pos_set in CONTRADICTION_PAIRS:
                claim_has_neg = bool(claim_words.intersection(neg_set))
                doc_has_pos = bool(doc_words.intersection(pos_set))
                claim_has_pos = bool(claim_words.intersection(pos_set))
                doc_has_neg = bool(doc_words.intersection(neg_set))

                if (claim_has_neg and doc_has_pos) or (claim_has_pos and doc_has_neg):
                    is_contradiction_suspected = True
                    break

        # Invariant: AI never declares an electoral claim FALSE autonomously
        if is_contradiction_suspected and top_match_doc:
            suggested_status = VerificationDecision.UNDER_REVIEW.value
            summary = (
                f"Preliminary analysis identified potential contradiction with official release '{top_match_doc.get('title')}' "
                f"issued by {top_match_doc.get('issuing_institution')} (Similarity: {highest_similarity:.0%}). "
                f"Official gazette asserts the opposite of the submitted claim."
            )
            rec_action = "Assign to Verification Officer for priority human review and candidate clarification advisory."
        elif highest_similarity >= 0.70 and top_match_doc:
            suggested_status = VerificationDecision.UNDER_REVIEW.value
            summary = (
                f"Claim exhibits high similarity ({highest_similarity:.0%}) to certified announcement '{top_match_doc.get('title')}' "
                f"issued by {top_match_doc.get('issuing_institution')}."
            )
            rec_action = "Review whether claim is an accurate quote or partial excerpt of the official statement."
        else:
            suggested_status = VerificationDecision.UNVERIFIED.value
            summary = (
                f"No strongly matching certified announcements found in the reference registry (Max similarity: {highest_similarity:.0%}). "
                f"Claim classified under {classification['category']}."
            )
            rec_action = "Seek primary confirmation from the relevant state electoral authority."

        # Sort sources by similarity
        matched_sources.sort(key=lambda s: s["similarity_score"], reverse=True)

        return {
            "extracted_claim": claim_text,
            "category": classification["category"],
            "category_confidence": classification["confidence"],
            "ai_confidence_score": round(highest_similarity, 2),
            "ai_suggested_status": suggested_status,
            "analysis_summary": summary,
            "sources_consulted": matched_sources[:5],
            "contradiction_suspected": is_contradiction_suspected,
            "recommended_next_action": rec_action,
            "requires_human_review": True,  # Hard Invariant
        }
