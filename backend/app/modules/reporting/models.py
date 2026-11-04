"""Citizen Reporting and Uploaded Evidence ORM Models."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin, UUIDMixin
from backend.app.common.enums import ReportStatus, PriorityLevel, MediaType


class Report(Base, UUIDMixin, TimestampMixin):
    """Citizen-submitted electoral report."""

    __tablename__ = "reports"

    reference_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    encounter_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., "WhatsApp", "X", "Radio"
    nigerian_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    incident_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default=ReportStatus.SUBMITTED.value, index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default=PriorityLevel.MEDIUM.value, nullable=False)
    submitter_ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    submitter: Mapped[Optional["User"]] = relationship("User", back_populates="reports")
    evidence_items: Mapped[List["UploadedEvidence"]] = relationship("UploadedEvidence", back_populates="report", cascade="all, delete-orphan", lazy="selectin")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="report", cascade="all, delete-orphan", lazy="selectin")
    status_history: Mapped[List["ReportStatusHistory"]] = relationship("ReportStatusHistory", back_populates="report", cascade="all, delete-orphan")


class UploadedEvidence(Base, UUIDMixin, TimestampMixin):
    """Untrusted file attachment uploaded as evidence for a report."""

    __tablename__ = "uploaded_evidence"

    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Sanitized random storage filename
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), default=MediaType.DOCUMENT.value, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)

    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    perceptual_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # OCR / Transcript

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="evidence_items")


class ReportStatusHistory(Base, UUIDMixin, TimestampMixin):
    """Audit log of status transitions for a citizen report."""

    __tablename__ = "report_status_history"

    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=False)
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="status_history")
