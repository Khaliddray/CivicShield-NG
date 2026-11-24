"""AI Misinformation Intelligence Orchestrator Service (Member 2).

Orchestrates:
- Defensive prompt sanitization (PromptDefense)
- Discrete claim and entity extraction (ClaimExtractionEngine)
- Official source retrieval and grounding (EvidenceRetrievalEngine)
- Electoral information classification (ElectoralInformationClassifier)
- Multi-tier semantic similarity detection (SimilarityEngine)
- Multilingual dialect processing and translation (MultilingualEngine)
- Accessibility voice transcription integration (SpeechTranscriptionService)
- Responsible AI guardrail enforcement (ResponsibleAISafetyEngine)
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.modules.ai_engine.prompt_defense import PromptDefense
from backend.app.modules.ai_engine.claim_extractor import ClaimExtractionEngine
from backend.app.modules.ai_engine.similarity import SimilarityEngine
from backend.app.modules.ai_engine.evidence_retrieval import EvidenceRetrievalEngine
from backend.app.modules.ai_engine.classifier import ElectoralInformationClassifier
from backend.app.modules.ai_engine.multilingual import MultilingualEngine
from backend.app.modules.ai_engine.speech import SpeechTranscriptionService
from backend.app.modules.ai_engine.safety import ResponsibleAISafetyEngine
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.providers.factory import get_ai_provider
from backend.app.modules.ai_engine.schemas import (
    ClaimAnalysisRequest,
    ClaimAnalysisResponse,
    OfficialSourceMatchOut,
    EvidenceItemOut,
    StructuredAIAssessment,
    ClaimExtractionResponse,
    SimilarityDetectionResponse,
    SimilarReportMatch,
)
from backend.app.modules.registry.models import OfficialDocument, TrustedSource
from backend.app.modules.reporting.models import Report, UploadedEvidence
from backend.app.modules.verification.models import Claim
from backend.app.common.enums import ReportStatus, VerificationDecision


class AIEngineService:
    """Orchestrates defensive input sanitization, claim extraction, and official source correlation."""

    _provider: Optional[BaseAIProvider] = None

    @classmethod
    def get_provider(cls) -> BaseAIProvider:
        """Retrieve active AI Provider according to configuration."""
        if cls._provider is None:
            cls._provider = get_ai_provider()
        return cls._provider

    @classmethod
    def set_provider(cls, provider: BaseAIProvider) -> None:
        """Explicitly override AI provider (primarily for isolated test harnesses)."""
        cls._provider = provider

    # ---------------------------------------------------------
    # 1. Claim Extraction Service (Section 3)
    # ---------------------------------------------------------

    @classmethod
    def extract_claims(
        cls,
        text: str,
        context_state: Optional[str] = None,
    ) -> ClaimExtractionResponse:
        """
        Extract discrete factual claims and electoral entities from text.
        Handles Nigerian Pidgin normalization and preserves original text.
        """
        # 1. Defensively sanitize against adversarial prompts
        sanitized_text, injection_detected, _ = PromptDefense.sanitize_input(text)

        # 2. Check language
        lang_res = MultilingualEngine.detect_language(sanitized_text)

        # If Pidgin, translate to English for entity and assertion extraction while preserving original
        process_text = sanitized_text
        is_translated = False
        if lang_res.detected_language == "pcm":
            trans_res = MultilingualEngine.translate_pidgin_to_english(sanitized_text)
            process_text = trans_res.translated_text
            is_translated = True

        extraction_result = ClaimExtractionEngine.extract_claims(
            text=process_text,
            context_state=context_state,
        )

        extraction_result.original_text = text
        extraction_result.detected_language = lang_res.detected_language
        extraction_result.is_translated = is_translated

        return extraction_result

    # ---------------------------------------------------------
    # 2. Complete Claim Analysis Pipeline (Section 4, 5, 6)
    # ---------------------------------------------------------

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
                "source_url": doc.source_url,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
            }
            for doc in official_docs
        ]

        # 3. Evaluate claim against official sources with resilience
        try:
            assessment = provider.evaluate_claim_against_sources(
                claim_text=sanitized_text,
                official_sources=reference_data,
            )

            # Build source list and models
            consulted_models: List[OfficialSourceMatchOut] = []
            for s in assessment.get("sources_consulted", []):
                if isinstance(s, dict):
                    consulted_models.append(OfficialSourceMatchOut(**s))
                elif isinstance(s, OfficialSourceMatchOut):
                    consulted_models.append(s)

            sources_list = [
                f"{s.issuing_institution or 'INEC'}: {s.title or s.document_code}"
                for s in consulted_models
            ]

            # Build evidence list
            raw_evidence = assessment.get("evidence", [])
            evidence_out_list: List[Union[str, EvidenceItemOut]] = []
            for ev in raw_evidence:
                if isinstance(ev, dict):
                    evidence_out_list.append(EvidenceItemOut(**ev))
                elif isinstance(ev, str):
                    evidence_out_list.append(ev)

            if not evidence_out_list:
                evidence_out_list = [s.title for s in consulted_models if s.title]

            return ClaimAnalysisResponse(
                extracted_claim=assessment.get("extracted_claim", sanitized_text),
                category=assessment.get("category", "GENERAL_ELECTORAL"),
                category_confidence=assessment.get("category_confidence", 0.8),
                ai_confidence_score=assessment.get("ai_confidence_score", 0.0),
                ai_suggested_status=assessment.get("ai_suggested_status", "UNVERIFIED"),
                analysis_summary=assessment.get("analysis_summary", "Claim evaluated against official registry."),
                contradiction_suspected=assessment.get("contradiction_suspected", False),
                sources_consulted=consulted_models,
                recommended_next_action=assessment.get(
                    "recommended_next_action", "Assign to Verification Officer for review."
                ),
                requires_human_review=True,  # Non-negotiable responsible AI rule
                adversarial_injection_detected=injection_detected,
                # Structured contract fields
                claim=assessment.get("extracted_claim", sanitized_text),
                classification=assessment.get("classification") or assessment.get("ai_suggested_status"),
                confidence=assessment.get("ai_confidence_score", 0.0),
                evidence=evidence_out_list,
                sources=sources_list,
                limitations=assessment.get("limitations", [
                    "Automated analysis is heuristic and non-binding.",
                    "Grounding restricted to certified gazettes in local registry.",
                ]),
                service_available=True,
            )
        except Exception as exc:
            logger.error(f"AI Service processing error or timeout: {exc}")
            # Graceful degraded fallback adhering strictly to prompt requirements
            return ClaimAnalysisResponse(
                extracted_claim=sanitized_text,
                category="GENERAL_ELECTORAL",
                category_confidence=0.0,
                ai_confidence_score=0.0,
                ai_suggested_status="INSUFFICIENT_EVIDENCE",
                analysis_summary="AI verification service is temporarily unavailable or timed out. Manual review required.",
                contradiction_suspected=False,
                sources_consulted=[],
                recommended_next_action="Assign to Verification Officer for manual review.",
                requires_human_review=True,
                adversarial_injection_detected=injection_detected,
                claim=sanitized_text,
                classification="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                evidence=[],
                sources=[],
                limitations=["AI Service unavailable or timed out; cannot verify automatically."],
                service_available=False,
                error_message=str(exc),
            )

    # ---------------------------------------------------------
    # 3. Standard Structured AI Assessment Contract (Section 6)
    # ---------------------------------------------------------

    @classmethod
    def generate_structured_assessment(
        cls,
        db: Session,
        claim_text: str,
        context_state: Optional[str] = None,
    ) -> StructuredAIAssessment:
        """Generate structured AI assessment conforming to Member 1 backend contract."""
        analysis = cls.analyze_claim_text(
            db=db,
            request=ClaimAnalysisRequest(claim_text=claim_text, context_state=context_state),
        )

        structured_evidence: List[EvidenceItemOut] = []
        for ev in analysis.evidence:
            if isinstance(ev, EvidenceItemOut):
                structured_evidence.append(ev)
            elif isinstance(ev, dict):
                structured_evidence.append(EvidenceItemOut(**ev))
            elif isinstance(ev, str):
                structured_evidence.append(
                    EvidenceItemOut(
                        description=ev,
                        source_name="Official Gazette Registry",
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                    )
                )

        return StructuredAIAssessment(
            claim=analysis.extracted_claim,
            classification=analysis.classification or "INSUFFICIENT_EVIDENCE",
            confidence=analysis.confidence or 0.0,
            evidence=structured_evidence,
            sources=analysis.sources,
            limitations=analysis.limitations,
            requires_human_review=True,
            service_available=analysis.service_available,
            reasoning=analysis.analysis_summary,
        )

    # ---------------------------------------------------------
    # 4. Report Claims Extraction & Ingestion Pipeline (Member 1 Integration)
    # ---------------------------------------------------------

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
                "summary": doc.summary,
                "issuing_institution": doc.issuing_institution,
                "source_url": doc.source_url,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
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
            try:
                assessment = provider.evaluate_claim_against_sources(claim_text, reference_data)
                claim = Claim(
                    report_id=report.id,
                    claim_text=claim_text,
                    category=assessment.get("category", "GENERAL_ELECTORAL"),
                    ai_confidence_score=assessment.get("ai_confidence_score", 0.0),
                    ai_analysis_summary=assessment.get("analysis_summary", "Analyzed against official registry."),
                    ai_suggested_status=assessment.get("ai_suggested_status", "UNVERIFIED"),
                    requires_human_review=True,
                )
            except Exception as exc:
                logger.error(f"Error evaluating claim '{claim_text[:50]}': {exc}")
                claim = Claim(
                    report_id=report.id,
                    claim_text=claim_text,
                    category="GENERAL_ELECTORAL",
                    ai_confidence_score=0.0,
                    ai_analysis_summary="AI evaluation timed out or failed. Manual verification required.",
                    ai_suggested_status="INSUFFICIENT_EVIDENCE",
                    requires_human_review=True,
                )
            db.add(claim)
            persisted_claims.append(claim)

        # Update report status to UNDER_REVIEW
        report.status = ReportStatus.UNDER_REVIEW.value
        db.commit()

        logger.info(f"Report {report.reference_number}: extracted and analyzed {len(persisted_claims)} atomic claims.")
        return persisted_claims

    # ---------------------------------------------------------
    # 5. Similarity Detection Service (Section 7)
    # ---------------------------------------------------------

    @classmethod
    def detect_similar_reports(
        cls,
        db: Session,
        target_text: str,
        target_report_id: Optional[str] = None,
        candidate_reports: Optional[List[Dict[str, Any]]] = None,
        threshold: float = 0.70,
    ) -> SimilarityDetectionResponse:
        """
        Compare report or claim text against recent reports in the database or candidate list.
        Returns candidate matches with exact algorithmically derived similarity scores.
        """
        candidates: List[Dict[str, Any]] = []

        if candidate_reports is not None:
            candidates = candidate_reports
        else:
            # Query recent 100 reports from DB
            recent_reps = list(
                db.execute(select(Report).order_by(desc(Report.created_at)).limit(100)).scalars().all()
            )
            candidates = [
                {
                    "id": r.id,
                    "title": r.title,
                    "content_text": r.content_text,
                    "text": f"{r.title} {r.content_text}",
                }
                for r in recent_reps
            ]

        return SimilarityEngine.find_similar_reports(
            target_text=target_text,
            candidate_reports=candidates,
            target_report_id=target_report_id,
            threshold=threshold,
        )

    # ---------------------------------------------------------
    # 6. Multilingual Processing Service (Section 9)
    # ---------------------------------------------------------

    @classmethod
    def process_multilingual_text(cls, text: str) -> Dict[str, Any]:
        """Detect language, normalize, and provide English and Nigerian Pidgin translations."""
        det = MultilingualEngine.detect_language(text)

        if det.detected_language == "pcm":
            trans = MultilingualEngine.translate_pidgin_to_english(text)
            return {
                "detected_language": det.detected_language,
                "language_name": det.language_name,
                "confidence": det.confidence,
                "original_text": text,
                "english_translation": trans.translated_text,
                "translation_label": trans.translation_label,
            }
        else:
            trans_pidgin = MultilingualEngine.translate_english_to_pidgin(text)
            return {
                "detected_language": det.detected_language,
                "language_name": det.language_name,
                "confidence": det.confidence,
                "original_text": text,
                "pidgin_translation": trans_pidgin.translated_text,
                "translation_label": trans_pidgin.translation_label,
            }
