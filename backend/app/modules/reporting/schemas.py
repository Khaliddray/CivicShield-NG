"""Pydantic schemas for Citizen Reporting and Evidence."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from backend.app.common.geo import validate_nigerian_state
from backend.app.common.enums import ReportStatus, PriorityLevel, MediaType


class ReportCreateRequest(BaseModel):
    """Payload for submitting a suspicious electoral announcement or report."""

    title: str = Field(min_length=5, max_length=255, description="Brief summary of suspicious announcement")
    content_text: str = Field(min_length=10, description="Full text or transcript of the suspicious information")
    encounter_location: Optional[str] = Field(default=None, max_length=255, description="Platform or location where encountered (e.g. WhatsApp, X, Polling Unit)")
    nigerian_state: Optional[str] = Field(default=None, description="Relevant Nigerian State or FCT")
    incident_date: Optional[datetime] = None

    @field_validator("nigerian_state")
    @classmethod
    def check_valid_state(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_nigerian_state(v):
            raise ValueError(f"'{v}' is not a recognized Nigerian State or Federal Capital Territory.")
        return v.title() if v else None


class EvidenceOut(BaseModel):
    """Evidence file attachment metadata."""

    id: str
    file_name: str
    original_file_name: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    extracted_text: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimSummaryOut(BaseModel):
    """Summary of AI-extracted claim linked to report."""

    id: str
    claim_text: str
    category: str
    ai_confidence_score: float
    ai_suggested_status: str
    requires_human_review: bool

    model_config = {"from_attributes": True}


class StatusHistoryOut(BaseModel):
    """Status transition log item."""

    previous_status: str
    new_status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportPublicOut(BaseModel):
    """Publicly trackable report response."""

    id: Optional[str] = None
    reference_number: str
    title: str
    status: str
    priority: str
    nigerian_state: Optional[str] = None
    encounter_location: Optional[str] = None
    incident_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0
    claims_count: int = 0

    model_config = {"from_attributes": True}


class ReportDetailOut(BaseModel):
    """Comprehensive institutional report view for Analysts and Verification Officers."""

    id: str
    reference_number: str
    title: str
    content_text: str
    encounter_location: Optional[str] = None
    nigerian_state: Optional[str] = None
    incident_date: Optional[datetime] = None
    status: str
    priority: str
    assigned_analyst_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    evidence_items: List[EvidenceOut] = []
    claims: List[ClaimSummaryOut] = []
    status_history: List[StatusHistoryOut] = []

    model_config = {"from_attributes": True}


class ReportStatusUpdateRequest(BaseModel):
    """Payload for updating report lifecycle status."""

    status: str = Field(description="New status: UNVERIFIED, UNDER_REVIEW, VERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE, WITHDRAWN, RESOLVED, DISMISSED")
    notes: Optional[str] = Field(default=None, description="Analyst or officer notes justifying the status change")


class ReportAssignRequest(BaseModel):
    """Payload for assigning an analyst to a report."""

    analyst_user_id: str = Field(description="UUID of analyst user to assign")
    notes: Optional[str] = Field(default=None, description="Assignment guidance or notes")


class ReportWithdrawRequest(BaseModel):
    """Payload for withdrawing a report."""

    reason: str = Field(min_length=5, description="Reason for withdrawing the report")
