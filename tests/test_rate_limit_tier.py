"""
Test rate limit theo tier
"""
import time
import unittest

from app import create_app
from app.config import Settings
from services.api_key_service import create_api_key, get_rate_limit_for_key


class TestRateLimitTier(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        # Enable tiered mode
        app.config["SETTINGS"] = Settings(api_key_mode="tiered")
        self.client = app.test_client()

    def test_free_tier_rate_limit_10_per_minute(self):
        """Free tier: 10 requests/minute"""
        # Tạo key free
        key = create_api_key(tier="free", owner_email="test@example.com")
        
        # Gọi 10 lần → OK
        for i in range(10):
            resp = self.client.post(
                "/v1/cccd/parse",
                json={"cccd": "079203012345"},
                headers={"X-API-Key": key}
            )
            self.assertEqual(resp.status_code, 200, f"Request {i+1} should be 200")
        
        # Lần thứ 11 → 429
        resp = self.client.post(
            "/v1/cccd/parse",
            json={"cccd": "079203012345"},
            headers={"X-API-Key": key}
        )
        self.assertEqual(resp.status_code, 429)

    def test_premium_tier_rate_limit_100_per_minute(self):
        """Premium tier: 100 requests/minute"""
        key = create_api_key(tier="premium", owner_email="test@example.com")
        
        # Gọi 100 lần → OK
        for i in range(100):
            resp = self.client.post(
                "/v1/cccd/parse",
                json={"cccd": "079203012345"},
                headers={"X-API-Key": key}
            )
            if resp.status_code != 200:
                self.fail(f"Request {i+1} failed with {resp.status_code}")
        
        # Lần thứ 101 → 429
        resp = self.client.post(
            "/v1/cccd/parse",
            json={"cccd": "079203012345"},
            headers={"X-API-Key": key}
        )
        self.assertEqual(resp.status_code, 429)

    def test_ultra_tier_rate_limit_1000_per_minute(self):
        """Ultra tier: 1000 requests/minute"""
        key = create_api_key(tier="ultra", owner_email="test@example.com")
        
        # Gọi 1000 lần → OK (chỉ test 50 lần để không quá lâu)
        for i in range(50):
            resp = self.client.post(
                "/v1/cccd/parse",
                json={"cccd": "079203012345"},
                headers={"X-API-Key": key}
            )
            self.assertEqual(resp.status_code, 200, f"Request {i+1} should be 200")
        
        # Verify rate limit string
        rate_limit = get_rate_limit_for_key(key)
        self.assertEqual(rate_limit, "1000 per minute")


if __name__ == "__main__":
    unittest.main()

