"""
Comprehensive AI Evaluation and Verification Test Suite (Section 13).

Evaluates:
 1. Claim extraction correctness and entity extraction.
 2. Verified claims with reliable supporting evidence.
 3. Claims contradicted by trusted references.
 4. Claims with insufficient evidence (never falsely labeled misinformation).
 5. Outdated announcements.
 6. Impersonation and forged circular attempts.
 7. Ambiguous and incomplete statements.
 8. Opinion-based statements vs empirical factual claims.
 9. Duplicate report detection (exact normalized matching).
10. Semantically similar reports.
11. Unrelated reports (distinction).
12. English and Nigerian Pidgin multilingual processing.
13. Unsupported language detection and graceful handling.
14. Provider timeouts and malformed response recovery.
15. Malformed source records handling.
16. Audio format validation, empty audio rejection, and transcription linking.
"""

import io
import uuid
import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.init_db import init_database
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService
from backend.app.modules.registry.service import RegistryService
from backend.app.modules.registry.schemas import DocumentCreateRequest
from backend.app.modules.reporting.service import ReportingService
from backend.app.modules.reporting.schemas import ReportCreateRequest
from backend.app.modules.ai_engine.service import AIEngineService
from backend.app.modules.ai_engine.schemas import ClaimAnalysisRequest, ClaimExtractionRequest
from backend.app.modules.ai_engine.similarity import SimilarityEngine
from backend.app.modules.ai_engine.multilingual import MultilingualEngine
from backend.app.modules.ai_engine.speech import SpeechTranscriptionService
from backend.app.modules.ai_engine.providers.dev_adapter import DevelopmentAdapterAIProvider
from backend.app.modules.ai_engine.providers.local_heuristic import LocalHeuristicAIProvider
from backend.app.common.enums import UserRoleType, VerificationDecision, ClaimCategory


