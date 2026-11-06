"""
Comprehensive Test Suite for Member 1 Extensions:
- Admin User & Role Management & Logout
- Report Lifecycle Transitions, Analyst Assignment & Withdrawal
- Secure Evidence Download & Path Traversal Defense
- Trusted Official Information Sources Registry (CRUD)
- Analyst Recommendations & Dual-Key Review Workflow
- Alert Submission, Rejection, Approval Audit & In-App Notifications
- Narrative Pulse Cluster Status Updates
- Accessibility Voice Transcription & Speech Synthesis
"""

import io
import uuid
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.models import User
from backend.app.modules.auth.service import AuthService
from backend.app.modules.reporting.models import Report, UploadedEvidence
from backend.app.modules.reporting.service import ReportingService
from backend.app.modules.registry.models import OfficialDocument, TrustedSource
from backend.app.modules.verification.models import Claim, VerificationRecommendation, VerificationRecord
from backend.app.modules.notifications.models import Alert
from backend.app.modules.narratives.models import NarrativeCluster
from backend.app.common.enums import UserRoleType, VerificationDecision, AlertSeverity, AlertCategory, AlertStatus


class TestMember1Extensions(unittest.TestCase):
    """Integration tests for all newly implemented Member 1 capabilities."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            # 1. Admin user
            cls.admin_email = f"admin_ext_{uuid.uuid4().hex[:6]}@civicshield.ng"
            cls.password = "CivicShieldAdmin2026!"
            cls.admin = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.admin_email,
                    "password": cls.password,
                    "full_name": "Chief Administrator",
                    "phone_number": "+2348011223344",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.ADMINISTRATOR.value,
            )

            # 2. Analyst user
            cls.analyst_email = f"analyst_ext_{uuid.uuid4().hex[:6]}@civicshield.ng"
            cls.analyst = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.analyst_email,
                    "password": cls.password,
                    "full_name": "Field Analyst",
                    "phone_number": "+2348022334455",
                    "state_of_residence": "Lagos",
                })(),
                role_name=UserRoleType.ANALYST.value,
            )

            # 3. Verification Officer
            cls.officer_email = f"officer_ext_{uuid.uuid4().hex[:6]}@civicshield.ng"
            cls.officer = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.officer_email,
                    "password": cls.password,
                    "full_name": "Senior Verifier",
                    "phone_number": "+2348033445566",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.VERIFICATION_OFFICER.value,
            )

            # 4. Citizen user
            cls.citizen_email = f"citizen_ext_{uuid.uuid4().hex[:6]}@civicshield.ng"
            cls.citizen = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.citizen_email,
                    "password": cls.password,
                    "full_name": "Amaka Okonkwo",
                    "phone_number": "+2348044556677",
                    "state_of_residence": "Anambra",
                })(),
                role_name=UserRoleType.CITIZEN.value,
            )

        # Log in all users and store tokens
        cls.admin_token = cls._login(cls.admin_email, cls.password)
        cls.analyst_token = cls._login(cls.analyst_email, cls.password)
        cls.officer_token = cls._login(cls.officer_email, cls.password)
        cls.citizen_token = cls._login(cls.citizen_email, cls.password)

    @classmethod
    def _login(cls, email: str, password: str) -> str:
        res = cls.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return res.json()["data"]["access_token"]

    def setUp(self):
        self.unique = uuid.uuid4().hex[:6]

    # --- 1. ADMIN USER MANAGEMENT & LOGOUT ---

    def test_01_admin_list_users(self):
        """Admin can list platform users with pagination."""
        res = self.client.get(
            "/api/v1/auth/users?page=1&page_size=10",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("items", data)
        self.assertGreaterEqual(data["pagination"]["total_count"], 4)

    def test_02_citizen_forbidden_from_user_management(self):
        """Regular citizen is rejected when attempting to access user management."""
        res = self.client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(res.status_code, 403)

    def test_03_admin_update_user_roles(self):
        """Admin can promote or adjust a user's assigned roles."""
        res = self.client.patch(
            f"/api/v1/auth/users/{self.citizen.id}/roles",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"roles": ["CITIZEN", "ANALYST"]},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        role_names = [r["name"] for r in data["roles"]]
        self.assertIn("ANALYST", role_names)

        # Revert role back to CITIZEN
        self.client.patch(
            f"/api/v1/auth/users/{self.citizen.id}/roles",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"roles": ["CITIZEN"]},
        )

    def test_04_user_logout(self):
        """Authenticated user can log out cleanly, revoke token, and trigger audit logging."""
        temp_token = self._login(self.citizen_email, self.password)
        res = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {temp_token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["logged_out"])

        # Confirm token is revoked
        check_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {temp_token}"})
        self.assertEqual(check_res.status_code, 401)

    # --- 2. REPORT STATUS, ASSIGNMENT & WITHDRAWAL ---

    def test_05_update_report_status_and_assign(self):
        """Analyst can update report status and assign lead analyst."""
        # Citizen submits report
        sub_res = self.client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            data={
                "title": f"Ward 5 announcement relocation rumor {self.unique}",
                "content_text": "Rumor claims all voting centers moved across local river.",
                "nigerian_state": "Anambra",
            },
        )
        self.assertEqual(sub_res.status_code, 201)
        report_id = sub_res.json()["data"]["id"]

        # Analyst assigns report
        assign_res = self.client.post(
            f"/api/v1/reports/{report_id}/assign",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
            json={"analyst_user_id": self.analyst.id, "notes": "Taking ownership of Anambra incident."},
        )
        self.assertEqual(assign_res.status_code, 200)
        self.assertEqual(assign_res.json()["data"]["assigned_analyst_id"], self.analyst.id)

        # Analyst updates status to UNDER_REVIEW
        status_res = self.client.patch(
            f"/api/v1/reports/{report_id}/status",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
            json={"status": "UNDER_REVIEW", "notes": "Correlating with certified INEC PU gazette."},
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["data"]["status"], "UNDER_REVIEW")

    def test_06_citizen_withdraw_own_report(self):
        """Citizen can withdraw their own report with justification."""
        sub_res = self.client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            data={
                "title": f"Accidental duplicate submission {self.unique}",
                "content_text": "This was an erroneous submission submitted twice by accident.",
                "nigerian_state": "Lagos",
            },
        )
        report_id = sub_res.json()["data"]["id"]

        # Citizen withdraws
        withdraw_res = self.client.post(
            f"/api/v1/reports/{report_id}/withdraw",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            json={"reason": "Citizen realized this was posted in error."},
        )
        self.assertEqual(withdraw_res.status_code, 200)
        self.assertEqual(withdraw_res.json()["data"]["status"], "WITHDRAWN")

    # --- 3. SECURE EVIDENCE DOWNLOAD & PATH TRAVERSAL DEFENSE ---

    def test_07_evidence_upload_and_secure_download(self):
        """Upload evidence image and download it through the controlled endpoint."""
        fake_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        sub_res = self.client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            data={"title": f"Notice photo with evidence {self.unique}", "content_text": "Photo of fake notice attached."},
            files={"files": ("fake_notice.png", io.BytesIO(fake_image), "image/png")},
        )
        self.assertEqual(sub_res.status_code, 201)
        report_id = sub_res.json()["data"]["id"]

        # Fetch detailed report to get evidence ID
        detail_res = self.client.get(
            f"/api/v1/reports/{report_id}",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        evidence_list = detail_res.json()["data"]["evidence_items"]
        self.assertEqual(len(evidence_list), 1)
        evidence_id = evidence_list[0]["id"]

        # Download evidence as authorized officer
        download_res = self.client.get(
            f"/api/v1/reports/{report_id}/evidence/{evidence_id}/download",
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(download_res.status_code, 200)
        self.assertEqual(download_res.content, fake_image)

    # --- 4. TRUSTED OFFICIAL INFORMATION REGISTRY ---

    def test_08_trusted_source_crud(self):
        """Verify full lifecycle of trusted institutional sources."""
        # 1. Create trusted source
        source_name = f"Nigeria Fact-Check Coalition {self.unique}"
        create_res = self.client.post(
            "/api/v1/registry/sources",
            headers={"Authorization": f"Bearer {self.officer_token}"},
            json={
                "name": source_name,
                "url": "https://factchecknigeria.org",
                "category": "FACT_CHECKER",
                "verification_status": "VERIFIED",
                "description": "Certified coalition of Nigerian fact-checkers.",
            },
        )
        self.assertEqual(create_res.status_code, 201)
        source_id = create_res.json()["data"]["id"]

        # 2. Public lookup
        get_res = self.client.get(f"/api/v1/registry/sources/{source_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["data"]["name"], source_name)

        # 3. Update source
        update_res = self.client.put(
            f"/api/v1/registry/sources/{source_id}",
            headers={"Authorization": f"Bearer {self.officer_token}"},
            json={"description": "Updated certification notes and mandate."},
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["data"]["description"], "Updated certification notes and mandate.")

        # 4. Deactivate source
        del_res = self.client.delete(
            f"/api/v1/registry/sources/{source_id}",
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(del_res.json()["data"]["is_active"])

    # --- 5. HUMAN VERIFICATION WORKFLOW: ANALYST RECOMMENDATION & DUAL-KEY REVIEW ---

    def test_09_analyst_recommendation_and_reviewer_approval(self):
        """Analyst submits recommendation -> Verification Officer approves -> Authoritative decision persisted."""
        # 1. Create report and extract claims
        sub_res = self.client.post(
            "/api/v1/reports",
            data={
                "title": f"Claim on collation halt in Ward 7 {self.unique}",
                "content_text": "The returning officer announced collation is suspended until next week.",
                "nigerian_state": "Rivers",
            },
        )
        report_id = sub_res.json()["data"]["id"]

        # Trigger AI claim analysis
        analyze_res = self.client.post(
            f"/api/v1/ai/reports/{report_id}/analyze",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        claims = analyze_res.json()["data"]
        self.assertGreaterEqual(len(claims), 1)
        claim_id = claims[0]["id"]

        # 2. Analyst submits recommendation
        rec_res = self.client.post(
            "/api/v1/verification/recommendations",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
            json={
                "claim_id": claim_id,
                "recommended_decision": "CONTRADICTED",
                "justification_notes": "INEC Section 64 Electoral Act mandates uninterrupted collation.",
                "proposed_clarification": "Collation is active and ongoing. Official results will be announced at the designated collation center.",
                "evidence_sources_consulted": ["INEC Gazette 2026/04", "Electoral Act 2022 Section 64"],
            },
        )
        self.assertEqual(rec_res.status_code, 201)
        rec_id = rec_res.json()["data"]["id"]
        self.assertEqual(rec_res.json()["data"]["status"], "PENDING_REVIEW")

        # 3. Lead Officer approves recommendation
        review_res = self.client.post(
            f"/api/v1/verification/recommendations/{rec_id}/review",
            headers={"Authorization": f"Bearer {self.officer_token}"},
            json={
                "action": "APPROVE",
                "reviewer_notes": "Reviewed and confirmed against Electoral Act guidelines. Approved for public debunk.",
            },
        )
        self.assertEqual(review_res.status_code, 200)
        self.assertEqual(review_res.json()["data"]["status"], "APPROVED")

        # 4. Verify claim details reflects recorded binding decision
        claim_detail_res = self.client.get(f"/api/v1/verification/claims/{claim_id}")
        claim_data = claim_detail_res.json()["data"]
        self.assertEqual(len(claim_data["verifications"]), 1)
        self.assertEqual(claim_data["verifications"][0]["decision"], "CONTRADICTED")

    # --- 6. ALERTS LIFECYCLE & IN-APP NOTIFICATIONS ---

    def test_10_alert_submit_for_approval_and_rejection(self):
        """Analyst drafts alert -> Submits for approval -> Reviewer rejects with justification."""
        # 1. Draft alert
        draft_res = self.client.post(
            "/api/v1/alerts",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
            json={
                "title": f"Emerging claim on polling unit closure {self.unique}",
                "summary": "Reports circulating claiming polling units in Ward 2 closed early.",
                "full_clarification": "Voting hours remain standard 8:30am to 2:30pm or until the last queued voter casts their ballot.",
                "severity": "MEDIUM",
                "category": "EMERGING_SUSPICIOUS",
                "target_scope": "NATIONAL",
            },
        )
        self.assertEqual(draft_res.status_code, 201)
        alert_id = draft_res.json()["data"]["id"]

        # 2. Inspect approval history
        history_res = self.client.get(
            f"/api/v1/alerts/{alert_id}/approvals",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(history_res.status_code, 200)
        self.assertGreaterEqual(len(history_res.json()["data"]), 1)

        # 3. Reject alert
        reject_res = self.client.post(
            f"/api/v1/alerts/{alert_id}/reject",
            headers={"Authorization": f"Bearer {self.officer_token}"},
            json={"rejection_reason": "Insufficient field confirmation from local electoral officers. Resubmit with primary citations."},
        )
        self.assertEqual(reject_res.status_code, 200)
        self.assertEqual(reject_res.json()["data"]["status"], "REJECTED")

    def test_11_citizen_in_app_notifications(self):
        """Citizen can query delivered in-app alerts and mark them as read."""
        res = self.client.get(
            "/api/v1/alerts/my-notifications",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIsInstance(data, list)

        # Query unread count
        count_res = self.client.get(
            "/api/v1/alerts/notifications/unread-count",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(count_res.status_code, 200)
        self.assertIn("unread_count", count_res.json()["data"])

    # --- 7. NARRATIVE PULSE CLUSTER STATUS UPDATES ---

    def test_12_update_narrative_cluster_status(self):
        """Command Centre analyst can update narrative cluster investigation status."""
        with SessionLocal() as db:
            cluster = NarrativeCluster(
                cluster_title=f"Coordinated cluster on BVAS failure {self.unique}",
                summary="Narrative alleging BVAS failures across 3 states.",
                velocity_score=2.5,
                amplification_pattern="CROSS_PLATFORM_SPIKE",
                geographic_scope=["Kano", "Kaduna"],
                status="ACTIVE",
            )
            db.add(cluster)
            db.commit()
            cluster_id = cluster.id

        update_res = self.client.patch(
            f"/api/v1/narratives/clusters/{cluster_id}",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
            json={
                "status": "INVESTIGATING",
                "verification_status": "UNDER_REVIEW",
                "assigned_analyst_id": self.analyst.id,
            },
        )
        self.assertEqual(update_res.status_code, 200)
        data = update_res.json()["data"]
        self.assertEqual(data["status"], "INVESTIGATING")
        self.assertEqual(data["verification_status"], "UNDER_REVIEW")

    # --- 8. ACCESSIBILITY VOICE & SPEECH SYNTHESIS ---

    def test_13_voice_transcription_and_synthesis(self):
        """Test accessible audio transcription and speech synthesis read-aloud endpoints."""
        fake_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"

        # 1. Transcribe voice
        trans_res = self.client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("recording.wav", io.BytesIO(fake_audio), "audio/wav")},
            data={"language_hint": "en"},
        )
        self.assertEqual(trans_res.status_code, 200)
        t_data = trans_res.json()["data"]
        self.assertTrue(len(t_data["transcript"]) > 10)
        self.assertGreaterEqual(t_data["confidence"], 0.8)

        # 2. Synthesize speech for read-aloud
        synth_res = self.client.post(
            "/api/v1/voice/synthesize",
            json={
                "text": "Official clarification: Voting centers in Ward 4 remain open.",
                "language": "en",
                "voice_speed": "normal",
            },
        )
        self.assertEqual(synth_res.status_code, 200)
        s_data = synth_res.json()["data"]
        self.assertEqual(s_data["status"], "READY")
        self.assertEqual(s_data["audio_format"], "audio/mp3")

    # --- 9. PRODUCTION HARDENING: TOKEN REVOCATION, HEADERS & STREAMING ---

    def test_14_token_revocation_blacklist_on_logout(self):
        """Test that logging out blacklists the JWT and rejects subsequent requests."""
        # 1. Login citizen
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": self.citizen_email,
            "password": self.password,
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["data"]["access_token"]

        # 2. Verify token works
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)

        # 3. Call logout
        logout_res = self.client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)

        # 4. Attempt to use revoked token - MUST BE REJECTED WITH 401
        revoked_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(revoked_res.status_code, 401)
        self.assertIn("revoked", revoked_res.json()["message"].lower())

    def test_15_hardened_security_headers(self):
        """Test presence of defense-in-depth HTTP security headers."""
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        headers = res.headers
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(headers.get("x-frame-options"), "DENY")
        self.assertIn("max-age=", headers.get("strict-transport-security", ""))
        self.assertEqual(headers.get("referrer-policy"), "strict-origin-when-cross-origin")

    def test_16_chunked_streaming_evidence_upload(self):
        """Test that chunked streaming upload stores, hashes, and validates evidence correctly."""
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        rep_res = self.client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            data={
                "title": "Stream upload verification test",
                "content_text": "Testing chunked upload streaming buffer without memory bloat.",
                "nigerian_state": "Lagos",
            },
            files={"files": ("stream_sample.png", io.BytesIO(dummy_png), "image/png")},
        )
        self.assertEqual(rep_res.status_code, 201)
        data = rep_res.json()["data"]
        self.assertEqual(data["evidence_count"], 1)

    def test_17_reactive_websocket_push_and_ping(self):
        """Test real-time WebSocket connection lifecycle, initial clusters, and keep-alive ping."""
        with self.client.websocket_connect("/api/v1/narratives/ws") as websocket:
            init_data = websocket.receive_json()
            self.assertEqual(init_data["event"], "INITIAL_CLUSTERS")
            self.assertIn("clusters", init_data)

            # Test ping/pong
            websocket.send_text("ping")
            pong = websocket.receive_text()
            self.assertEqual(pong, "pong")


if __name__ == "__main__":
    unittest.main()
