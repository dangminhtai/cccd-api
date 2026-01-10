"""
Test script để verify email sending functionality
Usage: python scripts/test_email.py
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from services.email_service import send_email, send_welcome_email, send_verification_email, send_password_reset_email


def test_basic_email():
    """Test basic email sending"""
    print("Testing basic email sending...")
    
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    if not test_email or test_email == "test@example.com":
        print("⚠️  Please set TEST_EMAIL in .env file")
        return False
    
    html_content = """
    <html>
    <body>
        <h2>Test Email</h2>
        <p>This is a test email from CCCD API email service.</p>
        <p>If you receive this email, the email system is working correctly!</p>
    </body>
    </html>
    """
    
    result = send_email(
        to_email=test_email,
        subject="Test Email - CCCD API",
        html_content=html_content,
        to_name="Test User"
    )
    
    if result:
        print(f"✅ Email sent successfully to {test_email}")
        return True
    else:
        print(f"❌ Failed to send email to {test_email}")
        return False


def test_welcome_email():
    """Test welcome email"""
    print("\nTesting welcome email...")
    
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    if not test_email or test_email == "test@example.com":
        print("⚠️  Please set TEST_EMAIL in .env file")
        return False
    
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    verification_url = f"{base_url}/portal/verify-email/test-token-123"
    
    result = send_welcome_email(
        to_email=test_email,
        to_name="Test User",
        verification_url=verification_url
    )
    
    if result:
        print(f"✅ Welcome email sent successfully to {test_email}")
        return True
    else:
        print(f"❌ Failed to send welcome email to {test_email}")
        return False


def test_verification_email():
    """Test verification email"""
    print("\nTesting verification email...")
    
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    if not test_email or test_email == "test@example.com":
        print("⚠️  Please set TEST_EMAIL in .env file")
        return False
    
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    verification_url = f"{base_url}/portal/verify-email/test-token-123"
    
    result = send_verification_email(
        to_email=test_email,
        to_name="Test User",
        verification_url=verification_url
    )
    
    if result:
        print(f"✅ Verification email sent successfully to {test_email}")
        return True
    else:
        print(f"❌ Failed to send verification email to {test_email}")
        return False


def test_password_reset_email():
    """Test password reset email"""
    print("\nTesting password reset email...")
    
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    if not test_email or test_email == "test@example.com":
        print("⚠️  Please set TEST_EMAIL in .env file")
        return False
    
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    reset_url = f"{base_url}/portal/reset-password/test-reset-token-123"
    
    result = send_password_reset_email(
        to_email=test_email,
        to_name="Test User",
        reset_url=reset_url
    )
    
    if result:
        print(f"✅ Password reset email sent successfully to {test_email}")
        return True
    else:
        print(f"❌ Failed to send password reset email to {test_email}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CCCD API - Email Service Test")
    print("=" * 60)
    
    # Check email provider
    email_provider = os.getenv("EMAIL_PROVIDER", "sendgrid")
    print(f"\nEmail Provider: {email_provider}")
    
    if email_provider == "sendgrid":
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            print("❌ SENDGRID_API_KEY not found in .env file")
            print("   Please set SENDGRID_API_KEY in .env file")
            sys.exit(1)
        else:
            print("✅ SENDGRID_API_KEY found")
    elif email_provider == "smtp":
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        if not smtp_username or not smtp_password:
            print("❌ SMTP_USERNAME or SMTP_PASSWORD not found in .env file")
            print("   Please set SMTP credentials in .env file")
            sys.exit(1)
        else:
            print("✅ SMTP credentials found")
    
    print("\n" + "=" * 60)
    
    # Run tests
    results = []
    results.append(("Basic Email", test_basic_email()))
    results.append(("Welcome Email", test_welcome_email()))
    results.append(("Verification Email", test_verification_email()))
    results.append(("Password Reset Email", test_password_reset_email()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Email system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check your email configuration.")
        sys.exit(1)
