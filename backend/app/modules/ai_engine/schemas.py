"""Pydantic schemas for AI Misinformation Intelligence Analysis."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Official Source & Evidence Schemas
# ---------------------------------------------------------

class OfficialSourceMatchOut(BaseModel):
    """Matching certified official announcement reference."""

    document_code: Optional[str] = None
    title: Optional[str] = None
    issuing_institution: Optional[str] = None
    similarity_score: float
    source_url: Optional[str] = None
    publication_date: Optional[str] = None


class EvidenceItemOut(BaseModel):
    """Structured evidence item extracted from official registry or trusted sources."""

    description: str
    source_name: str
    source_url: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_role: str = "CONTEXTUAL"  # SUPPORTING, CONTRADICTORY, CONTEXTUAL
    similarity_score: float = 0.0


# ---------------------------------------------------------
# Claim Extraction Schemas (Section 3)
# ---------------------------------------------------------

class ExtractedClaimItem(BaseModel):
    """Discrete factual claim extracted from citizen submission."""

    claim_text: str
    entities: List[str] = Field(default_factory=list, description="Extracted entities such as INEC, places, dates")
    claim_type: str = Field(default="GENERAL_CIVIC_CLAIM", description="Type of claim (e.g. ELECTION_DATE_OR_POSTPONEMENT)")
    is_opinion: bool = Field(default=False, description="Whether statement is opinion rather than factual")
    requires_verification: bool = Field(default=True, description="True for factual claims requiring verification")
    confidence: float = Field(default=0.85, description="Confidence in claim isolation")


class ClaimExtractionRequest(BaseModel):
    """Request payload for extracting factual claims from text."""

    text: str = Field(min_length=3, max_length=10000, description="Submitted electoral text or report narrative")
    context_state: Optional[str] = Field(default=None, description="Optional Nigerian state context")


class ClaimExtractionResponse(BaseModel):
    """Structured claim extraction output preserving original content."""

    original_text: str
    detected_language: str = "en"
    is_translated: bool = False
    claims: List[ExtractedClaimItem] = Field(default_factory=list)


# ---------------------------------------------------------
# Legacy / Existing Claim Analysis Contract (Section 6)
# ---------------------------------------------------------

class ClaimAnalysisRequest(BaseModel):
    """On-demand claim analysis request payload."""

    claim_text: str = Field(min_length=3, description="Electoral statement or submitted narrative to analyze")
    context_state: Optional[str] = Field(default=None, description="Optional relevant Nigerian State context")


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

    # Standard AI Contract fields
    claim: Optional[str] = None
    classification: Optional[str] = None
    confidence: Optional[float] = None
    evidence: List[Union[str, EvidenceItemOut]] = []
    sources: List[str] = []
    limitations: List[str] = []
    service_available: bool = True
    error_message: Optional[str] = None


class StructuredAIAssessment(BaseModel):
    """Standard contract between Member 1 Backend and Member 2 AI Service (Section 6)."""

    claim: str
    classification: str = "INSUFFICIENT_EVIDENCE"
    confidence: float = 0.0
    evidence: List[EvidenceItemOut] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    requires_human_review: bool = True
    service_available: bool = True
    reasoning: Optional[str] = None


# ---------------------------------------------------------
# Similarity Detection Schemas (Section 7)
# ---------------------------------------------------------

class SimilarReportMatch(BaseModel):
    """Candidate matching report with algorithmically derived similarity score."""

    report_id: str
    similarity_score: float
    matching_reason: str = "Semantic text overlap"


class SimilarityDetectionRequest(BaseModel):
    """Request payload for comparing a report or text against candidate reports."""

    report_id: Optional[str] = None
    target_text: str = Field(min_length=3, description="Target statement or report text")
    candidate_reports: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of candidate reports with 'id' and 'text'",
    )
    threshold: float = Field(default=0.70, ge=0.0, le=1.0, description="Similarity cutoff threshold")


class SimilarityDetectionResponse(BaseModel):
    """Structured similarity detection output."""

    report_id: Optional[str] = None
    similar_reports: List[SimilarReportMatch] = Field(default_factory=list)
    requires_cluster_review: bool = False
    top_similarity_score: float = 0.0
    safeguard_notice: str = (
        "Semantic similarity reflects narrative recurrence and does not prove common authorship "
        "or coordinated disinformation."
    )


# ---------------------------------------------------------
# Multilingual Processing Schemas (Section 9)
# ---------------------------------------------------------

class LanguageDetectionRequest(BaseModel):
    """Request to detect language of electoral submission."""

    text: str = Field(min_length=2, max_length=10000)


class LanguageDetectionResponse(BaseModel):
    """Language detection output."""

    text: str
    detected_language: str  # en, pcm, ha, yo, ig, unknown
    language_name: str
    confidence: float
    is_supported: bool
    message: str


class TranslationRequest(BaseModel):
    """Request to translate text between supported Nigerian languages."""

    text: str = Field(min_length=2, max_length=10000)
    source_language: Optional[str] = "pcm"
    target_language: str = "en"


class TranslationResponse(BaseModel):
    """Machine translation response with required transparent labeling."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    translation_label: str
    is_machine_translated: bool = True


# ---------------------------------------------------------
# Narrative Threat Intelligence Schemas (Section 8)
# ---------------------------------------------------------

class NarrativePulseClusterSummary(BaseModel):
    """Threat intelligence cluster summary for analyst review."""

    cluster_id: str
    title: str
    summary: str
    report_count: int
    first_reported_at: Optional[str] = None
    last_reported_at: Optional[str] = None
    entities: List[str] = Field(default_factory=list)
    requires_human_review: bool = True
    ai_disclaimer: str = (
        "AI-Generated Threat Intelligence Assessment — Pending human analyst review. "
        "Volume does not establish factual accuracy; similarity does not prove coordinated behavior."
    )
