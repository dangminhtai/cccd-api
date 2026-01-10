# CCCD API Documentation

Tài liệu đầy đủ về CCCD API - Parse thông tin từ số CCCD (Căn cước công dân) 12 chữ số của Việt Nam.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Rate Limits](#rate-limits)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [SDK Libraries](#sdk-libraries)
- [Postman Collection](#postman-collection)
- [OpenAPI Specification](#openapi-specification)

## Overview

CCCD API cung cấp endpoint để parse số CCCD 12 chữ số và lấy thông tin:

- **Mã tỉnh/thành phố** (province_code)
- **Tên tỉnh/thành phố** (province_name)
- **Giới tính** (gender)
- **Năm sinh** (birth_year)
- **Thế kỷ** (century)
- **Tuổi** (age)

### Base URL

- **Development**: `http://127.0.0.1:8000`
- **Production**: `https://api.cccd-api.com`

### API Version

- **Current Version**: `v1`
- **API Endpoint**: `/v1/cccd/parse`

## Quick Start

### 1. Get API Key

Đăng ký tài khoản tại [Customer Portal](http://127.0.0.1:8000/portal/register) để lấy API key.

### 2. Make a Request

```bash
curl -X POST http://127.0.0.1:8000/v1/cccd/parse \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"cccd": "079203012345"}'
```

### 3. Response

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

## API Endpoints

### Health Check

**Endpoint**: `GET /health`

Kiểm tra trạng thái API server.

**Response:**
```json
{
  "status": "ok"
}
```

### Parse CCCD

**Endpoint**: `POST /v1/cccd/parse`

Parse số CCCD 12 chữ số để lấy thông tin.

**Headers:**
- `X-API-Key`: API key (required)
- `Content-Type`: `application/json` (required)

**Request Body:**
```json
{
  "cccd": "079203012345",
  "province_version": "current_34"  // Optional: "legacy_63" or "current_34"
}
```

**Response (Success):**
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

**Response (Error):**
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
}
```

## Authentication

API sử dụng API key authentication qua header `X-API-Key`.

### Get API Key

1. Đăng ký tài khoản tại [Customer Portal](http://127.0.0.1:8000/portal/register)
2. Đăng nhập và tạo API key tại [Keys Management](http://127.0.0.1:8000/portal/keys)
3. Copy API key và sử dụng trong requests

### Usage

```bash
curl -X POST http://127.0.0.1:8000/v1/cccd/parse \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"cccd": "079203012345"}'
```

## Rate Limits

Rate limits được áp dụng theo tier của API key:

| Tier | Requests per Minute | Requests per Day |
|------|---------------------|------------------|
| **Free** | 10 | 1,000 |
| **Premium** | 100 | Unlimited |
| **Ultra** | 1,000 | Unlimited |

### Rate Limit Headers

Response headers chứa thông tin về rate limit:

- `X-RateLimit-Remaining`: Số requests còn lại
- `X-RateLimit-Reset`: Unix timestamp khi window reset
- `Retry-After`: Số giây cần chờ (khi 429)

### Handling Rate Limits

Xem chi tiết tại [Rate Limits Documentation](RATE_LIMITS.md).

## Error Handling

API trả về JSON format cho tất cả errors:

```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "Error message",
  "request_id": "abc12345"  // Optional: for debugging
}
```

### HTTP Status Codes

- `200 OK`: Request thành công
- `400 Bad Request`: Validation error (CCCD format không hợp lệ, thiếu field)
- `401 Unauthorized`: API key không hợp lệ hoặc thiếu
- `405 Method Not Allowed`: Method không được hỗ trợ (chỉ POST được phép)
- `429 Too Many Requests`: Vượt quá rate limit
- `500 Internal Server Error`: Lỗi server

Xem chi tiết tại [Error Codes Reference](ERROR_CODES.md).

## Code Examples

### Python

```python
import requests

url = "http://127.0.0.1:8000/v1/cccd/parse"
headers = {
    "X-API-Key": "your-api-key-here",
    "Content-Type": "application/json"
}
data = {
    "cccd": "079203012345"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

Xem full example tại [Python Example](examples/python_example.py).

### JavaScript

```javascript
fetch('http://127.0.0.1:8000/v1/cccd/parse', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key-here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    cccd: '079203012345'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

Xem full example tại [JavaScript Example](examples/javascript_example.js).

### cURL

```bash
curl -X POST http://127.0.0.1:8000/v1/cccd/parse \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"cccd": "079203012345"}'
```

Xem full example tại [cURL Example](examples/curl_example.sh).

### PHP

```php
<?php
$url = 'http://127.0.0.1:8000/v1/cccd/parse';
$data = json_encode(['cccd' => '079203012345']);

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: your-api-key-here',
    'Content-Type: application/json'
]);

$response = curl_exec($ch);
curl_close($ch);
echo $response;
?>
```

Xem full example tại [PHP Example](examples/php_example.php).

## SDK Libraries

### Python SDK

Python SDK để gọi API một cách dễ dàng.

**Installation:**
```bash
pip install requests
# Hoặc copy file sdk/python/cccd_api.py vào project
```

**Usage:**
```python
from cccd_api import CCCDAPI

api = CCCDAPI(api_key="your-api-key-here")

result = api.parse("079203012345")
print(result.data['province_name'])  # Tp. Hồ Chí Minh

api.close()
```

Xem chi tiết tại [Python SDK README](../../sdk/python/README.md).

### Node.js SDK

(Coming soon)

## Postman Collection

Import Postman collection để test API:

1. Download [CCCD_API.postman_collection.json](../../postman/CCCD_API.postman_collection.json)
2. Import vào Postman
3. Set environment variables:
   - `base_url`: `http://127.0.0.1:8000`
   - `api_key`: Your API key

## OpenAPI Specification

OpenAPI 3.0 specification cho API:

- [OpenAPI Spec](openapi.yaml)

### Swagger UI

Truy cập Swagger UI để xem interactive API documentation:

- **Development**: `http://127.0.0.1:8000/api-docs`
- **Production**: `https://api.cccd-api.com/api-docs`

## Additional Resources

- [Error Codes Reference](ERROR_CODES.md)
- [Rate Limits Documentation](RATE_LIMITS.md)
- [Python SDK](../../sdk/python/README.md)
- [Postman Collection](../../postman/CCCD_API.postman_collection.json)

## Support

Nếu cần hỗ trợ:

- **Email**: support@cccd-api.com
- **Documentation**: [API Docs](README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/cccd-api/issues)

## License

MIT License - Xem [LICENSE](../../LICENSE) để biết thêm chi tiết.
