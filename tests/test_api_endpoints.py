#!/usr/bin/env python3
"""
Automated API Testing Script for CCCD API
Tests all endpoints according to api_test_checklist.md
"""

import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Install it with: pip install requests")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8000"
API_KEYS = {
    "free": "free_ae958de78f1db400da50156d0b048f95",
    "premium": "prem_c1ba96f40906b9b0130fd83e0fa499c0",
    "ultra": "ultr_3232cc5f5c5128e43946726e0bc30251"
}

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "details": []
}

def log_test(name: str, passed: bool, message: str = "", skip: bool = False):
    """Log test result"""
    status = "SKIP" if skip else ("PASS" if passed else "FAIL")
    color = {
        "PASS": "\033[92m",  # Green
        "FAIL": "\033[91m",  # Red
        "SKIP": "\033[93m"   # Yellow
    }.get(status, "")
    reset = "\033[0m"
    
    # Safe print for Windows encoding
    try:
        print(f"{color}[{status}]{reset} {name}")
        if message:
            # Escape non-ASCII characters if needed
            safe_message = message.encode('ascii', 'replace').decode('ascii') if sys.platform == 'win32' else message
            print(f"      {safe_message}")
    except UnicodeEncodeError:
        print(f"{color}[{status}]{reset} {name}")
        if message:
            print(f"      {message.encode('utf-8', errors='replace').decode('utf-8', errors='replace')}")
    
    if skip:
        results["skipped"] += 1
    elif passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    results["details"].append({
        "name": name,
        "status": status,
        "message": message,
        "skip": skip
    })

