"""Official Information Verification Registry business logic."""

import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.security import compute_audit_hash
from backend.app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    ValidationException,
)
from backend.app.modules.registry.models import OfficialDocument, DocumentVersion
from backend.app.modules.registry.schemas import (
    DocumentCreateRequest,
    HashVerificationRequest,
    HashVerificationResponse,
)
from backend.app.modules.security_audit.models import AuditLog
from backend.app.modules.security_audit.service import SecurityAuditService


class RegistryService:
    """Manages certified electoral documents, canonical hash computation, and tampering checks."""

    @staticmethod
    def compute_sha256(content: str) -> str:
        """Compute standardized canonical SHA-256 hash of text."""
        # Normalize whitespace and line endings to prevent superficial hash mismatches
        normalized = "\n".join(line.rstrip() for line in content.strip().splitlines())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def register_document(
        cls,
        db: Session,
        request: DocumentCreateRequest,
        authorized_user_id: str,
    ) -> OfficialDocument:
        """Register a new certified official announcement in the trusted repository."""
        # Check uniqueness of document code
        clean_code = request.document_code.strip().upper()
        existing = db.execute(select(OfficialDocument).where(OfficialDocument.document_code == clean_code)).scalar_one_or_none()
        if existing:
            raise DuplicateEntityException("OfficialDocument", "document_code", clean_code)

        canonical_hash = cls.compute_sha256(request.content_text)

        doc = OfficialDocument(
            document_code=clean_code,
            issuing_institution=request.issuing_institution.strip(),
            title=request.title.strip(),
            summary=request.summary.strip(),
            content_text=request.content_text.strip(),
            current_version=1,
            sha256_hash=canonical_hash,
            digital_signature_info=request.digital_signature_info,
            publication_date=datetime.now(timezone.utc),
            source_url=request.source_url.strip() if request.source_url else None,
            is_authenticated=True,
            authorized_by_user_id=authorized_user_id,
        )
        db.add(doc)
        db.flush()

        # Create initial document version record
        version = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            sha256_hash=canonical_hash,
            content_text=doc.content_text,
            change_summary="Initial certified publication.",
            changed_by_user_id=authorized_user_id,
        )
        db.add(version)

        # Audit log entry
        SecurityAuditService.record_audit(
            db=db,
            action="DOCUMENT_CERTIFIED",
            entity_type="OFFICIAL_DOCUMENT",
            entity_id=doc.id,
            user_id=authorized_user_id,
            details={
                "document_code": clean_code,
                "institution": doc.issuing_institution,
                "sha256_hash": canonical_hash,
            },
            commit=False,
        )

        db.commit()
        db.refresh(doc)
        logger.info(f"Official document registered: {doc.document_code} [{doc.issuing_institution}]")
        return doc

    @classmethod
    def verify_document_integrity(
        cls,
        db: Session,
        request: HashVerificationRequest,
    ) -> HashVerificationResponse:
        """Verify if a submitted document hash or content matches a certified official release."""
        if request.sha256_hash:
            target_hash = request.sha256_hash.strip().lower()
        elif request.content_text:
            target_hash = cls.compute_sha256(request.content_text)
        else:
            raise ValidationException("Either 'sha256_hash' or 'content_text' must be provided for verification.")

        # 1. Search for exact hash match in official registry
        doc = db.execute(select(OfficialDocument).where(OfficialDocument.sha256_hash == target_hash)).scalar_one_or_none()

        if doc:
            return HashVerificationResponse(
                is_official_match=True,
                matched_document_code=doc.document_code,
                issuing_institution=doc.issuing_institution,
                document_title=doc.title,
                canonical_hash=doc.sha256_hash,
                submitted_hash=target_hash,
                verification_status="EXACT_MATCH",
                analytical_note=(
                    f"Verified authentic. Cryptographic hash matches official announcement '{doc.title}' "
                    f"issued by {doc.issuing_institution} (Code: {doc.document_code})."
                ),
            )

        # 2. Check historical document versions
        version_match = db.execute(select(DocumentVersion).where(DocumentVersion.sha256_hash == target_hash)).scalar_one_or_none()
        if version_match:
            parent_doc = db.execute(select(OfficialDocument).where(OfficialDocument.id == version_match.document_id)).scalar_one()
            return HashVerificationResponse(
                is_official_match=True,
                matched_document_code=parent_doc.document_code,
                issuing_institution=parent_doc.issuing_institution,
                document_title=parent_doc.title,
                canonical_hash=parent_doc.sha256_hash,
                submitted_hash=target_hash,
                verification_status="HISTORICAL_VERSION_MATCH",
                analytical_note=(
                    f"Matches version {version_match.version_number} of '{parent_doc.title}'. "
                    f"Note: An updated version ({parent_doc.current_version}) is currently active."
                ),
            )

        # 3. Check for partial text similarity / tampering signs if text was provided
        if request.content_text:
            import re
            # Extract possible document codes mentioned in the text
            mentioned_codes = [c.upper() for c in re.findall(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b", request.content_text)]
            cand = None
            if mentioned_codes:
                cand = db.execute(select(OfficialDocument).where(OfficialDocument.document_code.in_(mentioned_codes))).scalars().first()

            if not cand:
                recent_docs = db.execute(select(OfficialDocument).order_by(desc(OfficialDocument.created_at)).limit(50)).scalars().all()
                for d in recent_docs:
                    if d.title.lower() in request.content_text.lower():
                        cand = d
                        break

            if cand:
                return HashVerificationResponse(
                    is_official_match=False,
                    matched_document_code=cand.document_code,
                    issuing_institution=cand.issuing_institution,
                    document_title=cand.title,
                    canonical_hash=cand.sha256_hash,
                    submitted_hash=target_hash,
                    verification_status="TAMPERED_SUSPECTED",
                    analytical_note=(
                        f"Warning: The content references official announcement '{cand.title}' "
                        f"(Code: {cand.document_code}), but its cryptographic hash does NOT match the authentic release. "
                        f"The text has likely been altered, manipulated, or selectively quoted."
                    ),
                )

        # 4. Unregistered / no match found
        return HashVerificationResponse(
            is_official_match=False,
            matched_document_code=None,
            issuing_institution=None,
            document_title=None,
            canonical_hash=None,
            submitted_hash=target_hash,
            verification_status="UNREGISTERED",
            analytical_note=(
                "No matching record with this cryptographic hash was found in the authenticated official registry. "
                "This announcement is either unauthenticated or has not been certified by an authorized electoral authority."
            ),
        )

    @staticmethod
    def get_by_code(db: Session, document_code: str) -> Optional[OfficialDocument]:
        """Lookup certified document by official identifier."""
        return db.execute(
            select(OfficialDocument).where(OfficialDocument.document_code == document_code.upper().strip())
        ).scalar_one_or_none()

    @staticmethod
    def search_documents(
        db: Session,
        query: Optional[str] = None,
        issuing_institution: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[OfficialDocument], int]:
        """Public search across certified announcements."""
        stmt = select(OfficialDocument)

        if issuing_institution:
            stmt = stmt.where(OfficialDocument.issuing_institution.ilike(f"%{issuing_institution}%"))
        if query:
            stmt = stmt.where(
                OfficialDocument.title.ilike(f"%{query}%")
                | OfficialDocument.summary.ilike(f"%{query}%")
                | OfficialDocument.document_code.ilike(f"%{query}%")
            )

        total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        items = list(db.execute(stmt.order_by(desc(OfficialDocument.publication_date)).offset(skip).limit(limit)).scalars().all())
        return items, total