class TestAIEvaluationSuite(unittest.TestCase):
    """Rigorous evaluation suite testing all required AI behavior categories."""

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

        with SessionLocal() as db:
            cls.uid = uuid.uuid4().hex[:6].upper()
            cls.analyst_email = f"eval_analyst_{cls.uid.lower()}@civicshield.ng"
            cls.password = "EvalPass2026!"
            cls.analyst = AuthService.register_user(
                db=db,
                request=type("Req", (), {
                    "email": cls.analyst_email,
                    "password": cls.password,
                    "full_name": "AI Evaluation Officer",
                    "phone_number": "+2348011998877",
                    "state_of_residence": "Federal Capital Territory",
                })(),
                role_name=UserRoleType.ANALYST.value,
            )

            # 1. Register Supporting Gazette
            cls.doc_supp_code = f"INEC-SUPP-{cls.uid}"
            RegistryService.register_document(
                db=db,
                request=DocumentCreateRequest(
                    document_code=cls.doc_supp_code,
                    issuing_institution="Independent National Electoral Commission",
                    title=f"Accreditation Procedures for General Election {cls.uid}",
                    summary="INEC confirms accreditation commences strictly at 8:30am using BVAS nationwide.",
                    content_text=f"INEC confirms accreditation commences strictly at 8:30am nationwide with mandatory BVAS accreditation {cls.uid}.",
                    source_url="https://inecnigeria.org/gazettes/accreditation-2026",
                ),
                authorized_user_id=cls.analyst.id,
            )

            # 2. Register Contradicting Gazette
            cls.doc_contra_code = f"INEC-CONTRA-{cls.uid}"
            RegistryService.register_document(
                db=db,
                request=DocumentCreateRequest(
                    document_code=cls.doc_contra_code,
                    issuing_institution="Independent National Electoral Commission",
                    title=f"Clarification on Polling Unit Relocation Rumors in Ward 5 {cls.uid}",
                    summary="INEC confirms all polling units in Ward 5 remain at their gazetted locations without relocation.",
                    content_text=f"INEC clarifies that all polling units proceed normally at gazetted locations. No relocation has been approved for Ward 5 {cls.uid}.",
                    source_url="https://inecnigeria.org/gazettes/ward5-2026",
                ),
                authorized_user_id=cls.analyst.id,
            )

            # 3. Register Outdated Notice (dated 3 years ago)
            cls.doc_outdated_code = f"INEC-OLD-{cls.uid}"
            old_doc = RegistryService.register_document(
                db=db,
                request=DocumentCreateRequest(
                    document_code=cls.doc_outdated_code,
                    issuing_institution="Independent National Electoral Commission",
                    title=f"Historical Timetable for 2023 Electoral Cycle {cls.uid}",
                    summary="Historical notice regarding 2023 voter card collection deadline.",
                    content_text=f"PVC collection ends on January 22 for the 2023 cycle {cls.uid}.",
                ),
                authorized_user_id=cls.analyst.id,
            )
            # Adjust publication date to past
            old_doc.publication_date = datetime.now(timezone.utc) - timedelta(days=700)
            db.commit()

        # Login analyst
        res = cls.client.post("/api/v1/auth/login", json={"email": cls.analyst_email, "password": cls.password})
        cls.analyst_token = res.json()["data"]["access_token"]

    def tearDown(self):
        # Reset provider to default after tests
        AIEngineService.set_provider(LocalHeuristicAIProvider())

    # ---------------------------------------------------------
    # 1. Claim Extraction & Entity Spotting
    # ---------------------------------------------------------
    def test_01_claim_extraction_electoral_entities(self):
        """Evaluate claim extraction and entity recognition on complex electoral narratives."""
        text = (
            "The election has been postponed nationwide until next month. "
            "INEC Chairman announced the change in Abuja on Saturday."
        )
        res = self.client.post("/api/v1/ai/extract-claims", json={"text": text, "context_state": "Enugu"})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["original_text"], text)
        self.assertGreaterEqual(len(data["claims"]), 1)

        # Check entity recognition
        first_claim = data["claims"][0]
        self.assertEqual(first_claim["claim_type"], "ELECTION_DATE_OR_POSTPONEMENT")
        self.assertTrue(first_claim["requires_verification"])

        # Check entities in response
        all_entities = [e for c in data["claims"] for e in c["entities"]]
        self.assertTrue(any("INEC" in e for e in all_entities) or any("Abuja" in e for e in all_entities))

    # ---------------------------------------------------------
    # 2. Supported Claim with Reliable Supporting Evidence
    # ---------------------------------------------------------
    def test_02_supported_claim_with_reliable_evidence(self):
        """Evaluate that claim affirmed by certified official gazette is classified as SUPPORTED."""
        claim = f"INEC confirms accreditation commences strictly at 8:30am with mandatory BVAS accreditation {self.doc_supp_code}."
        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": claim})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["classification"], "SUPPORTED")
        self.assertEqual(data["ai_suggested_status"], VerificationDecision.UNDER_REVIEW.value)
        self.assertTrue(data["requires_human_review"])
        self.assertGreaterEqual(data["ai_confidence_score"], 0.70)
        self.assertFalse(data["contradiction_suspected"])

    # ---------------------------------------------------------
    # 3. Contradicted Claim with Trusted Reference
    # ---------------------------------------------------------
    def test_03_contradicted_claim_with_trusted_reference(self):
        """Evaluate that claim asserting opposite of certified gazette is flagged as CONTRADICTED."""
        claim = f"Urgent: all polling units in Ward 5 have been cancelled and relocated to another venue {self.doc_contra_code}."
        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": claim})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["classification"], "CONTRADICTED")
        self.assertTrue(data["contradiction_suspected"])
        self.assertEqual(data["ai_suggested_status"], VerificationDecision.UNDER_REVIEW.value)
        self.assertTrue(data["requires_human_review"])
        self.assertTrue(any(s["document_code"] == self.doc_contra_code for s in data["sources_consulted"]))

    # ---------------------------------------------------------
    # 4. Claims with Insufficient Evidence
    # ---------------------------------------------------------
    def test_04_insufficient_evidence_behavior(self):
        """
        Evaluate non-negotiable responsible AI rule:
        Absence of evidence MUST return INSUFFICIENT_EVIDENCE and NEVER be labeled false/misinformation.
        """
        unrecorded_claim = f"Community youth leaders in Ward 12 had an informal meeting regarding logistics {self.uid}."
        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": unrecorded_claim})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["classification"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(data["ai_suggested_status"], VerificationDecision.INSUFFICIENT_EVIDENCE.value)
        self.assertEqual(data["ai_confidence_score"], 0.0)
        self.assertFalse(data["contradiction_suspected"])
        self.assertTrue(data["requires_human_review"])
        self.assertIn("absence of evidence must not be construed as falsity", data["analysis_summary"].lower())

    # ---------------------------------------------------------
    # 5. Outdated Announcements
    # ---------------------------------------------------------
    def test_05_outdated_announcements(self):
        """Evaluate detection of superseded historical electoral announcements."""
        old_claim = f"PVC collection ends on January 22 for the 2023 cycle according to INEC notice {self.doc_outdated_code}."
        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": old_claim})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["classification"], "OUTDATED_INFORMATION")
        self.assertEqual(data["ai_suggested_status"], VerificationDecision.UNDER_REVIEW.value)
        self.assertTrue(data["requires_human_review"])

    # ---------------------------------------------------------
    # 6. Impersonation Attempts
    # ---------------------------------------------------------
    def test_06_impersonation_attempts(self):
        """Evaluate detection of forged circulars claiming unverified signing or viral broadcast urgency."""
        fake_circular = (
            f"Signed by the INEC Chairman Mahmood Yakubu. Official circular ref 098/2026. "
            f"Forward this to all groups immediately before voting is stopped {self.uid}."
        )
        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": fake_circular})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["classification"], "IMPERSONATION")
        self.assertEqual(data["category"], ClaimCategory.DISINFORMATION_CAMPAIGN.value)
        self.assertTrue(data["requires_human_review"])

    # ---------------------------------------------------------
    # 7. Ambiguous and Incomplete Statements
    # ---------------------------------------------------------
    def test_07_ambiguous_and_incomplete_statements(self):
        """Evaluate that noisy, short, or fragmented statements do not crash and preserve original text."""
        ambiguous_text = "They said rumors are everywhere in town."
        res = self.client.post("/api/v1/ai/extract-claims", json={"text": ambiguous_text})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["original_text"], ambiguous_text)
        self.assertGreaterEqual(len(data["claims"]), 1)

    # ---------------------------------------------------------
    # 8. Opinion-Based Statements
    # ---------------------------------------------------------
    def test_08_opinion_based_statements(self):
        """Evaluate differentiation between subjective opinions and empirical factual claims."""
        opinion_text = "I believe the candidate will probably win because in my opinion he is popular."
        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": opinion_text})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        self.assertEqual(data["classification"], "OPINION_BASED")
        self.assertIn("subjective", data["analysis_summary"].lower())
        self.assertTrue(data["requires_human_review"])

    # ---------------------------------------------------------
    # 9. Duplicate Report Detection
    # ---------------------------------------------------------
    def test_09_duplicate_report_detection(self):
        """Evaluate that exact normalized text duplicate yields 1.0 similarity score."""
        t1 = "Urgent: thugs attacked polling unit 004 in Ikeja LGA."
        t2 = "urgent: thugs attacked polling unit 004 in ikeja lga! "
        sim = SimilarityEngine.calculate_similarity(t1, t2)
        self.assertEqual(sim, 1.0)

    # ---------------------------------------------------------
    # 10. Semantically Similar Reports
    # ---------------------------------------------------------
    def test_10_semantically_similar_reports(self):
        """Evaluate algorithmic similarity detection over rephrased reports."""
        target = "INEC officials arrived late without ballot ink in Ward 3 polling units."
        similar = "Polling units in Ward 3 experienced severe delays because INEC officials arrived late without ink."
        candidates = [{"id": "rep-cand-1", "text": similar}]

        res = self.client.post(
            "/api/v1/ai/similar-reports",
            json={"target_text": target, "candidate_reports": candidates, "threshold": 0.40},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(len(data["similar_reports"]), 1)
        self.assertGreaterEqual(data["similar_reports"][0]["similarity_score"], 0.40)
        self.assertTrue(data["requires_cluster_review"])

    # ---------------------------------------------------------
    # 11. Unrelated Reports
    # ---------------------------------------------------------
    def test_11_unrelated_reports(self):
        """Evaluate that completely distinct topics produce near-zero similarity score."""
        t_electoral = "INEC confirms collation of senatorial results commences at midnight in Port Harcourt."
        t_weather = "Heavy flooding along the Third Mainland Bridge in Lagos caused multi-vehicle traffic standstill."
        sim = SimilarityEngine.calculate_similarity(t_electoral, t_weather)
        self.assertLess(sim, 0.15)

    # ---------------------------------------------------------
    # 12. English & Nigerian Pidgin Multilingual Processing
    # ---------------------------------------------------------
    def test_12_english_and_pidgin_multilingual_processing(self):
        """Evaluate Nigerian Pidgin detection, translation, and transparent machine labeling."""
        pidgin_text = "Make una hear, dem say inec don cancel election for Ward 4! Wahala dey!"
        # Detection
        det_res = self.client.post("/api/v1/ai/multilingual/detect", json={"text": pidgin_text})
        self.assertEqual(det_res.status_code, 200)
        self.assertEqual(det_res.json()["data"]["detected_language"], "pcm")

        # Translation
        trans_res = self.client.post(
            "/api/v1/ai/multilingual/translate",
            json={"text": pidgin_text, "source_language": "pcm", "target_language": "en"},
        )
        self.assertEqual(trans_res.status_code, 200)
        data = trans_res.json()["data"]
        self.assertIn("election", data["translated_text"].lower())
        self.assertTrue(data["is_machine_translated"])
        self.assertIn("Machine Translation", data["translation_label"])

    # ---------------------------------------------------------
    # 13. Unsupported Language Handling
    # ---------------------------------------------------------
    def test_13_unsupported_languages_graceful_handling(self):
        """Evaluate that Hausa input is identified but not translated with fake output."""
        hausa_text = "Hukumar zabe ta kasa INEC ta sanar da sabon tsarin zabe a jihar Kano."
        det_res = self.client.post("/api/v1/ai/multilingual/detect", json={"text": hausa_text})
        self.assertEqual(det_res.status_code, 200)
        data = det_res.json()["data"]
        self.assertEqual(data["detected_language"], "ha")
        self.assertFalse(data["is_supported"])

    # ---------------------------------------------------------
    # 14. Invalid AI Provider Responses & Timeout Fallback
    # ---------------------------------------------------------
    def test_14_invalid_ai_provider_responses_and_timeouts(self):
        """Evaluate graceful degraded recovery when AI provider times out."""
        # Inject timeout-simulating dev adapter
        AIEngineService.set_provider(DevelopmentAdapterAIProvider(simulate_timeout=True))

        res = self.client.post("/api/v1/ai/analyze-claim", json={"claim_text": "Sample claim during timeout"})
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        # Verifies degraded response adheres to Section 6/16 requirements
        self.assertFalse(data["service_available"])
        self.assertEqual(data["ai_suggested_status"], "INSUFFICIENT_EVIDENCE")
        self.assertTrue(data["requires_human_review"])
        self.assertIn("unavailable or timed out", data["analysis_summary"].lower())

    # ---------------------------------------------------------
    # 15. Malformed Source Records Handling
    # ---------------------------------------------------------
    def test_15_malformed_source_records(self):
        """Evaluate evidence comparison resilience against records missing standard keys."""
        malformed_sources = [
            {"invalid_key": 123},
            {"title": None, "content_text": None},
        ]
        provider = LocalHeuristicAIProvider()
        # Should execute safely without raising KeyError or AttributeError
        res = provider.evaluate_claim_against_sources("Voter accreditation in progress", malformed_sources)
        self.assertIn("ai_suggested_status", res)
        self.assertTrue(res["requires_human_review"])

    # ---------------------------------------------------------
    # 16. Audio Validation, Empty Audio Rejection & Linkage
    # ---------------------------------------------------------
    def test_16_audio_format_validation_and_errors(self):
        """Evaluate audio validation rejecting empty or invalid audio formats."""
        # 1. Empty audio file
        empty_res = self.client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("empty.wav", io.BytesIO(b""), "audio/wav")},
        )
        self.assertEqual(empty_res.status_code, 422)
        self.assertIn("empty", empty_res.json()["message"].lower())

        # 2. Unsupported MIME format
        bad_format_res = self.client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "application/x-dosexec")},
        )
        self.assertEqual(bad_format_res.status_code, 422)
        self.assertIn("unsupported audio format", bad_format_res.json()["message"].lower())

        # 3. Valid WAV audio with report_id linkage
        dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00data\x00\x00\x00\x00"
        valid_res = self.client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("speech.wav", io.BytesIO(dummy_wav), "audio/wav")},
            data={"language_hint": "en", "report_id": "rep-test-001"},
        )
        self.assertEqual(valid_res.status_code, 200)
        data = valid_res.json()["data"]
        self.assertEqual(data["detected_language"], "en")
        self.assertEqual(data["report_id"], "rep-test-001")


if __name__ == "__main__":
    unittest.main()
