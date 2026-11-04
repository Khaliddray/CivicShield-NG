"""Database Security, Tamper-Evident Audit Logs, and Threat Event ORM Models."""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base, TimestampMixin, UUIDMixin
from backend.app.common.enums import PriorityLevel, SecurityEventType


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Immutable, cryptographically chained audit log of consequential platform operations."""

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    sha256_entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class SecurityEvent(Base, UUIDMixin, TimestampMixin):
    """Technical security incident monitor (e.g. repeated auth failures, brute force, tamper detection)."""

    __tablename__ = "security_events"

    event_type: Mapped[str] = mapped_column(String(64), default=SecurityEventType.AUTH_FAILURE.value, index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default=PriorityLevel.MEDIUM.value, index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), index=True, nullable=True)
    user_identifier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email or user ID attempted
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
