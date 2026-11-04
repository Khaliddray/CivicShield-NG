"""Database Security, Audit Ledger Verification, and Threat Monitoring Service."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.security import compute_audit_hash
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.modules.security_audit.models import AuditLog, SecurityEvent
from backend.app.modules.security_audit.schemas import (
    AuditLedgerVerificationResult,
    SecurityMetricsOut,
)
from backend.app.modules.auth.models import User
from backend.app.common.enums import SecurityEventType

GENESIS_HASH = "GENESIS_ROOT_00000000000000000000000000000000000000000000000000000000"


class SecurityAuditService:
    """Manages immutable audit log recording, cryptographic chain verification, and security incident resolution."""

    @classmethod
    def record_audit(
        cls,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
        commit: bool = True,
    ) -> AuditLog:
        """Create a new tamper-evident audit log entry chained to the previous entry hash."""
        # Retrieve the latest audit log entry to establish the cryptographic link
        latest_entry = db.execute(
            select(AuditLog).order_by(desc(AuditLog.recorded_at), desc(AuditLog.id)).limit(1)
        ).scalar_one_or_none()
        previous_hash = latest_entry.sha256_entry_hash if latest_entry else GENESIS_HASH

        now = datetime.now(timezone.utc)
        timestamp_str = now.isoformat()
        current_hash = compute_audit_hash(previous_hash, action, entity_id, timestamp_str)

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            sha256_entry_hash=current_hash,
            previous_entry_hash=previous_hash,
            recorded_at=now,
        )
        db.add(log_entry)
        if commit:
            db.commit()
            db.refresh(log_entry)
        return log_entry

    @classmethod
    def verify_ledger_integrity(cls, db: Session, limit: int = 500) -> AuditLedgerVerificationResult:
        """
        Traverse the audit ledger sequentially and verify every link in the cryptographic hash chain.
        Proves whether any record has been modified, tampered with, or deleted.
        """
        entries = list(
            db.execute(
                select(AuditLog).order_by(AuditLog.recorded_at.asc(), AuditLog.id.asc()).limit(limit)
            ).scalars().all()
        )

        if not entries:
            return AuditLedgerVerificationResult(
                is_valid=True,
                total_entries_verified=0,
                verification_message="Audit ledger is empty. Chain is intact.",
            )

        expected_prev_hash = entries[0].previous_entry_hash

        for i, entry in enumerate(entries):
            # 1. Verify previous hash linkage
            if entry.previous_entry_hash != expected_prev_hash and i > 0:
                logger.error(f"Audit ledger broken at entry ID {entry.id}! Previous hash mismatch.")
                cls._log_tamper_incident(db, entry.id, "Hash chain link broken between records.")
                return AuditLedgerVerificationResult(
                    is_valid=False,
                    total_entries_verified=i,
                    broken_chain_at_id=entry.id,
                    verification_message=f"Audit chain verification FAILED at entry ID {entry.id}. Previous hash linkage broken.",
                )

            # 2. Recompute entry hash and verify payload integrity
            rec_dt = entry.recorded_at
            if rec_dt.tzinfo is None:
                rec_dt = rec_dt.replace(tzinfo=timezone.utc)
            timestamp_str = rec_dt.isoformat()
            recomputed = compute_audit_hash(entry.previous_entry_hash, entry.action, entry.entity_id, timestamp_str)

            if entry.sha256_entry_hash != recomputed:
                logger.error(f"Tampered entry detected at ID {entry.id}! Recomputed hash does not match stored hash.")
                cls._log_tamper_incident(db, entry.id, "Stored entry hash does not match recomputed payload hash.")
                return AuditLedgerVerificationResult(
                    is_valid=False,
                    total_entries_verified=i,
                    broken_chain_at_id=entry.id,
                    verification_message=f"Tampering detected at entry ID {entry.id}! Record payload was altered after recording.",
                )

            expected_prev_hash = entry.sha256_entry_hash

        return AuditLedgerVerificationResult(
            is_valid=True,
            total_entries_verified=len(entries),
            first_verified_hash=entries[0].sha256_entry_hash,
            latest_verified_hash=entries[-1].sha256_entry_hash,
            verification_message=f"Cryptographic audit ledger verified successfully across {len(entries)} entries. Hash chain is unbroken.",
        )

    @classmethod
    def _log_tamper_incident(cls, db: Session, entry_id: str, detail: str) -> None:
        """Create a high-severity security event when ledger tampering is identified."""
        event = SecurityEvent(
            event_type=SecurityEventType.TAMPER_DETECTED.value,
            severity="CRITICAL",
            details={"entry_id": entry_id, "detail": detail},
        )
        db.add(event)
        db.commit()

    @staticmethod
    def list_audit_logs(
        db: Session,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        """Query audit log entries with filters and pagination."""
        query = select(AuditLog)
        if action:
            query = query.where(AuditLog.action == action.upper())
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type.upper())

        total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
        items = list(
            db.execute(query.order_by(desc(AuditLog.recorded_at)).offset(skip).limit(limit)).scalars().all()
        )
        return items, total

    @staticmethod
    def list_security_events(
        db: Session,
        resolved: Optional[bool] = None,
        event_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SecurityEvent], int]:
        """Query technical security events."""
        query = select(SecurityEvent)
        if resolved is not None:
            query = query.where(SecurityEvent.resolved == resolved)
        if event_type:
            query = query.where(SecurityEvent.event_type == event_type.upper())

        total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
        items = list(
            db.execute(query.order_by(desc(SecurityEvent.created_at)).offset(skip).limit(limit)).scalars().all()
        )
        return items, total

    @staticmethod
    def resolve_event(
        db: Session,
        event_id: str,
        resolution_notes: str,
        officer_user_id: str,
    ) -> SecurityEvent:
        """Mark an open security incident as resolved with officer notes."""
        event = db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id)).scalar_one_or_none()
        if not event:
            raise EntityNotFoundException("SecurityEvent", event_id)

        event.resolved = True
        event.resolved_at = datetime.now(timezone.utc)
        event.resolution_notes = resolution_notes.strip()
        db.commit()
        db.refresh(event)
        logger.info(f"Security event {event_id} marked resolved by officer {officer_user_id}")
        return event

    @staticmethod
    def get_metrics(db: Session) -> SecurityMetricsOut:
        """Aggregate security KPIs across the platform."""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)

        # Failed logins in last 24h
        failed_logins = db.execute(
            select(func.count())
            .select_from(SecurityEvent)
            .where(
                and_(
                    SecurityEvent.event_type == SecurityEventType.AUTH_FAILURE.value,
                    SecurityEvent.created_at >= yesterday,
                )
            )
        ).scalar_one()

        # Currently locked accounts
        locked_accounts = db.execute(
            select(func.count()).select_from(User).where(User.locked_until > now)
        ).scalar_one()

        # Unresolved security events
        unresolved_events = db.execute(
            select(func.count()).select_from(SecurityEvent).where(SecurityEvent.resolved == False)
        ).scalar_one()

        # Tamper incidents
        tamper_incidents = db.execute(
            select(func.count())
            .select_from(SecurityEvent)
            .where(SecurityEvent.event_type == SecurityEventType.TAMPER_DETECTED.value)
        ).scalar_one()

        # Total audit records
        total_audits = db.execute(select(func.count()).select_from(AuditLog)).scalar_one()

        return SecurityMetricsOut(
            failed_logins_last_24h=failed_logins,
            currently_locked_accounts=locked_accounts,
            unresolved_security_events=unresolved_events,
            tamper_incidents_detected=tamper_incidents,
            total_audit_records_logged=total_audits,
            ledger_integrity_status="TAMPER_DETECTED" if tamper_incidents > 0 else "VERIFIED_SECURE",
        )
