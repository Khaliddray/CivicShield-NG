"""Unit and Integration Test Suite for Early Warning and Notification Engine."""

import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.modules.reporting.service import ReportingService
from backend.app.modules.reporting.schemas import ReportCreateRequest
from backend.app.modules.verification.service import VerificationService
from backend.app.modules.verification.schemas import VerificationDecisionCreate
from backend.app.common.enums import UserRoleType, VerificationDecision, AlertSeverity, AlertCategory, AlertScope


class TestNotificationsModule(unittest.TestCase):
    """Test suite verifying early warning drafting, dual-key approval, geographical filtering, and delivery tracking."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            # Create Administrator
            cls.admin_email = f"admin_alert_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.admin_pass = "AdminPass123!"
            cls.admin = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.admin_email,
                    "password": cls.admin_pass,
                    "full_name": "Lead Platform Admin",
                    "phone_number": "+2348011998877",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.ADMINISTRATOR.value,
            )

            # Create Verification Officer
            cls.officer_email = f"officer_alert_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.officer_pass = "OfficerPass123!"
            cls.officer = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.officer_email,
                    "password": cls.officer_pass,
                    "full_name": "Verification Officer Alerts",
                    "phone_number": "+2348022334455",
                    "state_of_residence": "Kaduna",
                })(),
                role_name=UserRoleType.VERIFICATION_OFFICER.value,
            )

            # Create Citizen in Kaduna
            cls.citizen_email = f"citizen_kaduna_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.citizen_pass = "CitizenPass123!"
            AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.citizen_email,
                    "password": cls.citizen_pass,
                    "full_name": "Kaduna Resident",
                    "phone_number": None,
                    "state_of_residence": "Kaduna",
                })(),
                role_name=UserRoleType.CITIZEN.value,
            )

            # Create a report and record an authoritative CONTRADICTED decision
            uid = uuid.uuid4().hex[:6]
            report = ReportingService.submit_report(
                db=db,
                report_data=ReportCreateRequest(
                    title=f"Viral rumor on voting cancellation {uid}",
                    content_text=f"A viral message claims voting is cancelled across Kaduna Central {uid}.",
                    nigerian_state="Kaduna",
                ),
            )
            cls.v_record = VerificationService.record_decision(
                db=db,
                payload=VerificationDecisionCreate(
                    claim_id=report.claims[0].id,
                    decision=VerificationDecision.CONTRADICTED,
                    justification_notes="INEC State Resident Electoral Commissioner confirms voting is ongoing normally.",
                    public_clarification="Voting in Kaduna Central has NOT been cancelled. All centers are active.",
                ),
                officer_user_id=cls.officer.id,
            )

        # Log in users
        admin_login = cls.client.post("/api/v1/auth/login", json={"email": cls.admin_email, "password": cls.admin_pass})
        cls.admin_token = admin_login.json()["data"]["access_token"]

        officer_login = cls.client.post("/api/v1/auth/login", json={"email": cls.officer_email, "password": cls.officer_pass})
        cls.officer_token = officer_login.json()["data"]["access_token"]

        citizen_login = cls.client.post("/api/v1/auth/login", json={"email": cls.citizen_email, "password": cls.citizen_pass})
        cls.citizen_token = citizen_login.json()["data"]["access_token"]

    def test_01_confirmed_misinformation_requires_verified_record(self):
        """Test invariant: Confirmed misinformation alert cannot be created without a valid CONTRADICTED record."""
        payload = {
            "title": "Unsubstantiated False Claim Alert",
            "summary": "Attempting to issue confirmed misinformation warning without verification evidence.",
            "full_clarification": "This attempt must be blocked by the system safety invariants.",
            "severity": AlertSeverity.HIGH.value,
            "category": AlertCategory.CONFIRMED_MISINFORMATION.value,
            "verification_record_id": None,  # Missing mandatory finding
        }
        response = self.client.post(
            "/api/v1/alerts",
            json=payload,
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_02_draft_alert_with_verified_finding(self):
        """Test successfully drafting an early warning backed by a verified finding."""
        payload = {
            "title": "False Announcement: Voting in Kaduna Central is NOT Cancelled",
            "summary": "Viral messages claiming election cancellation in Kaduna are completely false.",
            "full_clarification": "The Resident Electoral Commissioner has confirmed that all polling units remain open as scheduled.",
            "severity": AlertSeverity.HIGH.value,
            "category": AlertCategory.CONFIRMED_MISINFORMATION.value,
            "target_scope": AlertScope.STATE_SPECIFIC.value,
            "target_states": ["Kaduna"],
            "verification_record_id": self.v_record.id,
        }
        response = self.client.post(
            "/api/v1/alerts",
            json=payload,
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        self.assertEqual(data["status"], "PENDING_APPROVAL")
        self.assertTrue(data["alert_reference"].startswith("WARN-"))

        # Invariant: Unapproved alert must NOT appear in public feed
        public_res = self.client.get("/api/v1/alerts/active")
        self.assertFalse(any(a["id"] == data["id"] for a in public_res.json()["data"]))

    def test_03_approve_and_broadcast_alert(self):
        """Test approving and broadcasting alert to targeted population."""
        # Draft first
        draft_res = self.client.post(
            "/api/v1/alerts",
            json={
                "title": f"Official Clarification on Polling Units {uuid.uuid4().hex[:6]}",
                "summary": "Verified clarification regarding designated voting locations in Kaduna.",
                "full_clarification": "Official guidance confirming all designated gazetted centers remain active.",
                "severity": AlertSeverity.HIGH.value,
                "category": AlertCategory.CONFIRMED_MISINFORMATION.value,
                "target_scope": AlertScope.STATE_SPECIFIC.value,
                "target_states": ["Kaduna"],
                "verification_record_id": self.v_record.id,
            },
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        alert_id = draft_res.json()["data"]["id"]

        # Admin approves
        approve_res = self.client.post(
            f"/api/v1/alerts/{alert_id}/approve",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(approve_res.status_code, 200)
        self.assertEqual(approve_res.json()["data"]["status"], "ACTIVE")

        # Now appears in public active feed for Kaduna
        kaduna_feed = self.client.get("/api/v1/alerts/active?state=Kaduna")
        self.assertEqual(kaduna_feed.status_code, 200)
        self.assertTrue(any(a["id"] == alert_id for a in kaduna_feed.json()["data"]))

        # Does NOT appear when querying an unrelated state (e.g. Lagos)
        lagos_feed = self.client.get("/api/v1/alerts/active?state=Lagos")
        self.assertEqual(lagos_feed.status_code, 200)
        self.assertFalse(any(a["id"] == alert_id for a in lagos_feed.json()["data"]))

    def test_04_withdraw_alert(self):
        """Test withdrawing an active alert with justification notes."""
        # Draft and approve
        res = self.client.post(
            "/api/v1/alerts",
            json={
                "title": f"Superseded Alert {uuid.uuid4().hex[:6]}",
                "summary": "This alert will be withdrawn following new operational updates.",
                "full_clarification": "Initial clarification issued prior to subsequent operational changes.",
                "severity": AlertSeverity.MEDIUM.value,
                "category": AlertCategory.OFFICIAL_CLARIFICATION.value,
                "target_scope": AlertScope.NATIONAL.value,
            },
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        alert_id = res.json()["data"]["id"]
        self.client.post(f"/api/v1/alerts/{alert_id}/approve", headers={"Authorization": f"Bearer {self.admin_token}"})

        # Withdraw
        withdraw_res = self.client.post(
            f"/api/v1/alerts/{alert_id}/withdraw",
            json={"withdrawal_reason": "Superseded by national press release from INEC headquarters."},
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(withdraw_res.status_code, 200)
        self.assertEqual(withdraw_res.json()["data"]["status"], "WITHDRAWN")

        # No longer in public active feed
        public_feed = self.client.get("/api/v1/alerts/active")
        self.assertFalse(any(a["id"] == alert_id for a in public_feed.json()["data"]))

    def test_05_citizen_preferences(self):
        """Test citizen updating geographical and severity notification preferences."""
        get_res = self.client.get("/api/v1/alerts/preferences", headers={"Authorization": f"Bearer {self.citizen_token}"})
        self.assertEqual(get_res.status_code, 200)

        update_payload = {
            "preferred_states": ["Kaduna", "Kano"],
            "receive_critical_alerts": True,
            "receive_medium_alerts": False,
        }
        put_res = self.client.put(
            "/api/v1/alerts/preferences",
            json=update_payload,
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(put_res.status_code, 200)
        data = put_res.json()["data"]
        self.assertIn("Kaduna", data["preferred_states"])
        self.assertIn("Kano", data["preferred_states"])
        self.assertFalse(data["receive_medium_alerts"])


if __name__ == "__main__":
    unittest.main()
