import unittest

from app import create_app


class TestProvinceMapping(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_province_name_resolved(self):
        # province_code 079 is present in starter mapping files
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "079203012345", "province_version": "legacy_64"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["province_version"], "legacy_64")
        self.assertEqual(body["data"]["province_code"], "079")
        self.assertIsNotNone(body["data"]["province_name"])

    def test_province_code_not_found_warning(self):
        # 999 not in mapping
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "999203012345", "province_version": "legacy_64"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIsNone(body["data"]["province_name"])
        self.assertIn("province_code_not_found", body["warnings"])


if __name__ == "__main__":
    unittest.main()


