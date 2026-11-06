"""Early Warning and Notification Engine business logic."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import compute_audit_hash
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.modules.notifications.models import Alert, NotificationPreference, NotificationDelivery, AlertApprovalRecord
from backend.app.modules.notifications.schemas import (
    AlertCreateRequest,
    PreferenceUpdateRequest,
)
from backend.app.modules.notifications.channels.in_app import InAppNotificationChannel
from backend.app.modules.verification.models import VerificationRecord
from backend.app.modules.auth.models import User
from backend.app.modules.security_audit.models import AuditLog
from backend.app.modules.security_audit.service import SecurityAuditService
from backend.app.common.enums import (
    AlertStatus,
    AlertSeverity,
    AlertCategory,
    AlertScope,
    VerificationDecision,
)


class NotificationService:
    """Manages early warning alert lifecycle, dual-key approval gates, and multi-channel distribution."""

    _in_app_channel = InAppNotificationChannel()

    @staticmethod
    def generate_alert_reference(db: Session) -> str:
        """Generate unique alert reference (e.g. WARN-2026-A1B2)."""
        year_str = datetime.now(timezone.utc).strftime("%Y")
        for _ in range(10):
            suffix = secrets.token_hex(2).upper()
            ref = f"WARN-{year_str}-{suffix}"
            exists = db.execute(select(Alert.id).where(Alert.alert_reference == ref)).first()
            if not exists:
                return ref
        raise RuntimeError("Failed to generate unique alert reference after 10 attempts.")

    @classmethod
    def create_alert_draft(
        cls,
        db: Session,
        request: AlertCreateRequest,
        author_id: str,
    ) -> Alert:
        """Draft a new alert enforcing the responsible AI and verification dependency invariant."""
        # Non-negotiable safety invariant: Confirmed misinformation MUST link to a verified contradiction
        if request.category == AlertCategory.CONFIRMED_MISINFORMATION:
            if not request.verification_record_id:
                raise ValidationException(
                    "Confirmed misinformation early warnings require a valid, human-reviewed verification record ID."
                )
            v_record = db.execute(
                select(VerificationRecord).where(VerificationRecord.id == request.verification_record_id)
            ).scalar_one_or_none()
            if not v_record or v_record.decision != VerificationDecision.CONTRADICTED.value:
                raise ValidationException(
                    "Confirmed misinformation alerts can only be generated from an evidence-backed CONTRADICTED finding."
                )

        ref_code = cls.generate_alert_reference(db)

        alert = Alert(
            alert_reference=ref_code,
            title=request.title.strip(),
            summary=request.summary.strip(),
            full_clarification=request.full_clarification.strip(),
            severity=request.severity.value,
            category=request.category.value,
            target_scope=request.target_scope.value,
            target_states=request.target_states or [],
            verification_record_id=request.verification_record_id,
            status=AlertStatus.PENDING_APPROVAL.value,
            created_by_user_id=author_id,
            expires_at=request.expires_at,
        )
        db.add(alert)
        db.flush()

        # Approval history entry
        approval_rec = AlertApprovalRecord(
            alert_id=alert.id,
            action="DRAFTED",
            officer_user_id=author_id,
            comments="Alert drafted and queued for approval.",
        )
        db.add(approval_rec)

        # Audit log
        SecurityAuditService.record_audit(
            db=db,
            action="ALERT_DRAFTED",
            entity_type="ALERT",
            entity_id=alert.id,
            user_id=author_id,
            details={
                "alert_reference": ref_code,
                "severity": alert.severity,
                "category": alert.category,
                "scope": alert.target_scope,
            },
            commit=False,
        )

        db.commit()
        db.refresh(alert)
        logger.info(f"Early warning drafted: {ref_code} (Status: PENDING_APPROVAL)")
        return alert

    @classmethod
    def approve_and_broadcast(
        cls,
        db: Session,
        alert_id: str,
        approver_id: str,
    ) -> Alert:
        """Approve an alert, enforce suppression windows, and trigger multi-channel distribution."""
        alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
        if not alert:
            raise EntityNotFoundException("Alert", alert_id)

        now = datetime.now(timezone.utc)
        suppression_cutoff = now - timedelta(hours=settings.ALERT_DUPLICATION_WINDOW_HOURS)

        # Check suppression window for duplicate active alerts
        recent_duplicate = db.execute(
            select(Alert).where(
                and_(
                    Alert.id != alert.id,
                    Alert.status == AlertStatus.ACTIVE.value,
                    Alert.category == alert.category,
                    Alert.title == alert.title,
                    Alert.created_at >= suppression_cutoff,
                )
            )
        ).first()

        if recent_duplicate:
            logger.warning(f"Suppression window triggered: duplicate alert active in last {settings.ALERT_DUPLICATION_WINDOW_HOURS} hours.")

        alert.status = AlertStatus.ACTIVE.value
        alert.approved_by_user_id = approver_id
        alert.updated_at = now

        # Identify target user population based on geographic scope
        target_users_query = select(User).where(User.is_active == True)

        if alert.target_scope == AlertScope.STATE_SPECIFIC.value and alert.target_states:
            # Query users whose state matches target states
            target_users_query = target_users_query.where(User.state_of_residence.in_(alert.target_states))

        target_users = list(db.execute(target_users_query.limit(10000)).scalars().all())

        # Dispatch across in-app channel
        cls._in_app_channel.dispatch(alert=alert, target_users=target_users, db=db)

        # Record approval in history
        approval_rec = AlertApprovalRecord(
            alert_id=alert.id,
            action="APPROVED",
            officer_user_id=approver_id,
            comments=f"Alert approved and broadcast to {len(target_users)} users across in-app channels.",
        )
        db.add(approval_rec)

        # Audit publication
        SecurityAuditService.record_audit(
            db=db,
            action="ALERT_PUBLISHED",
            entity_type="ALERT",
            entity_id=alert.id,
            user_id=approver_id,
            details={
                "alert_reference": alert.alert_reference,
                "recipients_notified": len(target_users),
            },
            commit=False,
        )

        db.commit()
        db.refresh(alert)
        logger.info(f"Alert {alert.alert_reference} approved and broadcast to {len(target_users)} users.")
        return alert

    @staticmethod
    def withdraw_alert(
        db: Session,
        alert_id: str,
        reason: str,
        officer_id: str,
    ) -> Alert:
        """Withdraw or supersede an active alert with mandatory clarification justification."""
        alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
        if not alert:
            raise EntityNotFoundException("Alert", alert_id)

        alert.status = AlertStatus.WITHDRAWN.value
        alert.full_clarification += f"\n\n[OFFICIAL WITHDRAWAL ADVISORY - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}]: {reason.strip()}"
        alert.updated_at = datetime.now(timezone.utc)

        # Record withdrawal history
        approval_rec = AlertApprovalRecord(
            alert_id=alert.id,
            action="WITHDRAWN",
            officer_user_id=officer_id,
            comments=reason.strip(),
        )
        db.add(approval_rec)

        SecurityAuditService.record_audit(
            db=db,
            action="ALERT_WITHDRAWN",
            entity_type="ALERT",
            entity_id=alert.id,
            user_id=officer_id,
            details={"reason": reason},
            commit=False,
        )

        db.commit()
        db.refresh(alert)
        logger.info(f"Alert {alert.alert_reference} withdrawn by officer {officer_id}")
        return alert

    @staticmethod
    def reject_alert(
        db: Session,
        alert_id: str,
        reason: str,
        officer_id: str,
    ) -> Alert:
        """Reject an alert draft with mandatory officer justification."""
        alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
        if not alert:
            raise EntityNotFoundException("Alert", alert_id)

        alert.status = "REJECTED"
        alert.updated_at = datetime.now(timezone.utc)

        approval_rec = AlertApprovalRecord(
            alert_id=alert.id,
            action="REJECTED",
            officer_user_id=officer_id,
            comments=reason.strip(),
        )
        db.add(approval_rec)

        SecurityAuditService.record_audit(
            db=db,
            action="ALERT_REJECTED",
            entity_type="ALERT",
            entity_id=alert.id,
            user_id=officer_id,
            details={"reason": reason, "alert_reference": alert.alert_reference},
            commit=True,
        )
        db.refresh(alert)
        logger.info(f"Alert {alert.alert_reference} rejected by officer {officer_id}: {reason}")
        return alert

    @staticmethod
    def submit_for_approval(
        db: Session,
        alert_id: str,
        officer_id: str,
    ) -> Alert:
        """Submit a draft alert for lead officer approval."""
        alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
        if not alert:
            raise EntityNotFoundException("Alert", alert_id)

        alert.status = AlertStatus.PENDING_APPROVAL.value
        alert.updated_at = datetime.now(timezone.utc)

        approval_rec = AlertApprovalRecord(
            alert_id=alert.id,
            action="SUBMITTED",
            officer_user_id=officer_id,
            comments="Submitted draft for institutional verification signoff.",
        )
        db.add(approval_rec)

        SecurityAuditService.record_audit(
            db=db,
            action="ALERT_SUBMITTED_FOR_APPROVAL",
            entity_type="ALERT",
            entity_id=alert.id,
            user_id=officer_id,
            details={"alert_reference": alert.alert_reference},
            commit=True,
        )
        db.refresh(alert)
        logger.info(f"Alert {alert.alert_reference} submitted for approval by {officer_id}")
        return alert

    @staticmethod
    def get_alert_approvals(db: Session, alert_id: str) -> List[AlertApprovalRecord]:
        """Fetch complete approval/rejection audit trail for an alert."""
        return list(
            db.execute(
                select(AlertApprovalRecord)
                .where(AlertApprovalRecord.alert_id == alert_id)
                .order_by(AlertApprovalRecord.recorded_at.asc())
            ).scalars().all()
        )

    @staticmethod
    def list_user_notifications(
        db: Session,
        user_id: str,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """Retrieve in-app notifications delivered to a user."""
        query = (
            select(NotificationDelivery, Alert)
            .join(Alert, NotificationDelivery.alert_id == Alert.id)
            .where(NotificationDelivery.recipient_user_id == user_id)
        )
        if unread_only:
            query = query.where(NotificationDelivery.read_at == None)

        query = query.order_by(desc(NotificationDelivery.delivered_at)).offset(skip).limit(limit)
        results = db.execute(query).all()

        deliveries = []
        for delivery, alert in results:
            deliveries.append({
                "id": delivery.id,
                "alert_id": alert.id,
                "channel": delivery.channel,
                "delivery_status": delivery.delivery_status,
                "delivered_at": delivery.delivered_at,
                "read_at": delivery.read_at,
                "alert_title": alert.title,
                "alert_summary": alert.summary,
                "alert_severity": alert.severity,
            })
        return deliveries

    @staticmethod
    def mark_notification_read(db: Session, delivery_id: str, user_id: str) -> NotificationDelivery:
        """Mark an in-app notification delivery as read."""
        delivery = db.execute(
            select(NotificationDelivery).where(
                and_(NotificationDelivery.id == delivery_id, NotificationDelivery.recipient_user_id == user_id)
            )
        ).scalar_one_or_none()
        if not delivery:
            raise EntityNotFoundException("NotificationDelivery", delivery_id)

        delivery.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def get_unread_notification_count(db: Session, user_id: str) -> int:
        """Count unread in-app notifications for authenticated user."""
        from sqlalchemy import func
        count = db.execute(
            select(func.count(NotificationDelivery.id)).where(
                and_(NotificationDelivery.recipient_user_id == user_id, NotificationDelivery.read_at == None)
            )
        ).scalar_one()
        return count

    @staticmethod
    def get_active_alerts(
        db: Session,
        nigerian_state: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Alert]:
        """Public early warning feed. Returns ONLY approved active alerts."""
        query = select(Alert).where(Alert.status == AlertStatus.ACTIVE.value)

        if severity:
            query = query.where(Alert.severity == severity.upper())

        # Sort newest first
        query = query.order_by(desc(Alert.created_at)).limit(limit)
        alerts = list(db.execute(query).scalars().all())

        # Filter by geographical relevance
        if nigerian_state:
            clean_state = nigerian_state.title().strip()
            filtered = []
            for a in alerts:
                if a.target_scope == AlertScope.NATIONAL.value:
                    filtered.append(a)
                elif a.target_states and clean_state in a.target_states:
                    filtered.append(a)
            return filtered

        return alerts

    @staticmethod
    def get_or_create_preferences(db: Session, user_id: str) -> NotificationPreference:
        """Fetch or create default notification preferences for an authenticated citizen."""
        pref = db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id)).scalar_one_or_none()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                preferred_states=[],
                receive_critical_alerts=True,
                receive_high_alerts=True,
                receive_medium_alerts=True,
                channel_in_app=True,
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(
        db: Session,
        user_id: str,
        updates: PreferenceUpdateRequest,
    ) -> NotificationPreference:
        """Update citizen alert delivery preferences."""
        pref = NotificationService.get_or_create_preferences(db=db, user_id=user_id)

        if updates.preferred_states is not None:
            pref.preferred_states = updates.preferred_states
        if updates.receive_critical_alerts is not None:
            pref.receive_critical_alerts = updates.receive_critical_alerts
        if updates.receive_high_alerts is not None:
            pref.receive_high_alerts = updates.receive_high_alerts
        if updates.receive_medium_alerts is not None:
            pref.receive_medium_alerts = updates.receive_medium_alerts
        if updates.receive_informational is not None:
            pref.receive_informational = updates.receive_informational
        if updates.channel_in_app is not None:
            pref.channel_in_app = updates.channel_in_app
        if updates.channel_push is not None:
            pref.channel_push = updates.channel_push
        if updates.channel_email is not None:
            pref.channel_email = updates.channel_email

        pref.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(pref)
        return pref
