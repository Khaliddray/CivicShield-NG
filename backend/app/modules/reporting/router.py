"""Citizen Reporting and Verification Queue Endpoints."""

import math
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Form, File, UploadFile, Request, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, get_optional_current_user, require_permission
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.common.schemas import APIResponse, PaginatedResponse, PaginationMeta
from backend.app.modules.auth.models import User
from backend.app.modules.reporting.schemas import (
    ReportCreateRequest,
    ReportPublicOut,
    ReportDetailOut,
)
from backend.app.modules.reporting.service import ReportingService

router = APIRouter(prefix="/reports", tags=["Citizen Reporting & Submissions"])


def _to_public_out(report) -> ReportPublicOut:
    """Helper to convert Report entity to ReportPublicOut."""
    return ReportPublicOut(
        id=report.id,
        reference_number=report.reference_number,
        title=report.title,
        status=report.status,
        priority=report.priority,
        nigerian_state=report.nigerian_state,
        encounter_location=report.encounter_location,
        incident_date=report.incident_date,
        created_at=report.created_at,
        updated_at=report.updated_at,
        evidence_count=len(report.evidence_items) if report.evidence_items else 0,
        claims_count=len(report.claims) if report.claims else 0,
    )


@router.post(
    "",
    response_model=APIResponse[ReportPublicOut],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a suspicious electoral announcement or media (Anonymous or Authenticated)",
)
@router.post(
    "/submit",
    response_model=APIResponse[ReportPublicOut],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def submit_report(
    request: Request,
    title: Optional[str] = Form(None),
    content_text: str = Form(..., min_length=10),
    source_platform: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    encounter_location: Optional[str] = Form(None),
    nigerian_state: Optional[str] = Form(None),
    incident_date: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[ReportPublicOut]:
    """Citizen submission endpoint accepting multipart claims and media uploads."""
    client_ip = request.client.host if request.client else None

    # Auto-generate title if omitted
    clean_title = title.strip() if title else (content_text[:60].strip() + ("..." if len(content_text) > 60 else ""))

    location = encounter_location or source_platform

    parsed_date = None
    if incident_date:
        try:
            parsed_date = datetime.fromisoformat(incident_date)
        except ValueError:
            raise ValidationException("Invalid incident_date format. Please provide a valid ISO-8601 timestamp.")

    report_create = ReportCreateRequest(
        title=clean_title,
        content_text=content_text,
        encounter_location=location,
        nigerian_state=nigerian_state,
        incident_date=parsed_date,
    )

    report = ReportingService.submit_report(
        db=db,
        report_data=report_create,
        files=files,
        user_id=current_user.id if current_user else None,
        client_ip=client_ip,
    )

    return APIResponse(
        data=_to_public_out(report),
        message=f"Report successfully registered with reference code {report.reference_number}. Save this code to track progress.",
    )


@router.get(
    "/track/{reference_number}",
    response_model=APIResponse[ReportPublicOut],
    summary="Track report verification progress using reference number",
)
def track_report(
    reference_number: str,
    db: Session = Depends(get_db),
) -> APIResponse[ReportPublicOut]:
    """Public lookup allowing citizens to monitor report verification status without an account."""
    report = ReportingService.get_by_reference(db=db, reference_number=reference_number)
    if not report:
        raise EntityNotFoundException("Report", reference_number)

    return APIResponse(
        data=_to_public_out(report),
        message="Report status retrieved successfully.",
    )


@router.get(
    "/my-reports",
    response_model=APIResponse[List[ReportPublicOut]],
    summary="Retrieve reports submitted by the authenticated citizen",
)
def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[List[ReportPublicOut]]:
    """List authenticated user's submitted reports."""
    reports = ReportingService.list_user_reports(db=db, user_id=current_user.id)
    return APIResponse(
        data=[_to_public_out(r) for r in reports],
        message="User reports retrieved successfully.",
    )


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[ReportDetailOut]],
    summary="List all reports for institutional review (Command Centre)",
)
def list_reports(
    nigerian_state: Optional[str] = Query(None, description="Filter by Nigerian State"),
    report_status: Optional[str] = Query(None, description="Filter by status (e.g. SUBMITTED, UNDER_REVIEW)"),
    priority: Optional[str] = Query(None, description="Filter by priority (e.g. HIGH, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search keyword in title or content"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("reports:view_all")),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[ReportDetailOut]]:
    """Command Centre query with pagination and filters."""
    skip = (page - 1) * page_size
    items, total = ReportingService.list_reports(
        db=db,
        nigerian_state=nigerian_state,
        report_status=report_status,
        priority=priority,
        search_query=search,
        skip=skip,
        limit=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return APIResponse(
        data=PaginatedResponse(
            items=[ReportDetailOut.model_validate(r) for r in items],
            pagination=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
        message="Reports retrieved successfully.",
    )


@router.get(
    "/{report_id}",
    response_model=APIResponse[ReportDetailOut],
    summary="Retrieve detailed report with evidence and claim analysis",
)
def get_report_detail(
    report_id: str,
    current_user: User = Depends(require_permission("reports:view_all")),
    db: Session = Depends(get_db),
) -> APIResponse[ReportDetailOut]:
    """Institutional review detailed inspection."""
    report = ReportingService.get_by_id(db=db, report_id=report_id)
    if not report:
        raise EntityNotFoundException("Report", report_id)

    return APIResponse(
        data=ReportDetailOut.model_validate(report),
        message="Report details retrieved successfully.",
    )
