"""Pydantic schemas for Early Warning and Notification Management."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from backend.app.common.enums import AlertSeverity, AlertCategory, AlertScope, AlertStatus
from backend.app.common.geo import validate_nigerian_state


class AlertCreateRequest(BaseModel):
    """Payload to draft a new early warning alert."""

    title: str = Field(min_length=5, max_length=255, description="Clear, alarming-free headline")
    summary: str = Field(min_length=15, description="Executive summary of the alert")
    full_clarification: str = Field(min_length=25, description="Full factual clarification with citations")
    severity: AlertSeverity = Field(default=AlertSeverity.HIGH)
    category: AlertCategory = Field(default=AlertCategory.CONFIRMED_MISINFORMATION)
    target_scope: AlertScope = Field(default=AlertScope.NATIONAL)
    target_states: Optional[List[str]] = Field(default_factory=list, description="Targeted Nigerian states if scope is STATE_SPECIFIC")
    verification_record_id: Optional[str] = Field(default=None, description="UUID of linked verification record proving the finding")
    expires_at: Optional[datetime] = None

    @field_validator("target_states")
    @classmethod
    def validate_states(cls, states: Optional[List[str]]) -> List[str]:
        if not states:
            return []
        cleaned = []
        for s in states:
            if not validate_nigerian_state(s):
                raise ValueError(f"'{s}' is not a recognized Nigerian state.")
            cleaned.append(s.title())
        return cleaned


class AlertWithdrawRequest(BaseModel):
    """Payload to withdraw or supersede an active alert."""

    withdrawal_reason: str = Field(min_length=10, description="Mandatory official justification for alert withdrawal or clarification update")


class AlertPublicOut(BaseModel):
    """Public early warning advisory."""

    id: str
    alert_reference: str
    title: str
    summary: str
    full_clarification: str
    severity: str
    category: str
    target_scope: str
    target_states: Optional[list] = []
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertDetailOut(AlertPublicOut):
    """Detailed administrative view of an alert."""

    created_by_user_id: str
    approved_by_user_id: Optional[str] = None
    verification_record_id: Optional[str] = None
    deliveries_count: int = 0


class PreferenceUpdateRequest(BaseModel):
    """Payload to update citizen notification preferences."""

    preferred_states: Optional[List[str]] = None
    receive_critical_alerts: Optional[bool] = None
    receive_high_alerts: Optional[bool] = None
    receive_medium_alerts: Optional[bool] = None
    receive_informational: Optional[bool] = None
    channel_in_app: Optional[bool] = None
    channel_push: Optional[bool] = None
    channel_email: Optional[bool] = None

    @field_validator("preferred_states")
    @classmethod
    def validate_pref_states(cls, states: Optional[List[str]]) -> Optional[List[str]]:
        if states is None:
            return None
        cleaned = []
        for s in states:
            if not validate_nigerian_state(s):
                raise ValueError(f"'{s}' is not a recognized Nigerian state.")
            cleaned.append(s.title())
        return cleaned


class PreferenceOut(BaseModel):
    """Active citizen notification preferences."""

    preferred_states: list = []
    receive_critical_alerts: bool
    receive_high_alerts: bool
    receive_medium_alerts: bool
    receive_informational: bool
    channel_in_app: bool
    channel_push: bool
    channel_email: bool

    model_config = {"from_attributes": True}


class AlertRejectRequest(BaseModel):
    """Payload to reject an early warning draft."""

    rejection_reason: str = Field(min_length=10, description="Mandatory official justification for rejecting draft advisory")


class AlertApprovalRecordOut(BaseModel):
    """Historical audit entry for alert approval or rejection."""

    id: str
    alert_id: str
    action: str
    officer_user_id: str
    comments: Optional[str] = None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class NotificationDeliveryOut(BaseModel):
    """In-app citizen notification delivery item."""

    id: str
    alert_id: str
    channel: str
    delivery_status: str
    delivered_at: datetime
    read_at: Optional[datetime] = None
    alert_title: Optional[str] = None
    alert_summary: Optional[str] = None
    alert_severity: Optional[str] = None

    model_config = {"from_attributes": True}
