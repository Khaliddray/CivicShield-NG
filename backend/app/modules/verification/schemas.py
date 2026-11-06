"""Pydantic schemas for Institutional Verification and Decision Recording."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.common.enums import VerificationDecision


class VerificationDecisionCreate(BaseModel):
    """Payload for recording an authoritative verification decision by an authorized officer."""

    claim_id: str = Field(description="UUID of the claim being verified")
    decision: VerificationDecision = Field(description="Formal verification state (e.g. VERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE)")
    justification_notes: str = Field(min_length=15, description="Institutional evidence justification and reasoning")
    public_clarification: str = Field(min_length=15, description="Clear, public-facing factual explanation for citizens")
    official_document_id: Optional[str] = Field(default=None, description="Optional UUID of referenced official document from registry")
    evidence_sources_consulted: Optional[List[str]] = Field(default_factory=list, description="List of source URLs or official gazette citations")


class VerificationRecordOut(BaseModel):
    """Recorded institutional verification finding."""

    id: str
    claim_id: str
    decision: str
    justification_notes: str
    public_clarification: str
    official_document_id: Optional[str] = None
    evidence_sources_consulted: Optional[list] = []
    verified_by_user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QueueItemOut(BaseModel):
    """Prioritized claim item in the Verification Officer queue."""

    claim_id: str
    report_id: str
    report_reference: str
    claim_text: str
    category: str
    ai_confidence_score: float
    ai_suggested_status: str
    ai_analysis_summary: Optional[str] = None
    report_priority: str
    nigerian_state: Optional[str] = None
    incident_date: Optional[datetime] = None
    created_at: datetime


class RecommendationCreateRequest(BaseModel):
    """Analyst verification recommendation submitted for reviewer approval."""

    claim_id: str = Field(description="UUID of the claim being evaluated")
    recommended_decision: VerificationDecision = Field(description="Analyst recommendation (VERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE)")
    justification_notes: str = Field(min_length=10, description="Findings and factual evidence references")
    proposed_clarification: str = Field(min_length=10, description="Proposed public clarification text")
    official_document_id: Optional[str] = Field(default=None, description="Optional official document reference")
    evidence_sources_consulted: Optional[List[str]] = Field(default_factory=list, description="Citations and consult references")


class RecommendationReviewRequest(BaseModel):
    """Reviewer decision approving or rejecting an analyst recommendation."""

    action: str = Field(description="Reviewer action: APPROVE or REJECT")
    reviewer_notes: Optional[str] = Field(default=None, description="Reviewer feedback or notes")
    adjusted_decision: Optional[VerificationDecision] = Field(default=None, description="Optional revised decision if adjusting recommendation")
    adjusted_clarification: Optional[str] = Field(default=None, description="Optional refined public clarification")


class RecommendationOut(BaseModel):
    """Analyst recommendation detail."""

    id: str
    claim_id: str
    analyst_id: str
    recommended_decision: str
    justification_notes: str
    proposed_clarification: str
    official_document_id: Optional[str] = None
    evidence_sources_consulted: Optional[list] = []
    status: str
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClaimDetailOut(BaseModel):
    """Detailed claim inspection including verification history."""

    id: str
    report_id: str
    claim_text: str
    category: str
    ai_confidence_score: float
    ai_analysis_summary: Optional[str] = None
    ai_suggested_status: str
    requires_human_review: bool
    created_at: datetime
    verifications: List[VerificationRecordOut] = []
    recommendations: List[RecommendationOut] = []

    model_config = {"from_attributes": True}