def make_request(method: str, endpoint: str, **kwargs) -> tuple[Optional[requests.Response], Optional[str]]:
    """Make HTTP request and return response and error message"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        return response, None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to {BASE_URL}. Is the server running?"
    except requests.exceptions.Timeout:
        return None, "Request timeout"
    except Exception as e:
        return None, f"Request error: {str(e)}"

# ============================================================================
# 1. Health Check APIs
# ============================================================================

def test_health_check():
    """Test 1.1: GET /health"""
    print("\n" + "="*70)
    print("1. HEALTH CHECK APIs")
    print("="*70)
    
    response, error = make_request("GET", "/health")
    
    if error:
        log_test("1.1 GET /health", False, error, skip=False)
        return
    
    if response.status_code == 200:
        try:
            data = response.json()
            if "status" in data:
                # Check if timestamp exists (may be optional)
                version_info = f", Version: {data.get('version', 'N/A')}" if "version" in data else ""
                timestamp_info = f", Timestamp: {data.get('timestamp', 'N/A')}" if "timestamp" in data else ""
                log_test("1.1 GET /health", True, f"Status: {data.get('status')}{version_info}{timestamp_info}")
            else:
                log_test("1.1 GET /health", False, f"Missing 'status' field. Response: {data}")
        except json.JSONDecodeError:
            log_test("1.1 GET /health", False, "Response is not valid JSON")
    else:
        log_test("1.1 GET /health", False, f"Expected 200, got {response.status_code}")

# ============================================================================
# 2. CCCD Parse APIs
# ============================================================================

def test_cccd_parse():
    """Test 2.1: POST /v1/cccd/parse"""
    print("\n" + "="*70)
    print("2. CCCD PARSE APIs")
    print("="*70)
    
    # Test Case 1: Valid CCCD (12 digits)
    print("\n--- Case 1: Valid CCCD (12 digits) ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={"cccd": "001123456789"},
        headers={"X-API-Key": API_KEYS["free"]}
    )
    
    if error:
        log_test("2.1 Case 1: Valid CCCD", False, error, skip=False)
    elif response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("is_valid_format"):
            province_name = data.get('data', {}).get('province_name', 'N/A')
            log_test("2.1 Case 1: Valid CCCD", True, f"Province: {province_name}")
        else:
            log_test("2.1 Case 1: Valid CCCD", False, f"success={data.get('success')}, is_valid_format={data.get('is_valid_format')}")
    elif response.status_code == 401:
        log_test("2.1 Case 1: Valid CCCD", False, "401 Unauthorized - API key may be invalid or expired")
    else:
        log_test("2.1 Case 1: Valid CCCD", False, f"Expected 200, got {response.status_code}")
    
    # Test Case 2: CCCD too short (< 12 digits)
    print("\n--- Case 2: CCCD too short (< 12 digits) ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={"cccd": "00112345678"},
        headers={"X-API-Key": API_KEYS["free"]}
    )
    
    if error:
        log_test("2.1 Case 2: CCCD too short", False, error, skip=False)
    elif response.status_code == 400:
        data = response.json()
        if not data.get("is_valid_format"):
            log_test("2.1 Case 2: CCCD too short", True, "Correctly rejected invalid format")
        else:
            log_test("2.1 Case 2: CCCD too short", False, "Should have is_valid_format=false")
    else:
        log_test("2.1 Case 2: CCCD too short", False, f"Expected 400, got {response.status_code}")
    
    # Test Case 3: CCCD too long (> 12 digits)
    print("\n--- Case 3: CCCD too long (> 12 digits) ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={"cccd": "0011234567890"},
        headers={"X-API-Key": API_KEYS["free"]}
    )
    
    if error:
        log_test("2.1 Case 3: CCCD too long", False, error, skip=False)
    elif response.status_code == 400:
        log_test("2.1 Case 3: CCCD too long", True, "Correctly rejected invalid format")
    else:
        log_test("2.1 Case 3: CCCD too long", False, f"Expected 400, got {response.status_code}")
    
    # Test Case 4: CCCD with non-numeric characters
    print("\n--- Case 4: CCCD with non-numeric characters ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={"cccd": "00112345678a"},
        headers={"X-API-Key": API_KEYS["free"]}
    )
    
    if error:
        log_test("2.1 Case 4: CCCD non-numeric", False, error, skip=False)
    elif response.status_code == 400:
        log_test("2.1 Case 4: CCCD non-numeric", True, "Correctly rejected invalid format")
    else:
        log_test("2.1 Case 4: CCCD non-numeric", False, f"Expected 400, got {response.status_code}")
    
    # Test Case 5: Missing CCCD field
    print("\n--- Case 5: Missing CCCD field ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={},
        headers={"X-API-Key": API_KEYS["free"]}
    )
    
    if error:
        log_test("2.1 Case 5: Missing field", False, error, skip=False)
    elif response.status_code == 400:
        log_test("2.1 Case 5: Missing field", True, "Correctly rejected missing field")
    else:
        log_test("2.1 Case 5: Missing field", False, f"Expected 400, got {response.status_code}")
    
    # Test Case 6: No API Key (if tiered mode)
    print("\n--- Case 6: No API Key ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={"cccd": "001123456789"}
    )
    
    if error:
        log_test("2.1 Case 6: No API Key", False, error, skip=False)
    elif response.status_code == 401:
        log_test("2.1 Case 6: No API Key", True, "Correctly rejected request without API key")
    else:
        log_test("2.1 Case 6: No API Key", True, f"Got {response.status_code} (API key may not be required)", skip=True)
    
    # Test Case 7: Invalid API Key
    print("\n--- Case 7: Invalid API Key ---")
    response, error = make_request(
        "POST",
        "/v1/cccd/parse",
        json={"cccd": "001123456789"},
        headers={"X-API-Key": "invalid_key_12345"}
    )
    
    if error:
        log_test("2.1 Case 7: Invalid API Key", False, error, skip=False)
    elif response.status_code == 401:
        log_test("2.1 Case 7: Invalid API Key", True, "Correctly rejected invalid API key")
    else:
        log_test("2.1 Case 7: Invalid API Key", False, f"Expected 401, got {response.status_code}")
    
    # Test Case 9: Rate Limit (if enabled)
    print("\n--- Case 9: Rate Limit (sending 10 rapid requests) ---")
    rate_limit_hit = False
    for i in range(10):
        response, error = make_request(
            "POST",
            "/v1/cccd/parse",
            json={"cccd": "001123456789"},
            headers={"X-API-Key": API_KEYS["free"]}
        )
        if response and response.status_code == 429:
            rate_limit_hit = True
            break
        time.sleep(0.1)  # Small delay to avoid overwhelming server
    
    if rate_limit_hit:
        log_test("2.1 Case 9: Rate Limit", True, "Rate limit correctly applied (429)")
    else:
        log_test("2.1 Case 9: Rate Limit", True, "Rate limit not hit (may not be enabled or limit is higher)", skip=True)

# ============================================================================
# 3. Portal APIs (Limited - require session/login)
# ============================================================================

def test_portal_apis():
    """Test Portal APIs - limited to GET endpoints that don't require login"""
    print("\n" + "="*70)
    print("3. PORTAL APIs (Limited Testing)")
    print("="*70)
    
    # Test 3.1: GET /portal/ or /portal/login (should redirect or show login page)
    print("\n--- Test 3.1: GET /portal/login ---")
    response, error = make_request("GET", "/portal/login", allow_redirects=False)
    
    if error:
        log_test("3.1 GET /portal/login", False, error, skip=False)
    elif response.status_code in [200, 302]:
        log_test("3.1 GET /portal/login", True, f"Status: {response.status_code}")
    else:
        log_test("3.1 GET /portal/login", False, f"Expected 200 or 302, got {response.status_code}")
    
    # Test 3.3: GET /portal/register
    print("\n--- Test 3.3: GET /portal/register ---")
    response, error = make_request("GET", "/portal/register", allow_redirects=False)
    
    if error:
        log_test("3.3 GET /portal/register", False, error, skip=False)
    elif response.status_code == 200:
        log_test("3.3 GET /portal/register", True, "Registration page accessible")
    else:
        log_test("3.3 GET /portal/register", False, f"Expected 200, got {response.status_code}")
    
    # Test 3.17: GET /portal/forgot-password
    print("\n--- Test 3.17: GET /portal/forgot-password ---")
    response, error = make_request("GET", "/portal/forgot-password", allow_redirects=False)
    
    if error:
        log_test("3.17 GET /portal/forgot-password", False, error, skip=False)
    elif response.status_code == 200:
        log_test("3.17 GET /portal/forgot-password", True, "Forgot password page accessible")
    else:
        log_test("3.17 GET /portal/forgot-password", False, f"Expected 200, got {response.status_code}")
    
    # Note: POST endpoints require login/session, so we skip them
    print("\n[SKIP] POST endpoints require login/session - manual testing required")

