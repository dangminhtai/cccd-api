"""
CCCD API - Python Example
==========================
Example code để gọi CCCD API sử dụng Python requests library
"""

import requests
import json

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_KEY = "your-api-key-here"  # Thay bằng API key của bạn

# Headers
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def parse_cccd(cccd: str, province_version: str | None = None) -> dict:
    """
    Parse CCCD number
    
    Args:
        cccd: Số CCCD 12 chữ số
        province_version: Optional. "legacy_63" hoặc "current_34"
    
    Returns:
        dict: Response từ API
    
    Raises:
        requests.RequestException: Nếu có lỗi khi gọi API
    """
    url = f"{API_BASE_URL}/v1/cccd/parse"
    
    payload = {
        "cccd": cccd
    }
    
    if province_version:
        payload["province_version"] = province_version
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception nếu HTTP error
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.json()}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        raise


def health_check() -> dict:
    """Kiểm tra health của API server"""
    url = f"{API_BASE_URL}/health"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    # 1. Health check
    print("=== Health Check ===")
    try:
        health = health_check()
        print(f"Status: {health['status']}")
    except Exception as e:
        print(f"Health check failed: {e}")
        exit(1)
    
    # 2. Parse CCCD - Basic
    print("\n=== Parse CCCD - Basic ===")
    try:
        result = parse_cccd("079203012345")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Parse failed: {e}")
    
    # 3. Parse CCCD - With province version
    print("\n=== Parse CCCD - With province_version ===")
    try:
        result = parse_cccd("079203012345", province_version="legacy_63")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Parse failed: {e}")
    
    # 4. Handle errors
    print("\n=== Error Handling ===")
    try:
        # Invalid CCCD format
        result = parse_cccd("invalid")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error_data = e.response.json()
            print(f"Bad Request: {error_data.get('message')}")
        else:
            print(f"HTTP Error {e.response.status_code}: {e}")
    except Exception as e:
        print(f"Error: {e}")
