"""Pydantic schemas for AI Misinformation Intelligence Analysis."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ClaimAnalysisRequest(BaseModel):
    """On-demand claim analysis request payload."""

    claim_text: str = Field(min_length=5, description="Electoral statement or submitted narrative to analyze")
    context_state: Optional[str] = Field(default=None, description="Optional relevant Nigerian State context")


class OfficialSourceMatchOut(BaseModel):
    """Matching certified official announcement reference."""

    document_code: Optional[str] = None
    title: Optional[str] = None
    issuing_institution: Optional[str] = None
    similarity_score: float


class ClaimAnalysisResponse(BaseModel):
    """Structured, evidence-backed AI analytical assessment."""

    extracted_claim: str
    category: str
    category_confidence: float
    ai_confidence_score: float
    ai_suggested_status: str
    analysis_summary: str
    contradiction_suspected: bool
    sources_consulted: List[OfficialSourceMatchOut] = []
    recommended_next_action: str
    requires_human_review: bool = True
    adversarial_injection_detected: bool = False
