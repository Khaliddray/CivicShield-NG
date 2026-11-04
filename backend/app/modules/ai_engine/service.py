"""AI Misinformation Intelligence Orchestrator Service."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.modules.ai_engine.prompt_defense import PromptDefense
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.providers.local_heuristic import LocalHeuristicAIProvider
from backend.app.modules.ai_engine.schemas import ClaimAnalysisRequest, ClaimAnalysisResponse, OfficialSourceMatchOut
from backend.app.modules.registry.models import OfficialDocument
from backend.app.modules.reporting.models import Report
from backend.app.modules.verification.models import Claim
from backend.app.common.enums import ReportStatus


class AIEngineService:
    """Orchestrates defensive input sanitization, claim extraction, and official source correlation."""

    _provider: BaseAIProvider = LocalHeuristicAIProvider()

    @classmethod
    def get_provider(cls) -> BaseAIProvider:
        """Retrieve active AI Provider."""
        return cls._provider

    @classmethod
    def analyze_claim_text(
        cls,
        db: Session,
        request: ClaimAnalysisRequest,
    ) -> ClaimAnalysisResponse:
        """Run complete defensive analysis on an individual claim against the official registry."""
        provider = cls.get_provider()

        # 1. Prompt Injection Defense
        sanitized_text, injection_detected, detected_patterns = PromptDefense.sanitize_input(request.claim_text)
        if injection_detected:
            logger.warning(f"Adversarial prompt injection pattern detected and neutralized: {detected_patterns}")

        # 2. Retrieve reference dataset of authenticated documents
        official_docs = list(db.execute(select(OfficialDocument).where(OfficialDocument.is_authenticated == True)).scalars().all())
        reference_data = [
            {
                "document_code": doc.document_code,
                "title": doc.title,
                "summary": doc.summary,
                "content_text": doc.content_text,
                "issuing_institution": doc.issuing_institution,
            }
            for doc in official_docs
        ]

        # 3. Evaluate claim against official sources
        assessment = provider.evaluate_claim_against_sources(
            claim_text=sanitized_text,
            official_sources=reference_data,
        )

        return ClaimAnalysisResponse(
            extracted_claim=assessment["extracted_claim"],
            category=assessment["category"],
            category_confidence=assessment["category_confidence"],
            ai_confidence_score=assessment["ai_confidence_score"],
            ai_suggested_status=assessment["ai_suggested_status"],
            analysis_summary=assessment["analysis_summary"],
            contradiction_suspected=assessment["contradiction_suspected"],
            sources_consulted=[OfficialSourceMatchOut(**s) for s in assessment["sources_consulted"]],
            recommended_next_action=assessment["recommended_next_action"],
            requires_human_review=True,  # Non-negotiable responsible AI rule
            adversarial_injection_detected=injection_detected,
        )

    @classmethod
    def process_report_claims(cls, db: Session, report_id: str) -> List[Claim]:
        """Extract atomic claims from a citizen report, evaluate each against the registry, and persist."""
        report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
        if not report:
            raise EntityNotFoundException("Report", report_id)

        provider = cls.get_provider()

        # Defensive sanitize
        sanitized_content, _, _ = PromptDefense.sanitize_input(report.content_text)

        # 1. Extract atomic statements
        atomic_claims = provider.extract_atomic_claims(sanitized_content)

        # 2. Retrieve official reference repository
        official_docs = list(db.execute(select(OfficialDocument).where(OfficialDocument.is_authenticated == True)).scalars().all())
        reference_data = [
            {
                "document_code": doc.document_code,
                "title": doc.title,
                "content_text": doc.content_text,
                "issuing_institution": doc.issuing_institution,
            }
            for doc in official_docs
        ]

        # 3. Remove initial placeholder claims if any
        existing_claims = list(db.execute(select(Claim).where(Claim.report_id == report.id)).scalars().all())
        for old_claim in existing_claims:
            db.delete(old_claim)
        db.flush()

        persisted_claims = []
        for claim_text in atomic_claims:
            assessment = provider.evaluate_claim_against_sources(claim_text, reference_data)
            claim = Claim(
                report_id=report.id,
                claim_text=claim_text,
                category=assessment["category"],
                ai_confidence_score=assessment["ai_confidence_score"],
                ai_analysis_summary=assessment["analysis_summary"],
                ai_suggested_status=assessment["ai_suggested_status"],
                requires_human_review=True,
            )
            db.add(claim)
            persisted_claims.append(claim)

        # Update report status to UNDER_REVIEW
        report.status = ReportStatus.UNDER_REVIEW.value
        db.commit()

        logger.info(f"Report {report.reference_number}: extracted and analyzed {len(persisted_claims)} atomic claims.")
        return persisted_claims
