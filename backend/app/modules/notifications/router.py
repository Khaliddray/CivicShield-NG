"""Early Warning and Notification API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, require_permission
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.notifications.schemas import (
    AlertCreateRequest,
    AlertWithdrawRequest,
    AlertPublicOut,
    AlertDetailOut,
    PreferenceUpdateRequest,
    PreferenceOut,
)
from backend.app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/alerts", tags=["Early Warning & Notifications"])


@router.get(
    "/active",
    response_model=APIResponse[List[AlertPublicOut]],
    summary="Retrieve active, human-verified early warning advisories (Public)",
)
def get_active_alerts(
    state: Optional[str] = Query(None, description="Filter by Nigerian state of interest"),
    severity: Optional[str] = Query(None, description="Filter by severity level (e.g. CRITICAL, HIGH)"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[List[AlertPublicOut]]:
    """Public feed presenting verified early warnings, official clarifications, and security advisories."""
    alerts = NotificationService.get_active_alerts(db=db, nigerian_state=state, severity=severity, limit=limit)
    return APIResponse(
        data=[AlertPublicOut.model_validate(a) for a in alerts],
        message="Active early warning alerts retrieved successfully.",
    )


@router.post(
    "",
    response_model=APIResponse[AlertDetailOut],
    status_code=status.HTTP_201_CREATED,
    summary="Draft a new early warning alert (Analysts & Officers)",
)
def draft_alert(
    payload: AlertCreateRequest,
    current_user: User = Depends(require_permission("alerts:create")),
    db: Session = Depends(get_db),
) -> APIResponse[AlertDetailOut]:
    """Draft early warning alert adhering to safety invariants and verification linking."""
    alert = NotificationService.create_alert_draft(db=db, request=payload, author_id=current_user.id)
    return APIResponse(
        data=AlertDetailOut.model_validate(alert),
        message=f"Alert '{alert.alert_reference}' drafted successfully. Pending administrative sign-off.",
    )


@router.post(
    "/{alert_id}/approve",
    response_model=APIResponse[AlertDetailOut],
    summary="Approve and broadcast alert (Lead Officers & Admins)",
)
def approve_alert(
    alert_id: str,
    current_user: User = Depends(require_permission("alerts:approve")),
    db: Session = Depends(get_db),
) -> APIResponse[AlertDetailOut]:
    """Dual-key sign-off triggering multi-channel alert distribution."""
    alert = NotificationService.approve_and_broadcast(db=db, alert_id=alert_id, approver_id=current_user.id)
    return APIResponse(
        data=AlertDetailOut.model_validate(alert),
        message=f"Alert '{alert.alert_reference}' approved and broadcast successfully.",
    )


@router.post(
    "/{alert_id}/withdraw",
    response_model=APIResponse[AlertDetailOut],
    summary="Withdraw or issue clarification for an alert (Officers & Admins)",
)
def withdraw_alert(
    alert_id: str,
    payload: AlertWithdrawRequest,
    current_user: User = Depends(require_permission("alerts:withdraw")),
    db: Session = Depends(get_db),
) -> APIResponse[AlertDetailOut]:
    """Withdraw or supersede an active alert with justification."""
    alert = NotificationService.withdraw_alert(
        db=db, alert_id=alert_id, reason=payload.withdrawal_reason, officer_id=current_user.id
    )
    return APIResponse(
        data=AlertDetailOut.model_validate(alert),
        message=f"Alert '{alert.alert_reference}' officially withdrawn.",
    )


@router.get(
    "/preferences",
    response_model=APIResponse[PreferenceOut],
    summary="Get citizen alert preferences and state filters",
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[PreferenceOut]:
    """Retrieve authenticated citizen's notification preferences."""
    pref = NotificationService.get_or_create_preferences(db=db, user_id=current_user.id)
    return APIResponse(
        data=PreferenceOut.model_validate(pref),
        message="Notification preferences retrieved successfully.",
    )


@router.put(
    "/preferences",
    response_model=APIResponse[PreferenceOut],
    summary="Update citizen alert preferences and state filters",
)
def update_preferences(
    updates: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[PreferenceOut]:
    """Configure localized state alert preferences and severity thresholds."""
    pref = NotificationService.update_preferences(db=db, user_id=current_user.id, updates=updates)
    return APIResponse(
        data=PreferenceOut.model_validate(pref),
        message="Notification preferences updated successfully.",
    )
