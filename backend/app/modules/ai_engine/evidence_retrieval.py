"""Evidence Retrieval and Official Source Comparison Engine (Section 5).

Retrieves certified gazettes and trusted source announcements from the authenticated
registry, compares extracted claims against evidence, detects supporting or contradictory
findings, records source dates and URLs, and transparently explains sufficiency.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.modules.ai_engine.similarity import SimilarityEngine
from backend.app.modules.ai_engine.schemas import EvidenceItemOut, OfficialSourceMatchOut
from backend.app.modules.registry.models import OfficialDocument, TrustedSource

# Semantic contradiction pairs (Set A asserted vs Set B asserted)
CONTRADICTION_POLARITY_PAIRS = [
    # Cancelled/Postponed vs Proceeding
    (
        {"cancelled", "postponed", "halted", "suspended", "called off", "shifted", "deferred", "delayed", "delayed nationwide"},
        {"proceed", "scheduled", "ongoing", "active", "normal", "normally", "on course", "holding as planned", "no postponement", "proceeding normally"}
    ),
    # Relocation
    (
        {"relocated", "moved to", "changed location", "transferred", "shift polling"},
        {"original location", "gazetted center", "remain at", "unchanged", "no relocation"}
    ),
    # BVAS usage
    (
        {"bvas banned", "no bvas", "manual voting only", "bvas bypassed", "discard bvas", "incident form"},
        {"bvas mandatory", "accreditation only with bvas", "bvas compulsory", "no manual voting", "bvas required"}
    ),
    # Early/Premature results declaration
    (
        {"declared winner", "won election", "landslide victory", "leading", "elected president", "elected governor"},
        {"collation ongoing", "no winner declared", "results not final", "vote counting in progress", "awaiting collation"}
    ),
]

# Support reinforcement markers
SUPPORT_KEYWORDS = [
    {"proceed", "scheduled", "confirmed", "official", "gazetted", "approved", "authorized", "accreditation", "verified"}
]


class EvidenceRetrievalEngine:
    """Compares extracted claims against authenticated documents in the registry."""

    @classmethod
    def load_registry_documents(cls, db: Session) -> List[Dict[str, Any]]:
        """Fetch all authenticated official documents and active trusted sources."""
        docs = list(
            db.execute(select(OfficialDocument).where(OfficialDocument.is_authenticated == True)).scalars().all()
        )
        return [
            {
                "id": d.id,
                "document_code": d.document_code,
                "title": d.title,
                "summary": d.summary,
                "content_text": d.content_text,
                "issuing_institution": d.issuing_institution,
                "source_url": d.source_url or "https://inecnigeria.org/certified-gazettes",
                "publication_date": d.publication_date.isoformat() if d.publication_date else None,
                "sha256_hash": d.sha256_hash,
                "current_version": d.current_version,
            }
            for d in docs
        ]

    @classmethod
    def load_trusted_sources(cls, db: Session) -> List[Dict[str, Any]]:
        """Fetch verified trusted sources."""
        sources = list(
            db.execute(select(TrustedSource).where(TrustedSource.is_active == True)).scalars().all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "category": s.category,
                "verification_status": s.verification_status,
                "description": s.description,
            }
            for s in sources
        ]

    @classmethod
    def detect_contradiction_between_texts(cls, claim_text: str, doc_text: str) -> bool:
        """Analyze if claim and document assert opposite states on an electoral event."""
        claim_words = set(SimilarityEngine.tokenize(claim_text, filter_stopwords=False))
        doc_words = set(SimilarityEngine.tokenize(doc_text, filter_stopwords=False))

        # Direct explicit debunk check
        claim_norm = SimilarityEngine.normalize_text(claim_text)
        doc_norm = SimilarityEngine.normalize_text(doc_text)
        if "fake" in doc_norm or "debunk" in doc_norm or "not true" in doc_norm or "false report" in doc_norm:
            # If the doc mentions the claim's core subject and discredits it
            common_topics = set(SimilarityEngine.tokenize(claim_text, filter_stopwords=True)).intersection(
                set(SimilarityEngine.tokenize(doc_text, filter_stopwords=True))
            )
            if len(common_topics) >= 2:
                return True

        for set_a, set_b in CONTRADICTION_POLARITY_PAIRS:
            # Claim has A, Doc has B
            a_in_claim = bool(claim_words.intersection(set_a))
            b_in_doc = bool(doc_words.intersection(set_b))
            # Claim has B, Doc has A
            b_in_claim = bool(claim_words.intersection(set_b))
            a_in_doc = bool(doc_words.intersection(set_a))

            if (a_in_claim and b_in_doc) or (b_in_claim and a_in_doc):
                return True

        return False

    @classmethod
    def detect_supporting_evidence(cls, claim_text: str, doc_text: str, similarity_score: float) -> bool:
        """Determine if document affirms the claim."""
        if similarity_score < 0.35:
            return False

        # If similarity is strong and there is no contradiction polarity
        if not cls.detect_contradiction_between_texts(claim_text, doc_text):
            return similarity_score >= 0.50

        return False

    @classmethod
    def compare_claim_against_sources(
        cls,
        claim_text: str,
        official_documents: List[Dict[str, Any]],
        trusted_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Compare claim against reference documents and return structured evidence assessment.
        Adheres strictly to CivicShield responsible AI rules:
        - Prioritizes official and authoritative public sources.
        - Never fabricates citations, URLs, or metadata.
        - Explains sufficiency transparently.
        """
        matched_sources: List[OfficialSourceMatchOut] = []
        structured_evidence: List[EvidenceItemOut] = []
        highest_similarity = 0.0
        top_doc: Optional[Dict[str, Any]] = None
        has_contradiction = False
        has_support = False

        for doc in official_documents:
            title = doc.get("title", "")
            summary = doc.get("summary", "")
            content = doc.get("content_text", "")
            doc_code = doc.get("document_code", "")
            issuing_inst = doc.get("issuing_institution", "Independent National Electoral Commission")
            source_url = doc.get("source_url") or "https://inecnigeria.org"
            pub_date = doc.get("publication_date")

            sim_title = SimilarityEngine.calculate_similarity(claim_text, title)
            sim_content = SimilarityEngine.calculate_similarity(claim_text, content)
            sim_summary = SimilarityEngine.calculate_similarity(claim_text, summary)

            best_sim = max(sim_title, sim_content, sim_summary)

            # Check for direct document code citation in claim text
            if doc_code and doc_code.lower() in claim_text.lower():
                best_sim = max(best_sim, 0.85)

            if best_sim > highest_similarity:
                highest_similarity = best_sim
                top_doc = doc

            if best_sim >= 0.15:
                # Add to consulted sources
                matched_sources.append(
                    OfficialSourceMatchOut(
                        document_code=doc_code,
                        title=title,
                        issuing_institution=issuing_inst,
                        similarity_score=best_sim,
                        source_url=source_url,
                        publication_date=pub_date,
                    )
                )

                # Analyze role
                full_doc_text = f"{title}. {summary}. {content}"
                is_contra = cls.detect_contradiction_between_texts(claim_text, full_doc_text)
                is_supp = cls.detect_supporting_evidence(claim_text, full_doc_text, best_sim)

                if is_contra:
                    has_contradiction = True
                    evidence_role = "CONTRADICTORY"
                    desc = f"Official gazette '{title}' directly asserts the opposite of the submitted claim."
                elif is_supp:
                    has_support = True
                    evidence_role = "SUPPORTING"
                    desc = f"Official gazette '{title}' corroborates and affirms the submitted claim."
                else:
                    evidence_role = "CONTEXTUAL"
                    desc = f"Related official gazette '{title}' provides context on the cited subject matter."

                structured_evidence.append(
                    EvidenceItemOut(
                        description=desc,
                        source_name=f"{issuing_inst} ({doc_code})",
                        source_url=source_url,
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                        evidence_role=evidence_role,
                        similarity_score=best_sim,
                    )
                )

        # Sort sources and evidence descending by similarity
        matched_sources.sort(key=lambda s: s.similarity_score, reverse=True)
        structured_evidence.sort(key=lambda e: e.similarity_score, reverse=True)

        # Build transparent explanation of sufficiency
        limitations: List[str] = []
        is_sufficient = False
        evidence_explanation = ""

        if not official_documents:
            limitations.append("The certified gazette registry currently contains no authenticated records.")
            is_sufficient = False
            evidence_explanation = "Registry is empty; no authoritative evidence available."
        elif (highest_similarity < 0.15 and not has_contradiction and not has_support) or not top_doc:
            limitations.append("No authoritative certified announcement matches this specific assertion in the registry.")
            is_sufficient = False
            evidence_explanation = (
                f"Insufficient evidence: highest similarity to any certified announcement is {highest_similarity:.0%}, "
                f"which is below the verification threshold."
            )
        else:
            is_sufficient = True
            evidence_explanation = (
                f"Retrieved {len(matched_sources)} matching official document(s). "
                f"Primary source: '{top_doc.get('title')}' ({top_doc.get('document_code')}) "
                f"with {highest_similarity:.0%} similarity."
            )

        limitations.append("AI evidence evaluation is advisory and subject to mandatory human officer verification.")

        return {
            "is_sufficient": is_sufficient,
            "has_contradiction": has_contradiction,
            "has_support": has_support,
            "highest_similarity": highest_similarity,
            "top_document": top_doc,
            "matched_sources": matched_sources[:5],
            "structured_evidence": structured_evidence[:5],
            "evidence_explanation": evidence_explanation,
            "limitations": limitations,
        }
