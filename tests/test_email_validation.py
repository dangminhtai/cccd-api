"""
Test email validation logic
"""
import re
import unittest


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


class TestEmailValidation(unittest.TestCase):
    def test_valid_emails(self):
        """Email hợp lệ"""
        valid = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_123@test-domain.com",
            "test@sub.domain.com",
        ]
        for email in valid:
            self.assertTrue(validate_email(email), f"'{email}' should be valid")

    def test_invalid_emails(self):
        """Email không hợp lệ"""
        invalid = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@com",
            "user name@example.com",
            "",
            "user@example",
            "user@@example.com",
        ]
        for email in invalid:
            self.assertFalse(validate_email(email), f"'{email}' should be invalid")


if __name__ == "__main__":
    unittest.main()

