"""Unit and Integration Test Suite for Database Security and Audit Ledger."""

import unittest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.modules.security_audit.models import AuditLog, SecurityEvent
from backend.app.modules.security_audit.service import SecurityAuditService
from backend.app.common.enums import UserRoleType, SecurityEventType


class TestSecurityModule(unittest.TestCase):
    """Test suite verifying tamper-evident audit ledger, hash chaining, incident resolution, and security KPIs."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            # Create Security Officer
            cls.sec_officer_email = f"sec_officer_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.password = "SecOfficerPass123!"
            cls.sec_officer = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.sec_officer_email,
                    "password": cls.password,
                    "full_name": "Chief Security Officer",
                    "phone_number": "+2348099001122",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.SECURITY_OFFICER.value,
            )

            # Create regular citizen
            cls.citizen_email = f"citizen_sec_{uuid.uuid4().hex[:8]}@civicshield.ng"
            AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.citizen_email,
                    "password": cls.password,
                    "full_name": "Standard Citizen",
                    "phone_number": None,
                    "state_of_residence": "Delta",
                })(),
                role_name=UserRoleType.CITIZEN.value,
            )

        # Login
        sec_login = cls.client.post("/api/v1/auth/login", json={"email": cls.sec_officer_email, "password": cls.password})
        cls.sec_token = sec_login.json()["data"]["access_token"]

        citizen_login = cls.client.post("/api/v1/auth/login", json={"email": cls.citizen_email, "password": cls.password})
        cls.citizen_token = citizen_login.json()["data"]["access_token"]

    def test_01_audit_log_query_and_chaining(self):
        """Test retrieving audit ledger entries and inspecting cryptographic hash metadata."""
        response = self.client.get(
            "/api/v1/security/audit-logs",
            headers={"Authorization": f"Bearer {self.sec_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        items = data["data"]["items"]
        self.assertGreaterEqual(len(items), 1)

        # Inspect hash format
        entry = items[0]
        self.assertEqual(len(entry["sha256_entry_hash"]), 64)
        self.assertIn("previous_entry_hash", entry)

    def test_02_verify_ledger_integrity_success(self):
        """Test verifying unbroken cryptographic audit hash chain."""
        response = self.client.post(
            "/api/v1/security/audit-logs/verify-ledger",
            headers={"Authorization": f"Bearer {self.sec_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["is_valid"])
        self.assertGreaterEqual(data["total_entries_verified"], 1)

    def test_03_detect_tampering_when_record_altered(self):
        """Test that altering a database record breaks the cryptographic hash verification immediately."""
        with SessionLocal() as db:
            # Insert a record specifically to test tampering
            log_entry = SecurityAuditService.record_audit(
                db=db,
                action="SYSTEM_PARAMETER_CHANGED",
                entity_type="SYSTEM",
                entity_id="test-param-01",
                details={"param": "max_upload", "value": "25MB"},
            )
            tamper_id = log_entry.id
            original_action = log_entry.action

            # Simulate malicious tampering by directly changing the action without updating sha256_entry_hash
            log_entry.action = "TAMPERED_ACTION_MALICIOUS"
            db.commit()

        # Run verification tool - must detect break in chain
        verify_res = self.client.post(
            "/api/v1/security/audit-logs/verify-ledger",
            headers={"Authorization": f"Bearer {self.sec_token}"},
        )
        self.assertEqual(verify_res.status_code, 200)
        data = verify_res.json()["data"]
        self.assertFalse(data["is_valid"])
        self.assertEqual(data["broken_chain_at_id"], tamper_id)
        self.assertIn("tampering detected", data["verification_message"].lower())

        # Restore original action to maintain clean DB integrity
        with SessionLocal() as db:
            clean_entry = db.execute(select(AuditLog).where(AuditLog.id == tamper_id)).scalar_one()
            clean_entry.action = original_action
            db.commit()

    def test_04_security_events_and_resolution(self):
        """Test listing security events and resolving open threats with officer notes."""
        with SessionLocal() as db:
            # Create a test security event
            event = SecurityEvent(
                event_type=SecurityEventType.BRUTE_FORCE_SUSPECTED.value,
                severity="HIGH",
                ip_address="192.168.1.100",
                user_identifier="test_brute_force@civicshield.ng",
                details={"consecutive_failures": 6},
                resolved=False,
            )
            db.add(event)
            db.commit()
            event_id = event.id

        # List events
        list_res = self.client.get(
            "/api/v1/security/events?resolved=false",
            headers={"Authorization": f"Bearer {self.sec_token}"},
        )
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["data"]["items"]
        self.assertTrue(any(e["id"] == event_id for e in items))

        # Resolve event
        resolve_payload = {
            "resolution_notes": "IP investigated; temporary throttle applied. Account holder confirmed identity."
        }
        res_resolve = self.client.post(
            f"/api/v1/security/events/{event_id}/resolve",
            json=resolve_payload,
            headers={"Authorization": f"Bearer {self.sec_token}"},
        )
        self.assertEqual(res_resolve.status_code, 200)
        self.assertTrue(res_resolve.json()["data"]["resolved"])

    def test_05_security_metrics_kpi(self):
        """Test security overview metrics endpoint."""
        response = self.client.get(
            "/api/v1/security/metrics",
            headers={"Authorization": f"Bearer {self.sec_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("failed_logins_last_24h", data)
        self.assertIn("total_audit_records_logged", data)
        self.assertIn("ledger_integrity_status", data)

    def test_06_citizen_forbidden_from_security_audit(self):
        """Test that regular citizens cannot access audit logs or security metrics."""
        logs_res = self.client.get("/api/v1/security/audit-logs", headers={"Authorization": f"Bearer {self.citizen_token}"})
        self.assertEqual(logs_res.status_code, 403)

        metrics_res = self.client.get("/api/v1/security/metrics", headers={"Authorization": f"Bearer {self.citizen_token}"})
        self.assertEqual(metrics_res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
