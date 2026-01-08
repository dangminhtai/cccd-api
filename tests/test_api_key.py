import unittest

from app import create_app
from app.config import Settings


class TestAPIKey(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        # Replace Settings with one that requires API key
        app.config["SETTINGS"] = Settings(api_key="test-secret-key")
        self.client = app.test_client()

    def test_missing_api_key_returns_401(self):
        """Thiếu API key -> 401"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "079203012345"})
        self.assertEqual(resp.status_code, 401)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertIn("API key", body["message"])

    def test_wrong_api_key_returns_401(self):
        """Sai API key -> 401"""
        resp = self.client.post(
            "/v1/cccd/parse",
            json={"cccd": "079203012345"},
            headers={"X-API-Key": "wrong-key"}
        )
        self.assertEqual(resp.status_code, 401)
        body = resp.get_json()
        self.assertFalse(body["success"])

    def test_correct_api_key_returns_200(self):
        """Đúng API key -> 200"""
        resp = self.client.post(
            "/v1/cccd/parse",
            json={"cccd": "079203012345"},
            headers={"X-API-Key": "test-secret-key"}
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])


class TestNoAPIKey(unittest.TestCase):
    """Test khi không cấu hình API key (public API)"""
    def setUp(self):
        app = create_app()
        app.testing = True
        # Replace Settings with one that has no API key
        app.config["SETTINGS"] = Settings(api_key=None)
        self.client = app.test_client()

    def test_no_api_key_configured_allows_access(self):
        """Không cấu hình API key -> cho phép truy cập"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "079203012345"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])


if __name__ == "__main__":
    unittest.main()

