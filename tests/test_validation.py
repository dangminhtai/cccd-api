import unittest

from app import create_app


class TestValidation(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_missing_cccd(self):
        """Thiếu trường cccd -> 400"""
        resp = self.client.post("/v1/cccd/parse", json={})
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertFalse(body["is_valid_format"])
        self.assertIn("Thiếu", body["message"])

    def test_cccd_not_string(self):
        """cccd là số thay vì chuỗi -> 400"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": 123456789012})
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertFalse(body["is_valid_format"])

    def test_cccd_with_letters(self):
        """cccd có chữ -> 400"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "07920301234a"})
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertFalse(body["is_valid_format"])

    def test_cccd_wrong_length_short(self):
        """cccd ngắn hơn 12 số -> 400"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "12345"})
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertFalse(body["is_valid_format"])

    def test_cccd_wrong_length_long(self):
        """cccd dài hơn 12 số -> 400"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "1234567890123456"})
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertFalse(body["is_valid_format"])

    def test_cccd_valid(self):
        """cccd hợp lệ 12 số -> 200"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "079203012345"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])
        self.assertTrue(body["is_valid_format"])
        self.assertIsNotNone(body["data"])

    def test_invalid_province_version(self):
        """province_version không hợp lệ -> 400"""
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "079203012345", "province_version": "invalid"})
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertIn("province_version", body["message"])


if __name__ == "__main__":
    unittest.main()

