"""
Test validation cho Admin API (email, tier, days)
Note: Tests chỉ verify validation logic, không cần MySQL thật
"""
import unittest
from unittest.mock import patch

from app import create_app
from app.config import Settings


class TestAdminValidation(unittest.TestCase):
    def setUp(self):
        import os
        # Set env vars before creating app
        os.environ["API_KEY_MODE"] = "tiered"
        os.environ["ADMIN_SECRET"] = "test-admin-secret"
        # Mock MySQL connection (tests will fail if DB not available, but that's OK)
        os.environ["MYSQL_HOST"] = "localhost"
        os.environ["MYSQL_DATABASE"] = "cccd_api"
        
        app = create_app()
        app.testing = True
        app.config["SETTINGS"] = Settings(api_key_mode="tiered")
        self.client = app.test_client()
        self.admin_key = "test-admin-secret"

    def test_create_key_invalid_email_format(self):
        """Email sai format → 400"""
        test_cases = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@com",
            "user name@example.com",
            "",
        ]
        
        for email in test_cases:
            resp = self.client.post(
                "/admin/keys/create",
                json={"tier": "free", "email": email},
                headers={"X-Admin-Key": self.admin_key}
            )
            self.assertEqual(resp.status_code, 400, f"Email '{email}' should be rejected")
            data = resp.get_json()
            self.assertIn("email", data.get("error", "").lower())

    @patch("routes.admin.create_api_key")
    def test_create_key_valid_email_format(self, mock_create):
        """Email đúng format → 200"""
        mock_create.return_value = "free_test123"
        
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_123@test-domain.com",
        ]
        
        for email in valid_emails:
            resp = self.client.post(
                "/admin/keys/create",
                json={"tier": "free", "email": email},
                headers={"X-Admin-Key": self.admin_key}
            )
            self.assertEqual(resp.status_code, 200, f"Email '{email}' should be accepted")
            data = resp.get_json()
            self.assertTrue(data.get("success"))

    def test_create_key_invalid_tier(self):
        """Tier sai → 400"""
        resp = self.client.post(
            "/admin/keys/create",
            json={"tier": "invalid", "email": "test@example.com"},
            headers={"X-Admin-Key": self.admin_key}
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn("tier", data.get("error", "").lower())

    def test_create_key_missing_email(self):
        """Thiếu email → 400"""
        resp = self.client.post(
            "/admin/keys/create",
            json={"tier": "free"},
            headers={"X-Admin-Key": self.admin_key}
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn("email", data.get("error", "").lower())

    def test_create_key_invalid_days(self):
        """Days sai format → 400"""
        test_cases = [
            {"days": 0},      # < 1
            {"days": -1},     # < 1
            {"days": "abc"},  # không phải số
            {"days": 1.5},    # không phải số nguyên
        ]
        
        for days_data in test_cases:
            resp = self.client.post(
                "/admin/keys/create",
                json={"tier": "free", "email": "test@example.com", **days_data},
                headers={"X-Admin-Key": self.admin_key}
            )
            self.assertEqual(resp.status_code, 400, f"Days {days_data} should be rejected")

    def test_create_key_valid_days(self):
        """Days hợp lệ → 200"""
        resp = self.client.post(
            "/admin/keys/create",
            json={"tier": "free", "email": "test@example.com", "days": 30},
            headers={"X-Admin-Key": self.admin_key}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))


if __name__ == "__main__":
    unittest.main()

