"""Unit and Integration Test Suite for Coordinated Narrative Detection."""

import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.modules.reporting.service import ReportingService
from backend.app.modules.reporting.schemas import ReportCreateRequest
from backend.app.modules.narratives.service import NarrativesService
from backend.app.common.enums import UserRoleType


class TestNarrativesModule(unittest.TestCase):
    """Test suite verifying multi-report clustering, threat indicators, velocity scoring, and graph data."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            # Create Analyst
            cls.analyst_email = f"narrative_analyst_{uuid.uuid4().hex[:8]}@civicshield.ng"
            cls.password = "AnalystPass123!"
            cls.analyst = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.analyst_email,
                    "password": cls.password,
                    "full_name": "Threat Intelligence Analyst",
                    "phone_number": "+2348033445566",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.ANALYST.value,
            )

            # Create regular Citizen
            cls.citizen_email = f"citizen_narrative_{uuid.uuid4().hex[:8]}@civicshield.ng"
            AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.citizen_email,
                    "password": cls.password,
                    "full_name": "Informed Citizen",
                    "phone_number": None,
                    "state_of_residence": "Kano",
                })(),
                role_name=UserRoleType.CITIZEN.value,
            )

        # Login
        analyst_login = cls.client.post("/api/v1/auth/login", json={"email": cls.analyst_email, "password": cls.password})
        cls.analyst_token = analyst_login.json()["data"]["access_token"]

        citizen_login = cls.client.post("/api/v1/auth/login", json={"email": cls.citizen_email, "password": cls.password})
        cls.citizen_token = citizen_login.json()["data"]["access_token"]

    def test_01_cluster_similar_reports(self):
        """Test scanning and grouping multiple similar reports into a coherent narrative cluster."""
        uid = uuid.uuid4().hex[:6]
        # Ingest two reports with matching narrative
        with SessionLocal() as db:
            rep_a = ReportingService.submit_report(
                db=db,
                report_data=ReportCreateRequest(
                    title=f"Viral audio claims BVAS failure in Ward 7 {uid}",
                    content_text=f"A viral WhatsApp voice note claims BVAS machines failed completely across Ward 7 polling units {uid}.",
                    nigerian_state="Kano",
                ),
            )
            rep_b = ReportingService.submit_report(
                db=db,
                report_data=ReportCreateRequest(
                    title=f"Reports that BVAS failed in Ward 7 polling units {uid}",
                    content_text=f"Rumors circulating that BVAS machines have failed across Ward 7 polling units causing voters to disperse {uid}.",
                    nigerian_state="Kaduna",
                ),
            )
            self.rep_a_id = rep_a.id
            self.rep_b_id = rep_b.id

        # Trigger narrative scan
        scan_res = self.client.post(
            "/api/v1/narratives/scan?lookback_hours=24",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(scan_res.status_code, 200)
        self.assertTrue(scan_res.json()["success"])

        # Fetch active clusters
        clusters_res = self.client.get(
            "/api/v1/narratives/clusters",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(clusters_res.status_code, 200)
        clusters = clusters_res.json()["data"]
        self.assertGreaterEqual(len(clusters), 1)

        # Find the specific cluster containing rep_a
        target_cluster = None
        for c in clusters:
            d_res = self.client.get(
                f"/api/v1/narratives/clusters/{c['id']}",
                headers={"Authorization": f"Bearer {self.analyst_token}"},
            )
            c_detail = d_res.json()["data"]
            if any(r["report_id"] == self.rep_a_id for r in c_detail["cluster_reports"]):
                target_cluster = c_detail
                break

        self.assertIsNotNone(target_cluster)
        self.assertGreaterEqual(target_cluster["reports_count"], 2)
        indicator_types = [ti["indicator_type"] for ti in target_cluster["threat_indicators"]] + [target_cluster["amplification_pattern"]]
        self.assertTrue("CROSS_PLATFORM_SPIKE" in indicator_types or "SYNCHRONIZED_POSTING" in indicator_types)

    def test_02_graph_data_generation(self):
        """Test network graph endpoint returning nodes and edges for visualization."""
        response = self.client.get(
            "/api/v1/narratives/graph",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreaterEqual(len(data["nodes"]), 1)
        self.assertGreaterEqual(len(data["edges"]), 1)

    def test_03_citizen_forbidden_from_narrative_intelligence(self):
        """Test that regular citizens cannot access institutional narrative intelligence."""
        response = self.client.get(
            "/api/v1/narratives/clusters",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
