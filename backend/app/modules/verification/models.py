"""Human Verification and Evidence Review ORM Models."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin, UUIDMixin
from backend.app.common.enums import VerificationDecision, ClaimCategory, PriorityLevel


class Claim(Base, UUIDMixin, TimestampMixin):
    """Isolated factual statement extracted from report content for analysis."""

    __tablename__ = "claims"

    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default=ClaimCategory.GENERAL_ELECTORAL.value, index=True, nullable=False)

    ai_confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ai_analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_suggested_status: Mapped[str] = mapped_column(String(32), default=VerificationDecision.UNVERIFIED.value, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="claims")
    verifications: Mapped[List["VerificationRecord"]] = relationship("VerificationRecord", back_populates="claim", cascade="all, delete-orphan", lazy="selectin")
    recommendations: Mapped[List["VerificationRecommendation"]] = relationship("VerificationRecommendation", back_populates="claim", cascade="all, delete-orphan", lazy="selectin")


class VerificationRecommendation(Base, UUIDMixin, TimestampMixin):
    """Analyst recommendation submitted for reviewer approval."""

    __tablename__ = "verification_recommendations"

    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), index=True, nullable=False)
    analyst_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)

    recommended_decision: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # VERIFIED, CONTRADICTED, INSUFFICIENT_EVIDENCE
    justification_notes: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_clarification: Mapped[str] = mapped_column(Text, nullable=False)
    official_document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("official_documents.id", ondelete="SET NULL"), nullable=True)
    evidence_sources_consulted: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW", index=True, nullable=False)  # PENDING_REVIEW, APPROVED, REJECTED
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="recommendations")
    analyst: Mapped["User"] = relationship("User", foreign_keys=[analyst_id])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_id])
    official_document: Mapped[Optional["OfficialDocument"]] = relationship("OfficialDocument")


class VerificationRecord(Base, UUIDMixin, TimestampMixin):
    """Institutional evidence-backed verification decision recorded by a Verification Officer."""

    __tablename__ = "verification_records"

    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), index=True, nullable=False)
    verified_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)

    decision: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    official_document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("official_documents.id", ondelete="SET NULL"), nullable=True)

    justification_notes: Mapped[str] = mapped_column(Text, nullable=False)
    public_clarification: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_sources_consulted: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="verifications")
    verified_by_user: Mapped["User"] = relationship("User", back_populates="verifications")
    official_document: Mapped[Optional["OfficialDocument"]] = relationship("OfficialDocument", back_populates="verification_records")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="verification_record")


class Investigation(Base, UUIDMixin, TimestampMixin):
    """Deep-dive investigation tracking umbrella for high-threat electoral narratives."""

    __tablename__ = "investigations"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    lead_analyst_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default=PriorityLevel.MEDIUM.value, nullable=False)
    findings_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
