"""
Pytest configuration and hooks for CCCD API tests
"""
import pytest


def pytest_sessionfinish(session, exitstatus):
    """Hook to print custom message after all tests complete"""
    if exitstatus == 0:
        print("\n" + "=" * 70)
        print("[SUCCESS]: All tests passed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("[FAIL]: Some tests failed!")
        print("=" * 70)
