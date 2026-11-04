"""AI Misinformation Intelligence API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.ai_engine.schemas import ClaimAnalysisRequest, ClaimAnalysisResponse
from backend.app.modules.reporting.schemas import ClaimSummaryOut
from backend.app.modules.ai_engine.service import AIEngineService

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
