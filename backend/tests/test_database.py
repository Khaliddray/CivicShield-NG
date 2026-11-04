"""Integration test suite for Database Schema, Foreign Keys, and RBAC Seeding."""

import unittest
import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.core.init_db import seed_rbac
from backend.app.models import (
    User,
    Role,
    Permission,
    Report,
    UploadedEvidence,
    Claim,
    VerificationRecord,
    OfficialDocument,
    NarrativeCluster,
    Alert,
    AuditLog,
    SecurityEvent,
)
from backend.app.common.enums import (
    UserRoleType,
    ReportStatus,
    PriorityLevel,
    VerificationDecision,
    AlertSeverity,
    AlertCategory,
    AlertStatus as AlertStatusEnum,
)


class TestDatabaseModels(unittest.TestCase):
    """Test suite verifying all ORM entities and database operations."""

    @classmethod
    def setUpClass(cls):
        """Set up an in-memory test database for isolated testing."""
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.session = self.Session()
        # Seed RBAC for testing
        seed_rbac(self.session)

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_rbac_roles_seeded(self):
        """Verify all 5 standard roles and their permissions are seeded."""
        roles = self.session.execute(select(Role)).scalars().all()
        role_names = {r.name for r in roles}
        expected_roles = {
            UserRoleType.CITIZEN.value,
            UserRoleType.ANALYST.value,
            UserRoleType.VERIFICATION_OFFICER.value,
            UserRoleType.SECURITY_OFFICER.value,
            UserRoleType.ADMINISTRATOR.value,
        }
        self.assertTrue(expected_roles.issubset(role_names))

        admin_role = self.session.execute(select(Role).where(Role.name == UserRoleType.ADMINISTRATOR.value)).scalar_one()
        self.assertGreaterEqual(len(admin_role.permissions), 10)

    def test_user_creation_with_role(self):
        """Verify user creation, password hash storage, and role assignment."""
        user = User(
            email=f"test_{uuid.uuid4().hex[:8]}@civicshield.ng",
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$dummyhash",
            full_name="Fatima Bello",
            state_of_residence="Kano",
            is_active=True,
        )
        citizen_role = self.session.execute(select(Role).where(Role.name == UserRoleType.CITIZEN.value)).scalar_one()
        user.roles.append(citizen_role)

        self.session.add(user)
        self.session.commit()

        # Query back
        saved = self.session.execute(select(User).where(User.email == user.email)).scalar_one()
        self.assertEqual(saved.full_name, "Fatima Bello")
        self.assertTrue(saved.has_role(UserRoleType.CITIZEN.value))
        self.assertTrue(saved.has_permission("reports:create"))
        self.assertFalse(saved.has_permission("claims:verify"))

    def test_report_and_cascade_relationships(self):
        """Verify citizen report creation, evidence linking, and claim extraction."""
        report = Report(
            reference_number="CS-20270301-A1B2C3",
            title="Suspicious Announcement on Polling Unit Relocation",
            content_text="A WhatsApp broadcast claims all polling units in Ward 3 have moved.",
            encounter_location="WhatsApp Group",
            nigerian_state="Rivers",
            status=ReportStatus.SUBMITTED.value,
            priority=PriorityLevel.HIGH.value,
        )
        self.session.add(report)
        self.session.commit()

        # Add evidence item
        sample_hash = hashlib.sha256(b"sample evidence").hexdigest()
        evidence = UploadedEvidence(
            report_id=report.id,
            file_name="screenshot_sanitized.png",
            original_file_name="screenshot.png",
            file_type="IMAGE",
            mime_type="image/png",
            file_size_bytes=10240,
            storage_path="/uploads/test.png",
            sha256_hash=sample_hash,
        )
        self.session.add(evidence)

        # Add extracted claim
        claim = Claim(
            report_id=report.id,
            claim_text="Ward 3 polling units have moved to an undisclosed location.",
            category="INEC_OPERATIONS",
            ai_confidence_score=0.88,
            ai_suggested_status=VerificationDecision.UNVERIFIED.value,
            requires_human_review=True,
        )
        self.session.add(claim)
        self.session.commit()

        # Query report with relationships
        saved_report = self.session.execute(select(Report).where(Report.id == report.id)).scalar_one()
        self.assertEqual(len(saved_report.evidence_items), 1)
        self.assertEqual(len(saved_report.claims), 1)
        self.assertEqual(saved_report.claims[0].category, "INEC_OPERATIONS")

    def test_official_document_and_integrity_hash(self):
        """Verify official document integrity hash persistence."""
        content = "INEC confirms all Ward 3 polling units remain at their original designated gazetted centers."
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        doc = OfficialDocument(
            document_code="INEC-PUB-2027-042",
            issuing_institution="Independent National Electoral Commission",
            title="Official Statement on Ward 3 Polling Units",
            summary="Clarification on polling unit locations in Rivers State.",
            content_text=content,
            sha256_hash=content_hash,
            is_authenticated=True,
        )
        self.session.add(doc)
        self.session.commit()

        saved_doc = self.session.execute(select(OfficialDocument).where(OfficialDocument.document_code == "INEC-PUB-2027-042")).scalar_one()
        self.assertEqual(saved_doc.sha256_hash, content_hash)

    def test_chained_audit_log(self):
        """Verify tamper-evident hash chaining in audit logs."""
        prev_hash = "GENESIS_ROOT_HASH_000000000000000000000000000000000000000000000000"
        action = "USER_LOGIN"
        entry_content = f"{prev_hash}:{action}:admin@civicshield.ng"
        current_hash = hashlib.sha256(entry_content.encode("utf-8")).hexdigest()

        audit = AuditLog(
            action=action,
            entity_type="USER",
            entity_id="test-user-id",
            sha256_entry_hash=current_hash,
            previous_entry_hash=prev_hash,
        )
        self.session.add(audit)
        self.session.commit()

        saved_log = self.session.execute(select(AuditLog).where(AuditLog.id == audit.id)).scalar_one()
        self.assertEqual(saved_log.previous_entry_hash, prev_hash)
        self.assertEqual(saved_log.sha256_entry_hash, current_hash)


if __name__ == "__main__":
    unittest.main()
