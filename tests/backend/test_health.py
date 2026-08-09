import unittest
from fastapi.testclient import TestClient
from src.backend.main import app

class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "healthy")
        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("timestamp", data)

    def test_api_v1_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "healthy")

    def test_response_headers(self):
        response = self.client.get("/health")
        self.assertIn("x-request-id", response.headers)
        self.assertIn("x-process-time-ms", response.headers)

if __name__ == "__main__":
    unittest.main()
