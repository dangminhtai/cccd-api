import unittest

from routes.cccd import cccd_bp
from app import create_app


class TestPlausibility(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_birth_year_in_future_flagged(self):
        # gender code 3 => female, century 21 => 20xx; yy=99 => 2099
        resp = self.client.post("/v1/cccd/parse", json={"cccd": "052399012345"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["is_valid_format"])
        self.assertFalse(body["is_plausible"])
        self.assertIn("birth_year_in_future", body["warnings"])


if __name__ == "__main__":
    unittest.main()


