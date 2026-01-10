# Error Codes Reference

Tài liệu chi tiết về tất cả error codes và cách xử lý.

## HTTP Status Codes

### 200 OK
Request thành công.

**Response:**
```json
{
  "success": true,
  "data": {
    "province_code": "079",
    "province_name": "Tp. Hồ Chí Minh",
    "gender": "Nam",
    "birth_year": 2003,
    "century": 21,
    "age": 21
  },
  "is_valid_format": true,
  "is_plausible": true,
  "province_version": "current_34",
  "warnings": null
}
```

### 400 Bad Request
Validation error - CCCD format không hợp lệ hoặc thiếu field.

**Possible Messages:**
- `"Thiếu trường cccd."` - Field `cccd` không có trong request body
- `"CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."` - CCCD không đúng format
- `"province_version không hợp lệ (chỉ nhận legacy_63 hoặc current_34)."` - province_version không hợp lệ

**Response:**
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
}
```

**Handling:**
```python
# Python
try:
    result = api.parse("invalid")
except CCCDValidationError as e:
    print(f"Validation Error: {e}")
```

### 401 Unauthorized
API key không hợp lệ hoặc thiếu.

**Response:**
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "API key không hợp lệ hoặc thiếu."
}
```

**Handling:**
- Kiểm tra header `X-API-Key` có được gửi không
- Kiểm tra API key có đúng không
- Kiểm tra API key có còn active không (nếu dùng tiered mode)

### 405 Method Not Allowed
Method không được hỗ trợ. Chỉ POST được phép cho `/v1/cccd/parse`.

**Response:**
```json
{
  "error": "Method not allowed"
}
```

### 429 Too Many Requests
Vượt quá rate limit.

**Headers:**
- `Retry-After`: Số giây cần chờ trước khi retry

**Response:**
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "Quá nhiều request. Giới hạn: 10 per 1 minute"
}
```

**Rate Limits:**
- **Free**: 10 requests/minute
- **Premium**: 100 requests/minute
- **Ultra**: 1000 requests/minute

**Handling:**
```python
import time

try:
    result = api.parse("079203012345")
except CCCDRateLimitError as e:
    print(f"Rate Limit: {e}")
    # Wait before retry
    time.sleep(60)
    result = api.parse("079203012345")
```

### 500 Internal Server Error
Lỗi server (không mong muốn).

**Response:**
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "Lỗi hệ thống. Vui lòng thử lại sau.",
  "request_id": "abc12345"
}
```

**Handling:**
- Retry với exponential backoff
- Log `request_id` để báo cáo với support

## Response Warnings

Warnings được trả về trong field `warnings` (array of strings) khi có vấn đề không nghiêm trọng.

### `province_version_alias_legacy_64`
Dùng alias `legacy_64` thay vì `legacy_63`. API đã tự động chuyển đổi.

### `province_version_alias_current_63`
Dùng alias `current_63` thay vì `current_34`. API đã tự động chuyển đổi.

### `province_code_not_found`
Không tìm thấy `province_name` cho `province_code` trong mapping. `province_name` sẽ là `null`.

### `birth_year_in_future`
Năm sinh trong tương lai (không hợp lý). `is_plausible` sẽ là `false` và `age` sẽ là `null`.

**Example:**
```json
{
  "success": true,
  "data": {
    "province_code": "079",
    "province_name": null,
    "gender": "Nam",
    "birth_year": 2025,
    "century": 21,
    "age": null
  },
  "is_valid_format": true,
  "is_plausible": false,
  "province_version": "current_34",
  "warnings": [
    "province_code_not_found",
    "birth_year_in_future"
  ]
}
```

## Best Practices

### Error Handling

1. **Always check `success` field**:
   ```python
   response = api.parse("079203012345")
   if not response.success:
       print(f"Error: {response.message}")
   ```

2. **Use try-except for API calls**:
   ```python
   try:
       result = api.parse("079203012345")
       print(result.data)
   except CCCDAPIError as e:
       print(f"API Error: {e}")
   ```

3. **Handle rate limits with retry**:
   ```python
   import time
   from cccd_api import CCCDRateLimitError

   max_retries = 3
   for i in range(max_retries):
       try:
           result = api.parse("079203012345")
           break
       except CCCDRateLimitError:
           if i < max_retries - 1:
               time.sleep(60)  # Wait 1 minute
           else:
               raise
   ```

4. **Log request_id for debugging**:
   ```python
   try:
       result = api.parse("079203012345")
   except CCCDAPIError as e:
       if hasattr(e, 'request_id'):
           logger.error(f"Request ID: {e.request_id}, Error: {e}")
   ```

### Validation Before API Call

Validate CCCD format trước khi gọi API để tránh 400 errors:

```python
import re

def validate_cccd(cccd: str) -> bool:
    """Validate CCCD format"""
    return bool(re.match(r'^[0-9]{12}$', cccd))

# Before API call
cccd = "079203012345"
if not validate_cccd(cccd):
    print("Invalid CCCD format")
else:
    result = api.parse(cccd)
```

### Retry Logic

Implement retry logic cho network errors và 500 errors:

```python
import time
import random

def parse_with_retry(api, cccd, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api.parse(cccd)
        except CCCDAPIError as e:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
```

## Support

Nếu gặp lỗi không được document ở đây, vui lòng:
1. Kiểm tra `request_id` trong response
2. Liên hệ support@cccd-api.com với request_id và error message
