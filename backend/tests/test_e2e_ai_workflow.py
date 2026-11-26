"""
CIVICSHIELD NG — END-TO-END AI FUNCTIONALITY TEST (Section 17).

Demonstrates the 10-step AI workflow across all 3 mandatory verification scenarios:
 - Scenario A: Claim CONTRADICTED by authentic certified reference
 - Scenario B: Claim SUPPORTED by authentic certified reference
 - Scenario C: Claim with INSUFFICIENT EVIDENCE in reference registry

LABEL: [SIMULATED / DEMONSTRATION DATA]
"""

import io
import uuid
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.modules.reporting.service import ReportingService
from backend.app.modules.reporting.schemas import ReportCreateRequest
from backend.app.modules.registry.service import RegistryService
from backend.app.modules.registry.schemas import DocumentCreateRequest
from backend.app.modules.ai_engine.service import AIEngineService
from backend.app.modules.narratives.service import NarrativesService
from backend.app.common.enums import UserRoleType, VerificationDecision, ClaimCategory


class TestE2EAIFunctionality(unittest.TestCase):
    """End-to-end verification demonstrating the complete 10-step AI intelligence pipeline."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            cls.uid = uuid.uuid4().hex[:6].upper()
            # 1. Register staff users
            cls.analyst_email = f"ai_e2e_analyst_{cls.uid.lower()}@civicshield.ng"
            cls.officer_email = f"ai_e2e_officer_{cls.uid.lower()}@civicshield.ng"
            cls.password = "E2EPass2026!"

            cls.analyst = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.analyst_email,
                    "password": cls.password,
                    "full_name": "AI Triage Analyst",
                    "phone_number": "+2348011223300",
                    "state_of_residence": "Kano",
                })(),
                role_name=UserRoleType.ANALYST.value,
            )

            cls.officer = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.officer_email,
                    "password": cls.password,
                    "full_name": "Institutional Verification Lead",
                    "phone_number": "+2348022334400",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.VERIFICATION_OFFICER.value,
            )

            # 2. Register authentic official reference gazettes
            # Notice A: Official schedule for Kano
            cls.doc_contra_ref = f"INEC-GAZETTE-KANO-{cls.uid}"
            RegistryService.register_document(
                db=db,
                request=DocumentCreateRequest(
                    document_code=cls.doc_contra_ref,
                    issuing_institution="Independent National Electoral Commission",
                    title=f"Certified Polling Unit Schedule for Kano Central {cls.uid}",
                    summary="INEC confirms voting will proceed normally at all designated polling units in Ward 4 without cancellation.",
                    content_text=f"INEC confirms all polling units in Ward 4 proceed normally as scheduled. No cancellation has been approved {cls.uid}.",
                    source_url="https://inecnigeria.org/gazettes/kano-central",
                ),
                authorized_user_id=cls.officer.id,
            )

            # Notice B: Official schedule for BVAS accreditation
            cls.doc_supp_ref = f"INEC-GAZETTE-BVAS-{cls.uid}"
            RegistryService.register_document(
                db=db,
                request=DocumentCreateRequest(
                    document_code=cls.doc_supp_ref,
                    issuing_institution="Independent National Electoral Commission",
                    title=f"Mandatory Guidelines on BVAS Accreditation {cls.uid}",
                    summary="INEC confirms voter accreditation commences nationwide strictly at 8:30am using BVAS.",
                    content_text=f"INEC guidelines mandate that voter accreditation commences strictly at 8:30am with BVAS {cls.uid}.",
                    source_url="https://inecnigeria.org/gazettes/bvas-guidelines",
                ),
                authorized_user_id=cls.officer.id,
            )

        # Login users
        res_a = cls.client.post("/api/v1/auth/login", json={"email": cls.analyst_email, "password": cls.password})
        cls.analyst_token = res_a.json()["data"]["access_token"]

        res_o = cls.client.post("/api/v1/auth/login", json={"email": cls.officer_email, "password": cls.password})
        cls.officer_token = res_o.json()["data"]["access_token"]

    def test_scenario_a_contradicted_claim_lifecycle(self):
        """
        SCENARIO A: Suspicious announcement contradicted by genuine official gazette.
        Demonstrates the complete 10-step AI workflow.
        """
        # Step 1: Receive citizen report
        submitted_content = f"WhatsApp broadcast claims all voting in Ward 4 has been cancelled and halted due to missing materials {self.doc_contra_ref}."
        sub_res = self.client.post(
            "/api/v1/reports",
            data={
                "title": f"Viral claim that Ward 4 polling units are cancelled in Kano {self.uid}",
                "content_text": submitted_content,
                "nigerian_state": "Kano",
            },
        )
        self.assertEqual(sub_res.status_code, 201)
        report = sub_res.json()["data"]
        report_id = report["id"]

        # Step 2 & 3: Extract factual claim & identify entities
        extract_res = self.client.post("/api/v1/ai/extract-claims", json={"text": submitted_content})
        self.assertEqual(extract_res.status_code, 200)
        extracted = extract_res.json()["data"]
        self.assertGreaterEqual(len(extracted["claims"]), 1)
        first_claim = extracted["claims"][0]
        self.assertTrue(first_claim["requires_verification"])

        # Step 4, 5, 6: Retrieve trusted reference, compare evidence, produce structured assessment
        assess_res = self.client.post(
            "/api/v1/ai/assess",
            json={"claim_text": first_claim["claim_text"]},
        )
        self.assertEqual(assess_res.status_code, 200)
        assessment = assess_res.json()["data"]
        self.assertEqual(assessment["classification"], "CONTRADICTED")
        self.assertTrue(assessment["requires_human_review"])
        self.assertGreaterEqual(len(assessment["evidence"]), 1)
        self.assertEqual(assessment["evidence"][0]["evidence_role"], "CONTRADICTORY")

        # Step 7: Detect similar submitted reports
        sim_res = self.client.post(
            "/api/v1/ai/similar-reports",
            json={"target_text": submitted_content, "report_id": report_id},
        )
        self.assertEqual(sim_res.status_code, 200)

        # Step 8: Group candidate reports into Narrative Pulse
        # Ingest a second report with matching narrative
        self.client.post(
            "/api/v1/reports",
            data={
                "title": f"Second post claiming Ward 4 polling cancelled {self.uid}",
                "content_text": f"Multiple Twitter users saying Ward 4 voting has been cancelled in Kano {self.doc_contra_ref}.",
                "nigerian_state": "Kano",
            },
        )
        scan_res = self.client.post(
            "/api/v1/narratives/scan",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(scan_res.status_code, 200)

        # Step 9: Return and persist AI analysis on the report
        pipe_res = self.client.post(
            f"/api/v1/ai/reports/{report_id}/analyze",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(pipe_res.status_code, 200)
        persisted_claims = pipe_res.json()["data"]
        self.assertGreaterEqual(len(persisted_claims), 1)

        # Step 10: Allow analyst and verification officer to review
        queue_res = self.client.get(
            "/api/v1/verification/queue?nigerian_state=Kano",
            headers={"Authorization": f"Bearer {self.officer_token}"},
        )
        self.assertEqual(queue_res.status_code, 200)
        self.assertGreaterEqual(len(queue_res.json()["data"]), 1)

    def test_scenario_b_supported_claim_lifecycle(self):
        """
        SCENARIO B: Citizen report corroborated by genuine official gazette.
        Demonstrates that affirmed claims are classified as SUPPORTED.
        """
        claim_text = f"INEC confirms voter accreditation commences strictly at 8:30am with BVAS {self.doc_supp_ref}."
        assess_res = self.client.post("/api/v1/ai/assess", json={"claim_text": claim_text})
        self.assertEqual(assess_res.status_code, 200)
        data = assess_res.json()["data"]

        self.assertEqual(data["classification"], "SUPPORTED")
        self.assertTrue(data["requires_human_review"])
        self.assertGreaterEqual(data["confidence"], 0.70)
        self.assertTrue(any(e["evidence_role"] == "SUPPORTING" for e in data["evidence"]))

    def test_scenario_c_insufficient_evidence_lifecycle(self):
        """
        SCENARIO C: Citizen report with no matching official evidence.
        Demonstrates that lack of evidence strictly produces INSUFFICIENT_EVIDENCE
        without falsely declaring the content false.
        """
        unsupported_claim = f"Local rumor says Ward 9 polling booths will be painted green tomorrow {self.uid}."
        assess_res = self.client.post("/api/v1/ai/assess", json={"claim_text": unsupported_claim})
        self.assertEqual(assess_res.status_code, 200)
        data = assess_res.json()["data"]

        self.assertEqual(data["classification"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(data["confidence"], 0.0)
        self.assertTrue(data["requires_human_review"])
        self.assertTrue(any("absence" in lim.lower() and "falsity" in lim.lower() for lim in data["limitations"]))


if __name__ == "__main__":
    unittest.main()
