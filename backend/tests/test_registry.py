"""Unit and Integration Test Suite for Official Verification Registry."""

import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.common.enums import UserRoleType


class TestRegistryModule(unittest.TestCase):
    """Test suite verifying document certification, SHA-256 hashing, tampering detection, and public search."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        # Create Verification Officer
        with SessionLocal() as db:
            cls.officer_email = f"officer_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.officer_pass = "VerificationPass123!"
            AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.officer_email,
                    "password": cls.officer_pass,
                    "full_name": "Senior Verification Officer",
                    "phone_number": "+2348011223344",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.VERIFICATION_OFFICER.value,
            )

            # Create regular Citizen
            cls.citizen_email = f"citizen_reg_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.citizen_pass = "CitizenPass123!"
            AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.citizen_email,
                    "password": cls.citizen_pass,
                    "full_name": "Citizen Verifier",
                    "phone_number": None,
                    "state_of_residence": "Lagos",
                })(),
                role_name=UserRoleType.CITIZEN.value,
            )

        # Obtain tokens
        officer_login = cls.client.post("/api/v1/auth/login", json={"email": cls.officer_email, "password": cls.officer_pass})
        cls.officer_token = officer_login.json()["data"]["access_token"]

        citizen_login = cls.client.post("/api/v1/auth/login", json={"email": cls.citizen_email, "password": cls.citizen_pass})
        cls.citizen_token = citizen_login.json()["data"]["access_token"]

    def test_01_officer_can_publish_official_document(self):
        """Test that an authorized Verification Officer can certify an official document."""
        code = f"INEC-NOTICE-01-{uuid.uuid4().hex[:6].upper()}"
        content = f"Official certified circular {code} on polling schedule nationwide."
        payload = {
            "document_code": code,
            "issuing_institution": "Independent National Electoral Commission",
            "title": f"Schedule Notice {code}",
            "summary": "Clarification on opening times across all 176,846 polling units.",
            "content_text": content,
            "source_url": "https://inecnigeria.org/gazette-2027-01",
        }
        response = self.client.post(
            "/api/v1/registry/documents",
            json=payload,
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["document_code"], code)
        self.assertEqual(len(data["data"]["sha256_hash"]), 64)

    def test_02_citizen_forbidden_from_certifying(self):
        """Test that a regular citizen cannot publish an official certified announcement."""
        payload = {
            "document_code": f"FAKE-{uuid.uuid4().hex[:6]}",
            "issuing_institution": "Bogus Agency",
            "title": "Unauthorized Release",
            "summary": "Citizen trying to certify announcement.",
            "content_text": "This should be forbidden.",
        }
        response = self.client.post(
            "/api/v1/registry/documents",
            json=payload,
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_03_verify_exact_content_match(self):
        """Test public verification when exact authentic content is submitted."""
        code = f"INEC-NOTICE-03-{uuid.uuid4().hex[:6].upper()}"
        content = f"Canonical declaration {code}: voting continues smoothly in all centers."
        
        # Certify document
        reg_res = self.client.post(
            "/api/v1/registry/documents",
            json={
                "document_code": code,
                "issuing_institution": "INEC",
                "title": f"Declaration {code}",
                "summary": "Official certified release summary for polling verification.",
                "content_text": content,
            },
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(reg_res.status_code, 201)

        # Public user verifies the content
        response = self.client.post(
            "/api/v1/registry/verify",
            json={"content_text": content},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["is_official_match"])
        self.assertEqual(data["verification_status"], "EXACT_MATCH")
        self.assertEqual(data["matched_document_code"], code)

    def test_04_tampered_content_detection(self):
        """Test detection of altered text referencing the certified announcement."""
        code = f"INEC-NOTICE-04-{uuid.uuid4().hex[:6].upper()}"
        authentic_content = f"Official Announcement {code}: Polls close strictly at 2:30 PM."

        # Certify document
        reg_res = self.client.post(
            "/api/v1/registry/documents",
            json={
                "document_code": code,
                "issuing_institution": "INEC",
                "title": f"Poll Hours {code}",
                "summary": "Official certified release summary for poll closing times.",
                "content_text": authentic_content,
            },
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(reg_res.status_code, 201)

        # Attacker modifies "Polls close strictly at 2:30 PM" to "Polls are cancelled"
        tampered_content = (
            f"Regarding official notice {code}, polls are cancelled today."
        )

        response = self.client.post(
            "/api/v1/registry/verify",
            json={"content_text": tampered_content},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertFalse(data["is_official_match"])
        self.assertEqual(data["verification_status"], "TAMPERED_SUSPECTED")
        self.assertIn("altered", data["analytical_note"].lower())

    def test_05_unregistered_hash_verification(self):
        """Test verification of random uncertified text."""
        response = self.client.post(
            "/api/v1/registry/verify",
            json={"content_text": f"Random unverified rumor {uuid.uuid4().hex} with no official record."},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertFalse(data["is_official_match"])
        self.assertEqual(data["verification_status"], "UNREGISTERED")

    def test_06_public_search_and_document_inspection(self):
        """Test public keyword search and document detail retrieval."""
        code = f"INEC-GAZETTE-06-{uuid.uuid4().hex[:6].upper()}"
        content = f"Authentic collation protocols {code} text representation."
        
        reg_res = self.client.post(
            "/api/v1/registry/documents",
            json={
                "document_code": code,
                "issuing_institution": "Independent National Electoral Commission",
                "title": f"Gazette on Collation {code}",
                "summary": "Detailed collation protocols.",
                "content_text": content,
            },
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(reg_res.status_code, 201)

        # Search
        search_res = self.client.get(f"/api/v1/registry/search?q={code}")
        self.assertEqual(search_res.status_code, 200)
        self.assertGreaterEqual(search_res.json()["data"]["pagination"]["total_count"], 1)

        # Detail inspect
        detail_res = self.client.get(f"/api/v1/registry/documents/{code}")
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.json()["data"]["document_code"], code)
        self.assertGreaterEqual(len(detail_res.json()["data"]["versions"]), 1)


if __name__ == "__main__":
    unittest.main()
