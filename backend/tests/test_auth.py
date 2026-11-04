"""Comprehensive test suite for Authentication and Access Control (RBAC)."""

import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.init_db import init_database
from backend.app.modules.auth.models import User, Role
from backend.app.modules.auth.service import AuthService
from backend.app.common.enums import UserRoleType


class TestAuthModule(unittest.TestCase):
    """Test suite verifying user registration, login, JWT lifecycle, brute force defense, and RBAC."""

    @classmethod
    def setUpClass(cls):
        """Ensure database tables and RBAC seeds exist."""
        init_database()
        cls.client = TestClient(app)

    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.test_email = f"citizen_{self.unique_id}@civicshield.ng"
        self.test_password = "SecurePassword123!"

    def test_01_citizen_registration_success(self):
        """Test successful citizen registration with valid Nigerian state."""
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Chidi Nnamdi",
            "phone_number": "+2348012345678",
            "state_of_residence": "Enugu",
        }
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["email"], self.test_email)
        self.assertEqual(data["data"]["state_of_residence"], "Enugu")
        self.assertTrue(any(r["name"] == "CITIZEN" for r in data["data"]["roles"]))

    def test_02_registration_duplicate_email(self):
        """Test rejection when attempting to register with an existing email."""
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Chidi Nnamdi",
            "state_of_residence": "Enugu",
        }
        # First registration
        self.client.post("/api/v1/auth/register", json=payload)

        # Duplicate attempt
        dup_response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(dup_response.status_code, 409)
        self.assertFalse(dup_response.json()["success"])

    def test_03_registration_invalid_state(self):
        """Test validation failure when providing a fictitious state."""
        payload = {
            "email": f"bad_state_{self.unique_id}@civicshield.ng",
            "password": self.test_password,
            "full_name": "Tester",
            "state_of_residence": "Atlantis",
        }
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_04_login_success(self):
        """Test authentication with valid credentials returning JWT tokens."""
        # Register user first
        reg_payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Chidi Nnamdi",
            "state_of_residence": "Enugu",
        }
        self.client.post("/api/v1/auth/register", json=reg_payload)

        # Login
        login_payload = {"email": self.test_email, "password": self.test_password}
        response = self.client.post("/api/v1/auth/login", json=login_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertGreater(data["expires_in_seconds"], 0)

    def test_05_login_invalid_password(self):
        """Test authentication failure with incorrect password."""
        reg_payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Chidi Nnamdi",
        }
        self.client.post("/api/v1/auth/register", json=reg_payload)

        bad_login = {"email": self.test_email, "password": "WrongPassword999!"}
        response = self.client.post("/api/v1/auth/login", json=bad_login)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_06_account_lockout_after_repeated_failures(self):
        """Test account lock mechanism after exceeding maximum failed login attempts."""
        reg_payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Lockout Test User",
        }
        self.client.post("/api/v1/auth/register", json=reg_payload)

        bad_login = {"email": self.test_email, "password": "WrongPassword!"}
        # Fail 5 consecutive times
        for _ in range(5):
            self.client.post("/api/v1/auth/login", json=bad_login)

        # 6th attempt should return 403 Forbidden (locked account)
        locked_response = self.client.post("/api/v1/auth/login", json=bad_login)
        self.assertEqual(locked_response.status_code, 403)
        self.assertIn("locked", locked_response.json()["message"].lower())

    def test_07_token_refresh(self):
        """Test refresh token exchange for a fresh access token."""
        reg_payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Refresh Tester",
        }
        self.client.post("/api/v1/auth/register", json=reg_payload)
        login_res = self.client.post("/api/v1/auth/login", json={"email": self.test_email, "password": self.test_password})
        refresh_token = login_res.json()["data"]["refresh_token"]

        refresh_res = self.client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        self.assertEqual(refresh_res.status_code, 200)
        new_data = refresh_res.json()["data"]
        self.assertIn("access_token", new_data)
        self.assertIn("refresh_token", new_data)

    def test_08_get_me_protected(self):
        """Test protected /me profile endpoint requiring valid Bearer token."""
        # Unauthenticated request
        unauth_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(unauth_res.status_code, 401)

        # Authenticated request
        reg_payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Profile Tester",
        }
        self.client.post("/api/v1/auth/register", json=reg_payload)
        login_res = self.client.post("/api/v1/auth/login", json={"email": self.test_email, "password": self.test_password})
        token = login_res.json()["data"]["access_token"]

        auth_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(auth_res.status_code, 200)
        self.assertEqual(auth_res.json()["data"]["email"], self.test_email)


if __name__ == "__main__":
    unittest.main()
