"""Citizen Reporting business logic and evidence file processor."""

import os
import secrets
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import hash_ip_for_privacy, compute_audit_hash
from backend.app.core.exceptions import ValidationException, EntityNotFoundException
from backend.app.modules.reporting.models import Report, UploadedEvidence, ReportStatusHistory
from backend.app.modules.reporting.schemas import ReportCreateRequest
from backend.app.modules.verification.models import Claim
from backend.app.modules.security_audit.models import AuditLog
from backend.app.modules.security_audit.service import SecurityAuditService
from backend.app.common.enums import ReportStatus, PriorityLevel, MediaType, VerificationDecision, ClaimCategory


class ReportingService:
    """Manages citizen report ingestion, evidence sanitization, and lifecycle transitions."""

    @staticmethod
    def generate_reference_number(db: Session) -> str:
        """Generate a collision-resistant, human-friendly tracking code (e.g., CS-20261104-A1B2C3)."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        for _ in range(10):
            random_suffix = secrets.token_hex(3).upper()
            ref = f"CS-{date_str}-{random_suffix}"
            exists = db.execute(select(Report.id).where(Report.reference_number == ref)).first()
            if not exists:
                return ref
        raise RuntimeError("Failed to generate unique reference number after 10 attempts.")

    @staticmethod
    def _detect_media_type(mime_type: str) -> str:
        """Classify MIME type into domain MediaType."""
        if mime_type in settings.ALLOWED_IMAGE_TYPES:
            return MediaType.IMAGE.value
        elif mime_type in settings.ALLOWED_AUDIO_TYPES:
            return MediaType.AUDIO.value
        elif mime_type in settings.ALLOWED_VIDEO_TYPES:
            return MediaType.VIDEO.value
        elif mime_type in settings.ALLOWED_DOCUMENT_TYPES:
            return MediaType.DOCUMENT.value
        else:
            raise ValidationException(
                f"Unsupported media MIME type '{mime_type}'. Supported: images, audio recordings, video, and PDF documents."
            )

    @classmethod
    def submit_report(
        cls,
        db: Session,
        report_data: ReportCreateRequest,
        files: Optional[List[UploadFile]] = None,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Report:
        """Ingest a citizen report, sanitize attached evidence, and persist initial tracking records."""
        reference_number = cls.generate_reference_number(db)
        ip_hash = hash_ip_for_privacy(client_ip)

        report = Report(
            reference_number=reference_number,
            user_id=user_id,
            title=report_data.title.strip(),
            content_text=report_data.content_text.strip(),
            encounter_location=report_data.encounter_location.strip() if report_data.encounter_location else None,
            nigerian_state=report_data.nigerian_state,
            incident_date=report_data.incident_date or datetime.now(timezone.utc),
            status=ReportStatus.SUBMITTED.value,
            priority=PriorityLevel.MEDIUM.value,
            submitter_ip_hash=ip_hash,
        )
        db.add(report)
        db.flush()

        # Record initial status transition
        history = ReportStatusHistory(
            report_id=report.id,
            previous_status="NONE",
            new_status=ReportStatus.SUBMITTED.value,
            notes="Report initially submitted by citizen.",
            changed_by_user_id=user_id,
        )
        db.add(history)

        # Process attached evidence files with chunked streaming (64KB buffer)
        if files:
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            CHUNK_SIZE = 64 * 1024
            for upload in files:
                if not upload.filename:
                    continue

                extension = Path(upload.filename).suffix.lower() or ".bin"
                safe_filename = f"{secrets.token_hex(16)}{extension}"
                target_path = settings.UPLOAD_DIR / safe_filename

                hasher = hashlib.sha256()
                file_size = 0

                try:
                    with open(target_path, "wb") as f:
                        while True:
                            chunk = upload.file.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            file_size += len(chunk)
                            if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                                raise ValidationException(
                                    f"File '{upload.filename}' ({file_size / (1024*1024):.2f}MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f}MB."
                                )
                            hasher.update(chunk)
                            f.write(chunk)
                except Exception:
                    if target_path.exists():
                        target_path.unlink()
                    raise

                mime_type = upload.content_type or "application/octet-stream"
                media_type = cls._detect_media_type(mime_type)
                sha256_hash = hasher.hexdigest()

                evidence = UploadedEvidence(
                    report_id=report.id,
                    file_name=safe_filename,
                    original_file_name=upload.filename[:255],
                    file_type=media_type,
                    mime_type=mime_type,
                    file_size_bytes=file_size,
                    storage_path=str(target_path),
                    sha256_hash=sha256_hash,
                )
                db.add(evidence)

        # Initialize primary unverified claim from the report content
        claim = Claim(
            report_id=report.id,
            claim_text=report.title,
            category=ClaimCategory.GENERAL_ELECTORAL.value,
            ai_confidence_score=0.5,
            ai_analysis_summary="Preliminary submission received. Pending automated claim extraction and registry matching.",
            ai_suggested_status=VerificationDecision.UNVERIFIED.value,
            requires_human_review=True,
        )
        db.add(claim)

        # Audit log
        SecurityAuditService.record_audit(
            db=db,
            action="REPORT_SUBMITTED",
            entity_type="REPORT",
            entity_id=report.id,
            user_id=user_id,
            ip_address=client_ip,
            details={
                "reference_number": reference_number,
                "state": report.nigerian_state,
                "files_count": len(files) if files else 0,
            },
            commit=False,
        )

        db.commit()
        db.refresh(report)
        logger.info(f"New report ingested: {reference_number} (State: {report.nigerian_state})")
        return report

    @staticmethod
    def get_by_reference(db: Session, reference_number: str) -> Optional[Report]:
        """Publicly trackable query by reference code."""
        return db.execute(
            select(Report).where(Report.reference_number == reference_number.upper().strip())
        ).scalar_one_or_none()

    @staticmethod
    def get_by_id(db: Session, report_id: str) -> Optional[Report]:
        """Internal lookup by primary key."""
        return db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()

    @staticmethod
    def list_user_reports(db: Session, user_id: str, skip: int = 0, limit: int = 20) -> List[Report]:
        """Retrieve submission history for an authenticated citizen."""
        return list(
            db.execute(
                select(Report)
                .where(Report.user_id == user_id)
                .order_by(desc(Report.created_at))
                .offset(skip)
                .limit(limit)
            ).scalars().all()
        )

    @staticmethod
    def list_reports(
        db: Session,
        nigerian_state: Optional[str] = None,
        report_status: Optional[str] = None,
        priority: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Report], int]:
        """Command Centre query for analysts and verification officers with filters and pagination."""
        query = select(Report)

        if nigerian_state:
            query = query.where(Report.nigerian_state == nigerian_state.title())
        if report_status:
            query = query.where(Report.status == report_status.upper())
        if priority:
            query = query.where(Report.priority == priority.upper())
        if search_query:
            query = query.where(
                Report.title.ilike(f"%{search_query}%") | Report.content_text.ilike(f"%{search_query}%")
            )

        total_count = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

        items = list(
            db.execute(query.order_by(desc(Report.created_at)).offset(skip).limit(limit)).scalars().all()
        )
        return items, total_count

    @staticmethod
    def update_status(
        db: Session,
        report_id: str,
        new_status: str,
        notes: Optional[str] = None,
        changed_by_user_id: Optional[str] = None,
    ) -> Report:
        """Update report lifecycle status and record status audit transition."""
        report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
        if not report:
            raise EntityNotFoundException("Report", report_id)

        old_status = report.status
        report.status = new_status
        report.updated_at = datetime.now(timezone.utc)

        history = ReportStatusHistory(
            report_id=report.id,
            previous_status=old_status,
            new_status=new_status,
            notes=notes,
            changed_by_user_id=changed_by_user_id,
        )
        db.add(history)

        # Audit log entry
        SecurityAuditService.record_audit(
            db=db,
            action="REPORT_STATUS_UPDATED",
            entity_type="REPORT",
            entity_id=report.id,
            user_id=changed_by_user_id,
            details={
                "previous_status": old_status,
                "new_status": new_status,
                "notes": notes,
            },
            commit=False,
        )

        db.commit()
        db.refresh(report)
        logger.info(f"Report {report.reference_number} transitioned from {old_status} to {new_status}")
        return report

    @staticmethod
    def get_evidence(db: Session, evidence_id: str) -> UploadedEvidence:
        """Retrieve evidence item by ID or raise EntityNotFoundException."""
        evidence = db.execute(select(UploadedEvidence).where(UploadedEvidence.id == evidence_id)).scalar_one_or_none()
        if not evidence:
            raise EntityNotFoundException("UploadedEvidence", evidence_id)
        return evidence

    @staticmethod
    def get_secure_file_path(evidence: UploadedEvidence) -> Path:
        """Resolve file path securely, preventing path traversal attacks."""
        resolved = Path(evidence.storage_path).resolve()
        upload_root = settings.UPLOAD_DIR.resolve()

        # Strict containment check preventing directory traversal
        if not resolved.is_relative_to(upload_root):
            raise ValidationException("Illegal file path access attempt detected. Security violation recorded.")

        if not resolved.exists() or not resolved.is_file():
            raise EntityNotFoundException("EvidenceFile", evidence.id)

        return resolved

    @staticmethod
    def assign_analyst(
        db: Session,
        report_id: str,
        analyst_id: str,
        assigned_by_user_id: str,
        notes: Optional[str] = None,
    ) -> Report:
        """Assign an institutional analyst to an incoming report."""
        report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
        if not report:
            raise EntityNotFoundException("Report", report_id)

        report.assigned_analyst_id = analyst_id
        report.updated_at = datetime.now(timezone.utc)

        history = ReportStatusHistory(
            report_id=report.id,
            previous_status=report.status,
            new_status=report.status,
            notes=f"Assigned to analyst {analyst_id[:8]}... Notes: {notes or 'No notes provided'}",
            changed_by_user_id=assigned_by_user_id,
        )
        db.add(history)

        SecurityAuditService.record_audit(
            db=db,
            action="REPORT_ANALYST_ASSIGNED",
            entity_type="REPORT",
            entity_id=report.id,
            user_id=assigned_by_user_id,
            details={"assigned_analyst_id": analyst_id, "notes": notes},
            commit=True,
        )
        db.refresh(report)
        logger.info(f"Report {report.reference_number} assigned to analyst {analyst_id}")
        return report

    @staticmethod
    def withdraw_report(
        db: Session,
        report_id: str,
        withdrawn_by_user_id: Optional[str],
        reason: str,
    ) -> Report:
        """Withdraw a report from active investigation."""
        report = db.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()
        if not report:
            raise EntityNotFoundException("Report", report_id)

        old_status = report.status
        report.status = "WITHDRAWN"
        report.updated_at = datetime.now(timezone.utc)

        history = ReportStatusHistory(
            report_id=report.id,
            previous_status=old_status,
            new_status="WITHDRAWN",
            notes=f"Report withdrawn: {reason}",
            changed_by_user_id=withdrawn_by_user_id,
        )
        db.add(history)

        SecurityAuditService.record_audit(
            db=db,
            action="REPORT_WITHDRAWN",
            entity_type="REPORT",
            entity_id=report.id,
            user_id=withdrawn_by_user_id,
            details={"reason": reason, "previous_status": old_status},
            commit=True,
        )
        db.refresh(report)
        logger.info(f"Report {report.reference_number} marked WITHDRAWN: {reason}")
        return report
