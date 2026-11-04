"""Early Warning and Notification ORM Models."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin, UUIDMixin
from backend.app.common.enums import AlertSeverity, AlertCategory, AlertStatus, AlertScope


class Alert(Base, UUIDMixin, TimestampMixin):
    """Early Warning electoral misinformation advisory."""

    __tablename__ = "alerts"

    alert_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    full_clarification: Mapped[str] = mapped_column(Text, nullable=False)

    severity: Mapped[str] = mapped_column(String(16), default=AlertSeverity.HIGH.value, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), default=AlertCategory.CONFIRMED_MISINFORMATION.value, index=True, nullable=False)
    target_scope: Mapped[str] = mapped_column(String(16), default=AlertScope.NATIONAL.value, nullable=False)
    target_states: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)  # List of targeted state names

    verification_record_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("verification_records.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=AlertStatus.DRAFT.value, index=True, nullable=False)

    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id], back_populates="alerts_created")
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id])
    verification_record: Mapped[Optional["VerificationRecord"]] = relationship("VerificationRecord", back_populates="alerts")
    deliveries: Mapped[List["NotificationDelivery"]] = relationship("NotificationDelivery", back_populates="alert", cascade="all, delete-orphan")


class NotificationPreference(Base, UUIDMixin, TimestampMixin):
    """Citizen and analyst notification preferences and geographical filters."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    preferred_states: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)

    receive_critical_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    receive_high_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    receive_medium_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    receive_informational: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    channel_in_app: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    channel_push: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    channel_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")


class NotificationDelivery(Base, UUIDMixin, TimestampMixin):
    """Delivery log and read tracking for distributed alerts."""

    __tablename__ = "notification_deliveries"

    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), index=True, nullable=False)
    recipient_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)

    channel: Mapped[str] = mapped_column(String(32), default="IN_APP", nullable=False)  # IN_APP, PUSH, EMAIL
    delivery_status: Mapped[str] = mapped_column(String(32), default="DELIVERED", nullable=False)  # SENT, DELIVERED, FAILED
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="deliveries")
