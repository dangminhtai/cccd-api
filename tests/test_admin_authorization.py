"""
Test authorization cho Admin API - Xác nhận người dùng bình thường không thể truy cập
"""
import os
import unittest
from unittest.mock import patch

from app import create_app
from app.config import Settings


class TestAdminAuthorization(unittest.TestCase):
    """Test cases để xác nhận admin endpoints được bảo vệ đúng cách"""

    def setUp(self):
        """Setup test environment với ADMIN_SECRET"""
        os.environ["API_KEY_MODE"] = "tiered"
        os.environ["ADMIN_SECRET"] = "correct-admin-secret-12345"
        os.environ["MYSQL_HOST"] = "localhost"
        os.environ["MYSQL_DATABASE"] = "cccd_api"
        
        app = create_app()
        app.testing = True
        app.config["SETTINGS"] = Settings(api_key_mode="tiered")
        self.client = app.test_client()
        self.correct_admin_key = "correct-admin-secret-12345"

    def test_admin_dashboard_without_key(self):
        """GET /admin/ không cần key (chỉ hiển thị form)"""
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200, "Admin dashboard page should be accessible without key")

    def test_admin_endpoints_without_key(self):
        """Tất cả admin API endpoints yêu cầu X-Admin-Key header"""
        endpoints = [
            ("POST", "/admin/keys/create", {"tier": "free", "days": 30}),
            ("GET", "/admin/stats", None),
            ("GET", "/admin/payments", None),
            ("GET", "/admin/users", None),
        ]
        
        for method, endpoint, data in endpoints:
            if method == "POST":
                resp = self.client.post(endpoint, json=data)
            else:
                resp = self.client.get(endpoint)
            
            self.assertEqual(
                resp.status_code, 
                403, 
                f"{method} {endpoint} should return 403 without admin key"
            )
            json_data = resp.get_json()
            self.assertIn("error", json_data)
            self.assertIn("Unauthorized", json_data["error"])

    def test_admin_endpoints_with_wrong_key(self):
        """Admin endpoints với key sai → 403"""
        wrong_keys = [
            "",
            "wrong-key",
            "incorrect-admin-secret-12345",
            "correct-admin-secret-1234",  # Thiếu 1 ký tự
            "correct-admin-secret-123456",  # Thừa 1 ký tự
        ]
        
        endpoints = [
            ("POST", "/admin/keys/create", {"tier": "free", "days": 30}),
            ("GET", "/admin/stats", None),
        ]
        
        for wrong_key in wrong_keys:
            for method, endpoint, data in endpoints:
                headers = {"X-Admin-Key": wrong_key} if wrong_key else {}
                
                if method == "POST":
                    resp = self.client.post(endpoint, json=data, headers=headers)
                else:
                    resp = self.client.get(endpoint, headers=headers)
                
                self.assertEqual(
                    resp.status_code,
                    403,
                    f"{method} {endpoint} should return 403 with wrong key: '{wrong_key}'"
                )
                json_data = resp.get_json()
                self.assertIn("error", json_data)
                self.assertIn("Unauthorized", json_data["error"])

    def test_admin_endpoints_with_correct_key(self):
        """Admin endpoints với key đúng → không bị 403 (có thể 200 hoặc lỗi khác nhưng không phải 403)"""
        endpoints = [
            ("GET", "/admin/stats", None),
            ("GET", "/admin/payments", None),
            ("GET", "/admin/users", None),
        ]
        
        headers = {"X-Admin-Key": self.correct_admin_key}
        
        for method, endpoint, data in endpoints:
            if method == "POST":
                resp = self.client.post(endpoint, json=data, headers=headers)
            else:
                resp = self.client.get(endpoint, headers=headers)
            
            # Với key đúng, không được trả về 403
            # Có thể là 200 (success) hoặc 500 (DB error) nhưng KHÔNG phải 403
            self.assertNotEqual(
                resp.status_code,
                403,
                f"{method} {endpoint} should NOT return 403 with correct admin key"
            )
            
            # Nếu có error, không được là "Unauthorized"
            if resp.status_code != 200:
                json_data = resp.get_json()
                if json_data and "error" in json_data:
                    self.assertNotIn(
                        "Unauthorized",
                        json_data["error"],
                        f"{method} {endpoint} should NOT return 'Unauthorized' with correct key"
                    )

    def test_admin_key_case_sensitive(self):
        """Admin key phải case-sensitive"""
        # Test với key viết hoa
        resp = self.client.get(
            "/admin/stats",
            headers={"X-Admin-Key": self.correct_admin_key.upper()}
        )
        self.assertEqual(resp.status_code, 403, "Admin key should be case-sensitive")
        
        # Test với key viết thường (đã đúng)
        resp = self.client.get(
            "/admin/stats",
            headers={"X-Admin-Key": self.correct_admin_key.lower()}
        )
        # Nếu key đúng là lowercase thì không được 403
        if self.correct_admin_key.islower():
            self.assertNotEqual(resp.status_code, 403)

    def test_admin_key_missing_header(self):
        """Thiếu header X-Admin-Key → 403"""
        resp = self.client.post(
            "/admin/keys/create",
            json={"tier": "free", "days": 30}
            # Không có headers
        )
        self.assertEqual(resp.status_code, 403)
        json_data = resp.get_json()
        self.assertIn("Unauthorized", json_data["error"])

    def test_admin_key_in_query_vs_header(self):
        """Admin key chỉ chấp nhận từ header, không từ query parameter"""
        # Test với key trong query parameter (không được chấp nhận)
        resp = self.client.get("/admin/stats?X-Admin-Key=correct-admin-secret-12345")
        self.assertEqual(
            resp.status_code,
            403,
            "Admin key should only be accepted from header, not query parameter"
        )
        
        # Test với key trong header (được chấp nhận)
        resp = self.client.get(
            "/admin/stats",
            headers={"X-Admin-Key": self.correct_admin_key}
        )
        self.assertNotEqual(resp.status_code, 403)

    def test_admin_dashboard_accessible_without_key(self):
        """GET /admin/ phải accessible mà không cần key (chỉ hiển thị form)"""
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        # Kiểm tra response có chứa HTML (template được render)
        self.assertIn(b"<!DOCTYPE html", resp.data or b"")
        self.assertIn(b"Admin Dashboard", resp.data or b"")


if __name__ == "__main__":
    unittest.main()
