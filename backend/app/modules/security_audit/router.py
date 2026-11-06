"""Database Security and Tamper-Evident Audit API Endpoints."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.common.schemas import APIResponse, PaginatedResponse, PaginationMeta
from backend.app.modules.auth.models import User
from backend.app.modules.security_audit.schemas import (
    AuditLogOut,
    AuditLedgerVerificationResult,
    SecurityEventOut,
    SecurityEventResolveRequest,
    SecurityMetricsOut,
)
from backend.app.modules.security_audit.service import SecurityAuditService

router = APIRouter(prefix="/security", tags=["Database Security & Tamper-Evident Auditing"])


@router.get(
    "/audit-logs",
    response_model=APIResponse[PaginatedResponse[AuditLogOut]],
    summary="Query tamper-evident audit logs (Security Officers & Admins)",
)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action (e.g. USER_LOGIN, CLAIM_VERIFIED)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g. USER, REPORT, CLAIM)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[AuditLogOut]]:
    """Inspect immutable audit ledger capturing every consequential platform action."""
    skip = (page - 1) * page_size
    items, total = SecurityAuditService.list_audit_logs(
        db=db, action=action, entity_type=entity_type, skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return APIResponse(
        data=PaginatedResponse(
            items=[AuditLogOut.model_validate(log) for log in items],
            pagination=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
        message="Audit logs retrieved successfully.",
    )


@router.post(
    "/audit-logs/verify-ledger",
    response_model=APIResponse[AuditLedgerVerificationResult],
    summary="Cryptographically verify audit ledger hash chain integrity",
)
@router.post(
    "/verify-ledger",
    response_model=APIResponse[AuditLedgerVerificationResult],
    summary="Cryptographically verify audit ledger hash chain integrity (Alias)",
    include_in_schema=False,
)
def verify_audit_ledger(
    limit: int = Query(10000, ge=10, le=50000),
    current_user: User = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
) -> APIResponse[AuditLedgerVerificationResult]:
    """Execute cryptographic proof validating that no audit record has been altered or deleted."""
    result = SecurityAuditService.verify_ledger_integrity(db=db, limit=limit)
    return APIResponse(
        data=result,
        message="Audit ledger cryptographic chain verification completed.",
    )


@router.get(
    "/events",
    response_model=APIResponse[PaginatedResponse[SecurityEventOut]],
    summary="Inspect security monitoring incidents and brute-force flags",
)
def list_security_events(
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("security:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[SecurityEventOut]]:
    """Command Centre security incident monitor."""
    skip = (page - 1) * page_size
    items, total = SecurityAuditService.list_security_events(
        db=db, resolved=resolved, event_type=event_type, skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return APIResponse(
        data=PaginatedResponse(
            items=[SecurityEventOut.model_validate(e) for e in items],
            pagination=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
        message="Security events retrieved successfully.",
    )


@router.post(
    "/events/{event_id}/resolve",
    response_model=APIResponse[SecurityEventOut],
    summary="Resolve a security incident with investigation notes",
)
def resolve_security_event(
    event_id: str,
    payload: SecurityEventResolveRequest,
    current_user: User = Depends(require_permission("security:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[SecurityEventOut]:
    """Mark security threat resolved."""
    event = SecurityAuditService.resolve_event(
        db=db, event_id=event_id, resolution_notes=payload.resolution_notes, officer_user_id=current_user.id
    )
    return APIResponse(
        data=SecurityEventOut.model_validate(event),
        message="Security incident resolved successfully.",
    )


@router.get(
    "/metrics",
    response_model=APIResponse[SecurityMetricsOut],
    summary="Retrieve platform security overview metrics and ledger status",
)
def get_security_metrics(
    current_user: User = Depends(require_permission("security:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[SecurityMetricsOut]:
    """Dashboard KPIs summarizing threat velocity, account lockouts, and ledger integrity."""
    metrics = SecurityAuditService.get_metrics(db=db)
    return APIResponse(
        data=metrics,
        message="Security metrics retrieved successfully.",
    )
