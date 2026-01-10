"""
CCCD API Python SDK
===================
Python SDK để gọi CCCD API một cách dễ dàng.
"""

from __future__ import annotations

import json
from typing import Literal, Optional
from dataclasses import dataclass

try:
    import requests
except ImportError:
    raise ImportError(
        "requests library is required. Install with: pip install requests"
    )


@dataclass
class ParseResponse:
    """Response từ API parse CCCD"""
    success: bool
    data: dict | None
    is_valid_format: bool
    is_plausible: bool | None
    province_version: str
    warnings: list[str] | None
    message: str | None = None
    request_id: str | None = None


@dataclass
class ErrorResponse:
    """Error response từ API"""
    success: bool
    is_valid_format: bool
    data: dict | None
    message: str
    request_id: str | None = None


class CCCDAPIError(Exception):
    """Base exception cho CCCD API"""
    pass


class CCCDAPIKeyError(CCCDAPIError):
    """API key không hợp lệ hoặc thiếu"""
    pass


class CCCDValidationError(CCCDAPIError):
    """Validation error (format CCCD không hợp lệ, thiếu field, etc.)"""
    pass


class CCCDRateLimitError(CCCDAPIError):
    """Rate limit exceeded"""
    pass


class CCCDAPI:
    """
    CCCD API Client
    
    Example:
        >>> api = CCCDAPI(api_key="your-api-key")
        >>> result = api.parse("079203012345")
        >>> print(result.data["province_name"])
        Tp. Hồ Chí Minh
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:8000",
        timeout: int = 30,
    ):
        """
        Initialize CCCD API client
        
        Args:
            api_key: API key để authenticate
            base_url: Base URL của API server
            timeout: Request timeout (seconds)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        })
    
    def health_check(self) -> dict:
        """
        Kiểm tra health của API server
        
        Returns:
            dict: {"status": "ok"}
        
        Raises:
            CCCDAPIError: Nếu có lỗi khi gọi API
        """
        url = f"{self.base_url}/health"
        
        try:
            response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise CCCDAPIError(f"Health check failed: {e}")
    
    def parse(
        self,
        cccd: str,
        province_version: Optional[Literal["legacy_63", "current_34"]] = None,
    ) -> ParseResponse:
        """
        Parse CCCD number để lấy thông tin
        
        Args:
            cccd: Số CCCD 12 chữ số
            province_version: Optional. "legacy_63" hoặc "current_34"
        
        Returns:
            ParseResponse: Response từ API
        
        Raises:
            CCCDAPIKeyError: API key không hợp lệ hoặc thiếu (401)
            CCCDValidationError: CCCD format không hợp lệ hoặc thiếu field (400)
            CCCDRateLimitError: Vượt quá rate limit (429)
            CCCDAPIError: Các lỗi khác (500, network, etc.)
        """
        url = f"{self.base_url}/v1/cccd/parse"
        
        payload = {"cccd": cccd}
        if province_version:
            payload["province_version"] = province_version
        
        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
            
            # Handle HTTP errors
            if response.status_code == 401:
                error_data = response.json()
                raise CCCDAPIKeyError(
                    error_data.get("message", "API key không hợp lệ hoặc thiếu.")
                )
            elif response.status_code == 400:
                error_data = response.json()
                raise CCCDValidationError(
                    error_data.get("message", "Validation error")
                )
            elif response.status_code == 429:
                error_data = response.json()
                raise CCCDRateLimitError(
                    error_data.get("message", "Rate limit exceeded")
                )
            elif response.status_code >= 400:
                error_data = response.json()
                raise CCCDAPIError(
                    f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}"
                )
            
            # Success
            data = response.json()
            return ParseResponse(
                success=data.get("success", False),
                data=data.get("data"),
                is_valid_format=data.get("is_valid_format", False),
                is_plausible=data.get("is_plausible"),
                province_version=data.get("province_version", "current_34"),
                warnings=data.get("warnings"),
                message=data.get("message"),
                request_id=data.get("request_id"),
            )
            
        except (CCCDAPIKeyError, CCCDValidationError, CCCDRateLimitError, CCCDAPIError):
            raise
        except requests.exceptions.Timeout:
            raise CCCDAPIError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise CCCDAPIError("Connection error: Không thể kết nối đến API server")
        except requests.exceptions.RequestException as e:
            raise CCCDAPIError(f"Request error: {e}")
        except json.JSONDecodeError as e:
            raise CCCDAPIError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise CCCDAPIError(f"Unexpected error: {e}")
    
    def close(self):
        """Đóng session (cleanup)"""
        self._session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


# Example usage
if __name__ == "__main__":
    # Initialize client
    api = CCCDAPI(api_key="your-api-key-here")
    
    try:
        # Health check
        print("=== Health Check ===")
        health = api.health_check()
        print(f"Status: {health['status']}")
        
        # Parse CCCD
        print("\n=== Parse CCCD ===")
        result = api.parse("079203012345")
        print(f"Success: {result.success}")
        print(f"Province: {result.data['province_name']}")
        print(f"Gender: {result.data['gender']}")
        print(f"Birth Year: {result.data['birth_year']}")
        print(f"Age: {result.data['age']}")
        
        # Parse with province version
        print("\n=== Parse with province_version ===")
        result2 = api.parse("079203012345", province_version="legacy_63")
        print(f"Province: {result2.data['province_name']}")
        
        # Error handling
        print("\n=== Error Handling ===")
        try:
            result3 = api.parse("invalid")
        except CCCDValidationError as e:
            print(f"Validation Error: {e}")
        except CCCDAPIKeyError as e:
            print(f"API Key Error: {e}")
        except CCCDRateLimitError as e:
            print(f"Rate Limit Error: {e}")
        except CCCDAPIError as e:
            print(f"API Error: {e}")
        
        # Context manager usage
        print("\n=== Context Manager ===")
        with CCCDAPI(api_key="your-api-key-here") as api2:
            result4 = api2.parse("079203012345")
            print(f"Province: {result4.data['province_name']}")
        
    except CCCDAPIError as e:
        print(f"Fatal Error: {e}")
        exit(1)
    finally:
        api.close()
