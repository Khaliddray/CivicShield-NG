"""Institutional Verification and Response Centre business logic."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, desc, case
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.security import compute_audit_hash
from backend.app.core.exceptions import EntityNotFoundException, ValidationException
from backend.app.modules.verification.models import Claim, VerificationRecord
from backend.app.modules.verification.schemas import (
    VerificationDecisionCreate,
    QueueItemOut,
)
from backend.app.modules.reporting.models import Report, ReportStatusHistory
from backend.app.modules.registry.models import OfficialDocument
from backend.app.modules.security_audit.models import AuditLog
from backend.app.modules.security_audit.service import SecurityAuditService
from backend.app.common.enums import ReportStatus, PriorityLevel, VerificationDecision


class VerificationService:
    """Manages the verification queue, authoritative human decision recording, and resolution audit trails."""

    @staticmethod
    def get_queue(
        db: Session,
        nigerian_state: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[QueueItemOut]:
        """Retrieve prioritized verification queue ordered by threat severity and AI contradiction flags."""
        priority_weight = case(
            (Report.priority == PriorityLevel.CRITICAL.value, 4),
            (Report.priority == PriorityLevel.HIGH.value, 3),
            (Report.priority == PriorityLevel.MEDIUM.value, 2),
            else_=1,
        )

        query = (
            select(Claim, Report)
            .join(Report, Claim.report_id == Report.id)
            .where(Claim.requires_human_review == True)
        )

        if nigerian_state:
            query = query.where(Report.nigerian_state == nigerian_state.title())
        if category:
            query = query.where(Claim.category == category.upper())
        if priority:
            query = query.where(Report.priority == priority.upper())

        # Sort by priority rank descending, then AI confidence score descending
        query = query.order_by(desc(priority_weight), desc(Claim.ai_confidence_score), desc(Claim.created_at))
        results = db.execute(query.offset(skip).limit(limit)).all()

        queue_items = []
        for claim, report in results:
            queue_items.append(
                QueueItemOut(
                    claim_id=claim.id,
                    report_id=report.id,
                    report_reference=report.reference_number,
                    claim_text=claim.claim_text,
                    category=claim.category,
                    ai_confidence_score=claim.ai_confidence_score,
                    ai_suggested_status=claim.ai_suggested_status,
                    ai_analysis_summary=claim.ai_analysis_summary,
                    report_priority=report.priority,
                    nigerian_state=report.nigerian_state,
                    incident_date=report.incident_date,
                    created_at=claim.created_at,
                )
            )

        return queue_items

    @classmethod
    def record_decision(
        cls,
        db: Session,
        payload: VerificationDecisionCreate,
        officer_user_id: str,
    ) -> VerificationRecord:
        """Record an authoritative, human-reviewed verification decision backed by evidence."""
        claim = db.execute(select(Claim).where(Claim.id == payload.claim_id)).scalar_one_or_none()
        if not claim:
            raise EntityNotFoundException("Claim", payload.claim_id)

        # Verify official document link if provided
        if payload.official_document_id:
            doc = db.execute(select(OfficialDocument).where(OfficialDocument.id == payload.official_document_id)).scalar_one_or_none()
            if not doc:
                raise EntityNotFoundException("OfficialDocument", payload.official_document_id)

        # 1. Create VerificationRecord
        verification = VerificationRecord(
            claim_id=claim.id,
            verified_by_user_id=officer_user_id,
            decision=payload.decision.value,
            official_document_id=payload.official_document_id,
            justification_notes=payload.justification_notes.strip(),
            public_clarification=payload.public_clarification.strip(),
            evidence_sources_consulted=payload.evidence_sources_consulted or [],
        )
        db.add(verification)
        db.flush()

        # 2. Update claim state
        claim.ai_suggested_status = payload.decision.value
        claim.requires_human_review = False
        claim.updated_at = datetime.now(timezone.utc)

        # 3. Update parent report status
        report = db.execute(select(Report).where(Report.id == claim.report_id)).scalar_one()
        old_report_status = report.status

        # Transition report to VERIFIED or RESOLVED
        new_report_status = ReportStatus.VERIFIED.value if payload.decision == VerificationDecision.VERIFIED else ReportStatus.RESOLVED.value
        report.status = new_report_status
        report.updated_at = datetime.now(timezone.utc)

        status_history = ReportStatusHistory(
            report_id=report.id,
            previous_status=old_report_status,
            new_status=new_report_status,
            notes=f"Claim '{claim.id[:8]}' verified as {payload.decision.value}: {payload.justification_notes[:100]}...",
            changed_by_user_id=officer_user_id,
        )
        db.add(status_history)

        # 4. Tamper-evident Audit Log entry
        SecurityAuditService.record_audit(
            db=db,
            action="CLAIM_VERIFIED",
            entity_type="CLAIM",
            entity_id=claim.id,
            user_id=officer_user_id,
            details={
                "decision": payload.decision.value,
                "report_id": report.id,
                "report_reference": report.reference_number,
                "official_document_id": payload.official_document_id,
            },
            commit=False,
        )

        db.commit()
        db.refresh(verification)
        logger.info(f"Claim {claim.id} verified as {payload.decision.value} by officer {officer_user_id}")
        return verification

    @staticmethod
    def get_verification_record(db: Session, record_id: str) -> Optional[VerificationRecord]:
        """Fetch verification finding by primary key."""
        return db.execute(select(VerificationRecord).where(VerificationRecord.id == record_id)).scalar_one_or_none()

    @staticmethod
    def get_claim(db: Session, claim_id: str) -> Optional[Claim]:
        """Fetch claim entity along with all attached verification records."""
        return db.execute(select(Claim).where(Claim.id == claim_id)).scalar_one_or_none()