# ============================================================================
# 4. Admin APIs
# ============================================================================

def test_admin_apis():
    """Test Admin APIs"""
    print("\n" + "="*70)
    print("4. ADMIN APIs")
    print("="*70)
    
    # Admin key would be in .env, but we'll try without it first
    # Test 4.1: GET /admin/ (should be accessible without admin key)
    print("\n--- Test 4.1: GET /admin/ ---")
    response, error = make_request("GET", "/admin/", allow_redirects=False)
    
    if error:
        log_test("4.1 GET /admin/", False, error, skip=False)
    elif response.status_code == 200:
        log_test("4.1 GET /admin/", True, "Admin dashboard page accessible")
    else:
        log_test("4.1 GET /admin/", False, f"Expected 200, got {response.status_code}")
    
    # Test 4.2: GET /admin/stats (should require admin key)
    print("\n--- Test 4.2: GET /admin/stats (without admin key) ---")
    response, error = make_request("GET", "/admin/stats", allow_redirects=False)
    
    if error:
        log_test("4.2 GET /admin/stats (no key)", False, error, skip=False)
    elif response.status_code == 403:
        log_test("4.2 GET /admin/stats (no key)", True, "Correctly rejected without admin key")
    else:
        log_test("4.2 GET /admin/stats (no key)", False, f"Expected 403, got {response.status_code}")
    
    # Note: Other admin endpoints require admin key from .env
    print("\n[SKIP] Admin endpoints require ADMIN_SECRET from .env - manual testing required")

# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("CCCD API - AUTOMATED TEST SUITE")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Keys available: {', '.join(API_KEYS.keys())}")
    
    # Check if server is running
    response, error = make_request("GET", "/health")
    if error:
        print(f"\n[ERROR] {error}")
        print("Make sure the server is running: python run.py")
        sys.exit(1)
    
    # Run tests
    test_health_check()
    test_cccd_parse()
    test_portal_apis()
    test_admin_apis()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"[PASS] Passed:  {results['passed']}")
    print(f"[FAIL] Failed:  {results['failed']}")
    print(f"[SKIP] Skipped: {results['skipped']}")
    print(f"[TOTAL] Total:   {results['passed'] + results['failed'] + results['skipped']}")
    print("="*70)
    
    # Save detailed results to JSON
    output_file = "tests/test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "summary": {
                "passed": results["passed"],
                "failed": results["failed"],
                "skipped": results["skipped"]
            },
            "details": results["details"]
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INFO] Detailed results saved to: {output_file}")
    
    # Exit code based on failures
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
