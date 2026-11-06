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
    AlertRejectRequest,
    AlertApprovalRecordOut,
    NotificationDeliveryOut,
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


@router.post(
    "/{alert_id}/reject",
    response_model=APIResponse[AlertDetailOut],
    summary="Reject early warning alert draft (Lead Officers & Admins)",
)
def reject_alert(
    alert_id: str,
    payload: AlertRejectRequest,
    current_user: User = Depends(require_permission("alerts:approve")),
    db: Session = Depends(get_db),
) -> APIResponse[AlertDetailOut]:
    """Reject alert draft with institutional explanation."""
    alert = NotificationService.reject_alert(
        db=db, alert_id=alert_id, reason=payload.rejection_reason, officer_id=current_user.id
    )
    return APIResponse(
        data=AlertDetailOut.model_validate(alert),
        message=f"Alert '{alert.alert_reference}' has been rejected.",
    )


@router.post(
    "/{alert_id}/submit-for-approval",
    response_model=APIResponse[AlertDetailOut],
    summary="Submit draft alert for institutional signoff (Analysts & Officers)",
)
def submit_alert_for_approval(
    alert_id: str,
    current_user: User = Depends(require_permission("alerts:create")),
    db: Session = Depends(get_db),
) -> APIResponse[AlertDetailOut]:
    """Transition draft alert to PENDING_APPROVAL."""
    alert = NotificationService.submit_for_approval(
        db=db, alert_id=alert_id, officer_id=current_user.id
    )
    return APIResponse(
        data=AlertDetailOut.model_validate(alert),
        message=f"Alert '{alert.alert_reference}' submitted for approval.",
    )


@router.get(
    "/{alert_id}/approvals",
    response_model=APIResponse[List[AlertApprovalRecordOut]],
    summary="Inspect approval and rejection history for an alert",
)
def get_alert_approval_history(
    alert_id: str,
    current_user: User = Depends(require_permission("alerts:create")),
    db: Session = Depends(get_db),
) -> APIResponse[List[AlertApprovalRecordOut]]:
    """Retrieve complete audit history of alert lifecycle signoffs."""
    records = NotificationService.get_alert_approvals(db=db, alert_id=alert_id)
    return APIResponse(
        data=[AlertApprovalRecordOut.model_validate(r) for r in records],
        message="Alert approval records retrieved successfully.",
    )


@router.get(
    "/my-notifications",
    response_model=APIResponse[List[NotificationDeliveryOut]],
    summary="Retrieve citizen in-app notification alerts feed",
)
def get_my_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[List[NotificationDeliveryOut]]:
    """In-app notifications delivered to the logged in citizen."""
    skip = (page - 1) * page_size
    items = NotificationService.list_user_notifications(
        db=db, user_id=current_user.id, unread_only=unread_only, skip=skip, limit=page_size
    )
    return APIResponse(
        data=[NotificationDeliveryOut(**i) for i in items],
        message=f"Retrieved {len(items)} in-app notification(s).",
    )


@router.patch(
    "/notifications/{delivery_id}/read",
    response_model=APIResponse[dict],
    summary="Mark an in-app notification as read",
)
def mark_notification_as_read(
    delivery_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """Acknowledge read receipt of notification."""
    delivery = NotificationService.mark_notification_read(db=db, delivery_id=delivery_id, user_id=current_user.id)
    return APIResponse(
        data={"delivery_id": delivery.id, "read_at": delivery.read_at.isoformat() if delivery.read_at else None},
        message="Notification marked as read.",
    )


@router.get(
    "/notifications/unread-count",
    response_model=APIResponse[dict],
    summary="Get count of unread notifications",
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """Get count of unread notifications for badge indicator."""
    count = NotificationService.get_unread_notification_count(db=db, user_id=current_user.id)
    return APIResponse(
        data={"unread_count": count},
        message="Unread notification count retrieved.",
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
