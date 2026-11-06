"""Coordinated Narrative Detection and Threat Intelligence ORM Models."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin, UUIDMixin


class NarrativeCluster(Base, UUIDMixin, TimestampMixin):
    """Clustered grouping of reports and public signals exhibiting coordinated or rapid amplification."""

    __tablename__ = "narrative_clusters"

    cluster_title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    velocity_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # Reports per hour / rate of surge
    amplification_pattern: Mapped[str] = mapped_column(String(64), default="ORGANIC_SPREAD", nullable=False)
    geographic_scope: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)  # List of Nigerian states

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED", index=True, nullable=False)
    first_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_analyst_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    assigned_analyst: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_analyst_id])
    cluster_reports: Mapped[List["NarrativeClusterReport"]] = relationship("NarrativeClusterReport", back_populates="cluster", cascade="all, delete-orphan", lazy="selectin")
    threat_indicators: Mapped[List["ThreatIndicator"]] = relationship("ThreatIndicator", back_populates="cluster", cascade="all, delete-orphan", lazy="selectin")


class NarrativeClusterReport(Base, UUIDMixin, TimestampMixin):
    """Association linking a citizen report to an identified narrative cluster."""

    __tablename__ = "narrative_cluster_reports"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("narrative_clusters.id", ondelete="CASCADE"), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    cluster: Mapped["NarrativeCluster"] = relationship("NarrativeCluster", back_populates="cluster_reports")


class ThreatIndicator(Base, UUIDMixin, TimestampMixin):
    """Specific technical pattern indicator identified within a narrative (e.g. keyword burst, duplicate media)."""

    __tablename__ = "threat_indicators"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("narrative_clusters.id", ondelete="CASCADE"), index=True, nullable=False)
    indicator_type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., SYNCHRONIZED_POSTING, SYNTHETIC_MEDIA
    evidence_detail: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    # Relationships
    cluster: Mapped["NarrativeCluster"] = relationship("NarrativeCluster", back_populates="threat_indicators")
