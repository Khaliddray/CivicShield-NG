"""Official Information Verification Registry ORM Models."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin, UUIDMixin


class TrustedSource(Base, UUIDMixin, TimestampMixin):
    """Certified public authority, electoral commission, or verified civic institution."""

    __tablename__ = "trusted_sources"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="ELECTORAL_COMMISSION", index=True, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="VERIFIED", index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    registered_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    documents: Mapped[List["OfficialDocument"]] = relationship("OfficialDocument", back_populates="trusted_source")


class OfficialDocument(Base, UUIDMixin, TimestampMixin):
    """Authenticated repository of official electoral announcements and press releases."""

    __tablename__ = "official_documents"

    document_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    issuing_institution: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    sha256_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    digital_signature_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publication_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    is_authenticated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    authorized_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    trusted_source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("trusted_sources.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    trusted_source: Mapped[Optional["TrustedSource"]] = relationship("TrustedSource", back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", lazy="selectin")
    verification_records: Mapped[List["VerificationRecord"]] = relationship("VerificationRecord", back_populates="official_document")


class DocumentVersion(Base, UUIDMixin, TimestampMixin):
    """Historical audit version of an official document."""

    __tablename__ = "document_versions"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("official_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    document: Mapped["OfficialDocument"] = relationship("OfficialDocument", back_populates="versions")
