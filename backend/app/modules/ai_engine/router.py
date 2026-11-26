"""AI Misinformation Intelligence API Endpoints (Member 2)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.ai_engine.schemas import (
    ClaimAnalysisRequest,
    ClaimAnalysisResponse,
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    StructuredAIAssessment,
    SimilarityDetectionRequest,
    SimilarityDetectionResponse,
    TranslationRequest,
    TranslationResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
)
from backend.app.modules.reporting.schemas import ClaimSummaryOut
from backend.app.modules.ai_engine.service import AIEngineService
from backend.app.modules.ai_engine.multilingual import MultilingualEngine

router = APIRouter(prefix="/ai", tags=["AI Misinformation Intelligence"])


@router.post(
    "/analyze-claim",
    response_model=APIResponse[ClaimAnalysisResponse],
    summary="Analyze suspicious claim against authenticated official registry (Public / Assistant)",
)
def analyze_claim(
    request_data: ClaimAnalysisRequest,
    db: Session = Depends(get_db),
) -> APIResponse[ClaimAnalysisResponse]:
    """Public / Citizen AI Assistant analysis endpoint verifying assertions against authenticated sources."""
    result = AIEngineService.analyze_claim_text(db=db, request=request_data)
    return APIResponse(
        data=result,
        message="AI claim intelligence assessment completed.",
    )


@router.post(
    "/extract-claims",
    response_model=APIResponse[ClaimExtractionResponse],
    summary="Extract discrete factual claims and electoral entities from text (Section 3)",
)
def extract_claims(
    request_data: ClaimExtractionRequest,
) -> APIResponse[ClaimExtractionResponse]:
    """Isolate factual claims, entities (dates, institutions, places), and claim types from submitted narrative."""
    result = AIEngineService.extract_claims(
        text=request_data.text,
        context_state=request_data.context_state,
    )
    return APIResponse(
        data=result,
        message=f"Extracted {len(result.claims)} discrete claim(s).",
    )


@router.post(
    "/assess",
    response_model=APIResponse[StructuredAIAssessment],
    summary="Generate structured evidence-backed assessment with transparent limitations (Section 6)",
)
def generate_structured_assessment(
    request_data: ClaimAnalysisRequest,
    db: Session = Depends(get_db),
) -> APIResponse[StructuredAIAssessment]:
    """Generates standard contract assessment with evidence citations, uncertainty, and limitations."""
    result = AIEngineService.generate_structured_assessment(
        db=db,
        claim_text=request_data.claim_text,
        context_state=request_data.context_state,
    )
    return APIResponse(
        data=result,
        message="Structured AI assessment generated successfully.",
    )


@router.post(
    "/similar-reports",
    response_model=APIResponse[SimilarityDetectionResponse],
    summary="Detect similar reports and duplicates without external vector DB (Section 7)",
)
def detect_similar_reports(
    request_data: SimilarityDetectionRequest,
    db: Session = Depends(get_db),
) -> APIResponse[SimilarityDetectionResponse]:
    """Calculates algorithmic similarity against database or candidate reports."""
    result = AIEngineService.detect_similar_reports(
        db=db,
        target_text=request_data.target_text,
        target_report_id=request_data.report_id,
        candidate_reports=request_data.candidate_reports,
        threshold=request_data.threshold,
    )
    return APIResponse(
        data=result,
        message=f"Similarity scan found {len(result.similar_reports)} matching report(s).",
    )


@router.post(
    "/reports/{report_id}/analyze",
    response_model=APIResponse[List[ClaimSummaryOut]],
    summary="Trigger AI claim extraction and official source matching for a report (Command Centre)",
)
def trigger_report_analysis(
    report_id: str,
    current_user: User = Depends(require_permission("claims:analyze")),
    db: Session = Depends(get_db),
) -> APIResponse[List[ClaimSummaryOut]]:
    """Command Centre analyst tool to isolate claims from submission content and cross-reference registry."""
    claims = AIEngineService.process_report_claims(db=db, report_id=report_id)
    return APIResponse(
        data=[ClaimSummaryOut.model_validate(c) for c in claims],
        message=f"Successfully extracted and evaluated {len(claims)} claim(s) for report.",
    )


@router.post(
    "/multilingual/detect",
    response_model=APIResponse[LanguageDetectionResponse],
    summary="Identify language of electoral submission (Section 9)",
)
def detect_language(
    payload: LanguageDetectionRequest,
) -> APIResponse[LanguageDetectionResponse]:
    """Detects English, Nigerian Pidgin, Hausa, Yoruba, or Igbo."""
    result = MultilingualEngine.detect_language(payload.text)
    return APIResponse(
        data=result,
        message=f"Detected language: {result.language_name}",
    )


@router.post(
    "/multilingual/translate",
    response_model=APIResponse[TranslationResponse],
    summary="Translate between English and Nigerian Pidgin with transparent labeling (Section 9)",
)
def translate_text(
    payload: TranslationRequest,
) -> APIResponse[TranslationResponse]:
    """Provides machine translation while preserving original user narrative."""
    source_lang = (payload.source_language or "pcm").lower()
    target_lang = (payload.target_language or "en").lower()

    if source_lang == "pcm" and target_lang == "en":
        result = MultilingualEngine.translate_pidgin_to_english(payload.text)
    elif source_lang == "en" and target_lang == "pcm":
        result = MultilingualEngine.translate_english_to_pidgin(payload.text)
    else:
        # Fallback identity
        result = TranslationResponse(
            original_text=payload.text,
            translated_text=payload.text,
            source_language=source_lang,
            target_language=target_lang,
            translation_label=f"Language pair {source_lang}->{target_lang} retains original text.",
            is_machine_translated=False,
        )

    return APIResponse(
        data=result,
        message="Translation completed successfully.",
    )
