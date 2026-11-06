"""Pydantic schemas for Official Information Verification Registry."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentCreateRequest(BaseModel):
    """Institutional request to publish and certify an official electoral document."""

    document_code: str = Field(min_length=3, max_length=64, description="Unique institutional document reference code (e.g. INEC-PUB-2027-001)")
    issuing_institution: str = Field(min_length=2, max_length=128, description="Official issuing authority (e.g. Independent National Electoral Commission)")
    title: str = Field(min_length=5, max_length=255, description="Official document title")
    summary: str = Field(min_length=10, description="Brief summary of official announcement")
    content_text: str = Field(min_length=20, description="Full canonical text of the announcement")
    digital_signature_info: Optional[str] = Field(default=None, description="Cryptographic signature metadata if present")
    source_url: Optional[str] = Field(default=None, description="Official institutional gazette or press portal URL")
    trusted_source_id: Optional[str] = Field(default=None, description="Foreign key linking to certified trusted source")


class TrustedSourceCreateRequest(BaseModel):
    """Payload to register a certified trusted public authority."""

    name: str = Field(min_length=2, max_length=255, description="Authority name (e.g. Independent National Electoral Commission)")
    url: str = Field(min_length=5, max_length=512, description="Official domain URL")
    category: str = Field(default="ELECTORAL_COMMISSION", description="Category: ELECTORAL_COMMISSION, LAW_ENFORCEMENT, JUDICIARY, FACT_CHECKER, GOVERNMENT")
    verification_status: str = Field(default="VERIFIED", description="Status: VERIFIED, PENDING, SUSPENDED, REVOKED")
    description: Optional[str] = Field(default=None, description="Description of mandate or operational scope")


class TrustedSourceUpdateRequest(BaseModel):
    """Payload to update trusted source details."""

    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    verification_status: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TrustedSourceOut(BaseModel):
    """Publicly inspectable trusted source record."""

    id: str
    name: str
    url: str
    category: str
    verification_status: str
    description: Optional[str] = None
    is_active: bool
    last_retrieved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    documents_count: int = 0

    model_config = {"from_attributes": True}


class DocumentVersionOut(BaseModel):
    """Historical version entry for an official document."""

    version_number: int
    sha256_hash: str
    change_summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OfficialDocumentOut(BaseModel):
    """Publicly inspectable official document record."""

    id: str
    document_code: str
    issuing_institution: str
    title: str
    summary: str
    content_text: str
    current_version: int
    sha256_hash: str
    digital_signature_info: Optional[str] = None
    publication_date: datetime
    source_url: Optional[str] = None
    trusted_source_id: Optional[str] = None
    is_authenticated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OfficialDocumentDetailOut(OfficialDocumentOut):
    """Detailed official document record including full version history."""

    versions: List[DocumentVersionOut] = []


class HashVerificationRequest(BaseModel):
    """Request to verify the authenticity and integrity of a document or text claim."""

    sha256_hash: Optional[str] = Field(default=None, min_length=64, max_length=64, description="SHA-256 hash of suspect document")
    content_text: Optional[str] = Field(default=None, description="Raw suspect text to compute hash and compare against official records")


class HashVerificationResponse(BaseModel):
    """Integrity verification result."""

    is_official_match: bool
    matched_document_code: Optional[str] = None
    issuing_institution: Optional[str] = None
    document_title: Optional[str] = None
    canonical_hash: Optional[str] = None
    submitted_hash: str
    verification_status: str  # EXACT_MATCH, TAMPERED_SUSPECTED, UNREGISTERED
    analytical_note: str
