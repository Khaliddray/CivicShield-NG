"""Unit and Integration Test Suite for Institutional Human Verification Workflow."""

import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.modules.reporting.service import ReportingService
from backend.app.modules.reporting.schemas import ReportCreateRequest
from backend.app.modules.registry.service import RegistryService
from backend.app.modules.registry.schemas import DocumentCreateRequest
from backend.app.common.enums import UserRoleType, VerificationDecision, ReportStatus


class TestVerificationModule(unittest.TestCase):
    """Test suite verifying verification queue ordering, decision recording, and RBAC authorization."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            # Create Verification Officer
            cls.officer_email = f"officer_ver_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.password = "OfficerPass123!"
            cls.officer = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.officer_email,
                    "password": cls.password,
                    "full_name": "Institutional Verification Lead",
                    "phone_number": "+2348077889900",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.VERIFICATION_OFFICER.value,
            )

            # Create regular citizen
            cls.citizen_email = f"citizen_ver_{uuid.uuid4().hex[:8]}@civicshield.ng"
            AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.citizen_email,
                    "password": cls.password,
                    "full_name": "Regular Citizen",
                    "phone_number": None,
                    "state_of_residence": "Oyo",
                })(),
                role_name=UserRoleType.CITIZEN.value,
            )

            # Register an official document to link
            uid = uuid.uuid4().hex[:6]
            cls.doc = RegistryService.register_document(
                db=db,
                request=DocumentCreateRequest(
                    document_code=f"INEC-VER-REF-{uid.upper()}",
                    issuing_institution="Independent National Electoral Commission",
                    title=f"Gazette on Polling Unit Accreditation {uid}",
                    summary="INEC confirms BVAS is strictly required across all polling centers.",
                    content_text=f"The Commission reiterates that accreditation without BVAS is strictly invalid {uid}.",
                ),
                authorized_user_id=cls.officer.id,
            )

        # Login users
        officer_login = cls.client.post("/api/v1/auth/login", json={"email": cls.officer_email, "password": cls.password})
        cls.officer_token = officer_login.json()["data"]["access_token"]

        citizen_login = cls.client.post("/api/v1/auth/login", json={"email": cls.citizen_email, "password": cls.password})
        cls.citizen_token = citizen_login.json()["data"]["access_token"]

    def setUp(self):
        # Create a sample report with pending claim
        with SessionLocal() as db:
            self.report = ReportingService.submit_report(
                db=db,
                report_data=ReportCreateRequest(
                    title=f"Claim on manual voting without BVAS {uuid.uuid4().hex[:6]}",
                    content_text="Social media post falsely claims BVAS is no longer required in Ward 5.",
                    nigerian_state="Rivers",
                ),
            )
            self.claim_id = self.report.claims[0].id
            self.report_id = self.report.id

    def test_01_officer_can_fetch_queue(self):
        """Test that authorized officer retrieves pending verification queue."""
        response = self.client.get(
            "/api/v1/verification/queue",
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 1)
        # Check queue item fields
        item = next(i for i in data["data"] if i["claim_id"] == self.claim_id)
        self.assertEqual(item["report_reference"], self.report.reference_number)

    def test_02_citizen_forbidden_from_queue(self):
        """Test that regular citizens cannot access the verification review queue."""
        response = self.client.get(
            "/api/v1/verification/queue",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_03_record_contradicted_decision(self):
        """Test recording an authoritative CONTRADICTED decision with official document citation."""
        payload = {
            "claim_id": self.claim_id,
            "decision": VerificationDecision.CONTRADICTED.value,
            "justification_notes": "Official INEC Gazette confirms that BVAS remains strictly mandatory for all voting under Electoral Act 2022.",
            "public_clarification": "The assertion that BVAS has been discarded is false. Accreditation without BVAS is legally invalid.",
            "official_document_id": self.doc.id,
            "evidence_sources_consulted": ["https://inecnigeria.org/electoral-act-2022"],
        }
        response = self.client.post(
            "/api/v1/verification/decisions",
            json=payload,
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        record = data["data"]
        self.assertEqual(record["decision"], "CONTRADICTED")
        self.assertEqual(record["official_document_id"], self.doc.id)

        # Inspect claim state
        claim_res = self.client.get(f"/api/v1/verification/claims/{self.claim_id}")
        self.assertEqual(claim_res.status_code, 200)
        claim_data = claim_res.json()["data"]
        self.assertEqual(claim_data["ai_suggested_status"], "CONTRADICTED")
        self.assertFalse(claim_data["requires_human_review"])
        self.assertEqual(len(claim_data["verifications"]), 1)

        # Inspect parent report status
        track_res = self.client.get(f"/api/v1/reports/track/{self.report.reference_number}")
        self.assertEqual(track_res.status_code, 200)
        self.assertEqual(track_res.json()["data"]["status"], ReportStatus.RESOLVED.value)

    def test_04_citizen_forbidden_from_recording_decisions(self):
        """Test that a regular citizen cannot record a verification decision."""
        payload = {
            "claim_id": self.claim_id,
            "decision": VerificationDecision.VERIFIED.value,
            "justification_notes": "Attempting unauthorized citizen verification.",
            "public_clarification": "Attempting unauthorized clarification.",
        }
        response = self.client.post(
            "/api/v1/verification/decisions",
            json=payload,
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
