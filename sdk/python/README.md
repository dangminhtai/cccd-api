# CCCD API Python SDK

Python SDK để gọi CCCD API một cách dễ dàng.

## Installation

```bash
pip install requests
```

Hoặc copy file `cccd_api.py` vào project của bạn.

## Usage

### Basic Usage

```python
from cccd_api import CCCDAPI

# Initialize client
api = CCCDAPI(api_key="your-api-key-here")

# Parse CCCD
result = api.parse("079203012345")
print(f"Province: {result.data['province_name']}")
print(f"Gender: {result.data['gender']}")
print(f"Birth Year: {result.data['birth_year']}")
print(f"Age: {result.data['age']}")

# Close session
api.close()
```

### Context Manager

```python
with CCCDAPI(api_key="your-api-key-here") as api:
    result = api.parse("079203012345")
    print(result.data)
```

### With Province Version

```python
api = CCCDAPI(api_key="your-api-key-here")

# Use legacy_63 province mapping
result = api.parse("079203012345", province_version="legacy_63")
print(result.data['province_name'])

api.close()
```

### Error Handling

```python
from cccd_api import (
    CCCDAPI,
    CCCDAPIKeyError,
    CCCDValidationError,
    CCCDRateLimitError,
    CCCDAPIError
)

api = CCCDAPI(api_key="your-api-key-here")

try:
    result = api.parse("079203012345")
    print(result.data)
except CCCDValidationError as e:
    print(f"Validation Error: {e}")
except CCCDAPIKeyError as e:
    print(f"API Key Error: {e}")
except CCCDRateLimitError as e:
    print(f"Rate Limit Error: {e}")
except CCCDAPIError as e:
    print(f"API Error: {e}")
finally:
    api.close()
```

### Health Check

```python
api = CCCDAPI(api_key="your-api-key-here")

health = api.health_check()
print(f"Status: {health['status']}")

api.close()
```

### Custom Base URL

```python
# For production server
api = CCCDAPI(
    api_key="your-api-key-here",
    base_url="https://api.cccd-api.com"
)

# For local development
api = CCCDAPI(
    api_key="your-api-key-here",
    base_url="http://127.0.0.1:8000"
)
```

### Custom Timeout

```python
api = CCCDAPI(
    api_key="your-api-key-here",
    timeout=60  # 60 seconds
)
```

## Response Object

### ParseResponse

```python
@dataclass
class ParseResponse:
    success: bool
    data: dict | None  # Parsed CCCD data
    is_valid_format: bool
    is_plausible: bool | None
    province_version: str
    warnings: list[str] | None
    message: str | None = None
    request_id: str | None = None
```

### Data Structure

```python
result.data = {
    "province_code": "079",
    "province_name": "Tp. Hồ Chí Minh",
    "gender": "Nam",
    "birth_year": 2003,
    "century": 21,
    "age": 21
}
```

## Exceptions

- `CCCDAPIError`: Base exception cho tất cả API errors
- `CCCDAPIKeyError`: API key không hợp lệ hoặc thiếu (401)
- `CCCDValidationError`: Validation error (400)
- `CCCDRateLimitError`: Rate limit exceeded (429)

## Requirements

- Python 3.7+
- requests library

## License

MIT
