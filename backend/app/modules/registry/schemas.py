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
