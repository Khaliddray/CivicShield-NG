"""Verification test suite for Application Foundation & Health endpoints."""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app


class TestHealthEndpoints(unittest.TestCase):
    """Test suite for root and health check endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Verify root endpoint provides platform metadata."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["platform"], "CivicShield NG")
        self.assertEqual(data["data"]["version"], "1.0.0")

    def test_health_check_endpoint(self):
        """Verify health check endpoint verifies database connectivity."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")
        self.assertEqual(data["data"]["database"], "healthy")


if __name__ == "__main__":
    unittest.main()
