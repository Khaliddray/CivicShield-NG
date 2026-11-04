"""Integration and Unit Test Suite for Citizen Reporting and File Uploads."""

import unittest
import io
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.models import User, Role
from backend.app.modules.auth.service import AuthService
from backend.app.common.enums import UserRoleType


class TestReportingModule(unittest.TestCase):
    """Test suite verifying citizen submissions, tracking, evidence handling, and RBAC isolation."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        # Create an analyst user for institutional reviews
        with SessionLocal() as db:
            cls.analyst_email = f"analyst_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.password = "OfficerPass123!"
            cls.analyst = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.analyst_email,
                    "password": cls.password,
                    "full_name": "Senior Analyst",
                    "phone_number": "+2348099887766",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.ANALYST.value,
            )

        # Obtain analyst token
        login_res = cls.client.post("/api/v1/auth/login", json={"email": cls.analyst_email, "password": cls.password})
        cls.analyst_token = login_res.json()["data"]["access_token"]

    def setUp(self):
        self.unique = uuid.uuid4().hex[:6]

    def test_01_anonymous_submission_success(self):
        """Test anonymous submission of a suspicious announcement."""
        form_data = {
            "title": f"Fake INEC circular circulating on social media {self.unique}",
            "content_text": "A circular claims voting in Ward 4 has been cancelled and moved to tomorrow.",
            "encounter_location": "WhatsApp",
            "nigerian_state": "Kaduna",
        }
        response = self.client.post("/api/v1/reports", data=form_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        ref = data["data"]["reference_number"]
        self.assertTrue(ref.startswith("CS-"))
        self.assertEqual(data["data"]["nigerian_state"], "Kaduna")
        self.assertEqual(data["data"]["status"], "SUBMITTED")

    def test_02_track_report_publicly(self):
        """Test public tracking endpoint using the returned reference code."""
        form_data = {
            "title": f"Purported polling unit changes in Ward 2 {self.unique}",
            "content_text": "Social media post claiming all voters should go to local council headquarters instead.",
            "nigerian_state": "Lagos",
        }
        create_res = self.client.post("/api/v1/reports", data=form_data)
        ref_number = create_res.json()["data"]["reference_number"]

        # Track anonymously
        track_res = self.client.get(f"/api/v1/reports/track/{ref_number}")
        self.assertEqual(track_res.status_code, 200)
        track_data = track_res.json()
        self.assertTrue(track_data["success"])
        self.assertEqual(track_data["data"]["reference_number"], ref_number)
        self.assertEqual(track_data["data"]["title"], form_data["title"])

    def test_03_track_nonexistent_report(self):
        """Test tracking with an unknown reference number returns 404."""
        response = self.client.get("/api/v1/reports/track/CS-99999999-NOTFOUND")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_04_submission_with_image_evidence(self):
        """Test report submission with attached image file."""
        form_data = {
            "title": f"Screenshot of altered electoral results flyer {self.unique}",
            "content_text": "Flyer falsely displaying premature vote counts for Kano Central.",
            "nigerian_state": "Kano",
        }
        # Fake PNG file
        fake_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        files = [
            ("files", ("flyer_evidence.png", io.BytesIO(fake_image_bytes), "image/png"))
        ]

        response = self.client.post("/api/v1/reports", data=form_data, files=files)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["data"]["evidence_count"], 1)

    def test_05_submission_disallowed_file_type(self):
        """Test rejection when submitting an unsupported or dangerous MIME type."""
        form_data = {
            "title": f"Malicious attachment test {self.unique}",
            "content_text": "Attempting to upload executable disguised as report evidence.",
            "nigerian_state": "Delta",
        }
        files = [
            ("files", ("malware.exe", io.BytesIO(b"MZ\x90\x00..."), "application/x-msdownload"))
        ]
        response = self.client.post("/api/v1/reports", data=form_data, files=files)
        self.assertEqual(response.status_code, 422)

    def test_06_rbac_citizen_blocked_from_command_centre(self):
        """Test that regular citizens cannot access the full institutional reports queue."""
        # Register a citizen
        citizen_email = f"citizen_{self.unique}@civicshield.ng"
        self.client.post("/api/v1/auth/register", json={
            "email": citizen_email,
            "password": "CitizenPass123!",
            "full_name": "Citizen One",
        })
        login_res = self.client.post("/api/v1/auth/login", json={"email": citizen_email, "password": "CitizenPass123!"})
        citizen_token = login_res.json()["data"]["access_token"]

        # Citizen attempts to view all institutional reports
        response = self.client.get("/api/v1/reports", headers={"Authorization": f"Bearer {citizen_token}"})
        self.assertEqual(response.status_code, 403)

    def test_07_analyst_can_access_command_centre(self):
        """Test that an Analyst can list all reports and inspect details."""
        response = self.client.get("/api/v1/reports", headers={"Authorization": f"Bearer {self.analyst_token}"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("items", data["data"])
        self.assertIn("pagination", data["data"])


if __name__ == "__main__":
    unittest.main()
