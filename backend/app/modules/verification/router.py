"""Institutional Verification Centre API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission, get_current_user
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.verification.schemas import (
    VerificationDecisionCreate,
    VerificationRecordOut,
    QueueItemOut,
    ClaimDetailOut,
)
from backend.app.modules.verification.service import VerificationService

router = APIRouter(prefix="/verification", tags=["Institutional Response & Verification"])


@router.get(
    "/queue",
    response_model=APIResponse[List[QueueItemOut]],
    summary="Retrieve prioritized verification review queue (Officers & Analysts)",
)
def get_verification_queue(
    nigerian_state: Optional[str] = Query(None, description="Filter by Nigerian State"),
    category: Optional[str] = Query(None, description="Filter by claim category"),
    priority: Optional[str] = Query(None, description="Filter by priority (e.g. HIGH, CRITICAL)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("claims:verify")),
    db: Session = Depends(get_db),
) -> APIResponse[List[QueueItemOut]]:
    """Command Centre queue prioritizing urgent claims, high-confidence AI contradictions, and critical states."""
    skip = (page - 1) * page_size
    items = VerificationService.get_queue(
        db=db,
        nigerian_state=nigerian_state,
        category=category,
        priority=priority,
        skip=skip,
        limit=page_size,
    )
    return APIResponse(
        data=items,
        message=f"Retrieved {len(items)} claim(s) pending institutional verification.",
    )


@router.post(
    "/decisions",
    response_model=APIResponse[VerificationRecordOut],
    status_code=status.HTTP_201_CREATED,
    summary="Record an authoritative human verification decision (Verification Officers)",
)
def submit_verification_decision(
    payload: VerificationDecisionCreate,
    current_user: User = Depends(require_permission("claims:verify")),
    db: Session = Depends(get_db),
) -> APIResponse[VerificationRecordOut]:
    """Record evidence-backed decision (VERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE) and update report lifecycle."""
    record = VerificationService.record_decision(
        db=db,
        payload=payload,
        officer_user_id=current_user.id,
    )
    return APIResponse(
        data=VerificationRecordOut.model_validate(record),
        message=f"Authoritative decision '{record.decision}' recorded successfully.",
    )


@router.get(
    "/decisions/{record_id}",
    response_model=APIResponse[VerificationRecordOut],
    summary="Inspect verification decision and supporting citations",
)
def get_decision(
    record_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[VerificationRecordOut]:
    """Retrieve full verification finding and evidence justifications."""
    record = VerificationService.get_verification_record(db=db, record_id=record_id)
    if not record:
        raise EntityNotFoundException("VerificationRecord", record_id)

    return APIResponse(
        data=VerificationRecordOut.model_validate(record),
        message="Verification decision retrieved successfully.",
    )


@router.get(
    "/claims/{claim_id}",
    response_model=APIResponse[ClaimDetailOut],
    summary="Inspect claim details and verification history",
)
def get_claim_detail(
    claim_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[ClaimDetailOut]:
    """Inspect claim lifecycle and all recorded verification decisions."""
    claim = VerificationService.get_claim(db=db, claim_id=claim_id)
    if not claim:
        raise EntityNotFoundException("Claim", claim_id)

    return APIResponse(
        data=ClaimDetailOut.model_validate(claim),
        message="Claim details retrieved successfully.",
    )
