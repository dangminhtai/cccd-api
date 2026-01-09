# 🔒 Hướng Dẫn Kiểm Thử Bảo Mật (Penetration Testing Guide)

**Mục tiêu:** Kiểm tra ứng dụng CCCD API như một hacker bên ngoài để phát hiện các lỗ hổng bảo mật tiềm ẩn.

**Lưu ý:** Chỉ test trên môi trường test/local của chính bạn. KHÔNG test trên hệ thống production mà không có sự cho phép.

---

## 📋 Mục Lục

1. [Thông Tin Tổng Quan](#1-thông-tin-tổng-quan)
2. [Reconnaissance - Thu Thập Thông Tin](#2-reconnaissance---thu-thập-thông-tin)
3. [Authentication Bypass](#3-authentication-bypass)
4. [Input Validation & Injection](#4-input-validation--injection)
5. [Rate Limiting Bypass](#5-rate-limiting-bypass)
6. [Information Disclosure](#6-information-disclosure)
7. [Admin Endpoint Security](#7-admin-endpoint-security)
8. [API Key Enumeration & Brute Force](#8-api-key-enumeration--brute-force)
9. [Denial of Service (DoS)](#9-denial-of-service-dos)
10. [CORS & Headers Security](#10-cors--headers-security)
11. [SQL Injection (Tiered Mode)](#11-sql-injection-tiered-mode)
12. [Logging & Data Leakage](#12-logging--data-leakage)
13. [Checklist Tổng Kết](#13-checklist-tổng-kết)

---

## 1. Thông Tin Tổng Quan

### 1.1. Hiểu Rõ Ứng Dụng

Trước khi test, bạn cần hiểu:
- **API Endpoints:** `/v1/cccd/parse`, `/health`, `/admin/*`
- **Authentication:** API Key (header `X-API-Key`)
- **Admin Auth:** Admin Secret (header `X-Admin-Key`)
- **Rate Limiting:** 30 req/min (default), có thể theo tier
- **Database:** MySQL (chỉ khi `API_KEY_MODE=tiered`)

### 1.2. Công Cụ Cần Thiết

```bash
# PowerShell (Windows)
# curl, Invoke-RestMethod đã có sẵn

# Hoặc cài đặt:
# - Postman / Insomnia
# - Burp Suite (cho advanced testing)
# - SQLMap (cho SQL injection testing)
# - Python với requests library
```

---

## 2. Reconnaissance - Thu Thập Thông Tin

### Test 2.1: Khám Phá Endpoints

**Mục tiêu:** Tìm tất cả các endpoint có thể truy cập.

```powershell
# Test các endpoint có thể có
$base = "http://127.0.0.1:8000"

# Health check (thường không yêu cầu auth)
Invoke-RestMethod -Uri "$base/health" -Method GET

# Root endpoint
Invoke-RestMethod -Uri "$base/" -Method GET

# Demo page
Invoke-RestMethod -Uri "$base/demo" -Method GET

# API endpoint (có thể yêu cầu auth)
Invoke-RestMethod -Uri "$base/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "079203012345"}'

# Admin endpoints (thử xem có leak không)
Invoke-RestMethod -Uri "$base/admin/" -Method GET
Invoke-RestMethod -Uri "$base/admin/stats" -Method GET
```

**Kỳ vọng:**
- ✅ Health check trả 200 (OK)
- ✅ API endpoint không có key → 401
- ✅ Admin endpoint không có key → 403 hoặc 503

**Cảnh báo nếu:**
- ❌ Admin endpoint trả 200 mà không cần auth
- ❌ Có endpoint `/debug`, `/admin/debug`, `/test` trả stacktrace
- ❌ Endpoints trả lỗi chi tiết về cấu trúc database

### Test 2.2: HTTP Methods Enumeration

**Mục tiêu:** Kiểm tra các HTTP methods được phép.

```powershell
$methods = @("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD")

foreach ($method in $methods) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method $method -ErrorAction Stop
        Write-Host "$method : $($response.StatusCode)"
    } catch {
        Write-Host "$method : $($_.Exception.Response.StatusCode.value__)"
    }
}
```

**Kỳ vọng:**
- ✅ Chỉ POST được phép cho `/v1/cccd/parse`
- ✅ GET cho `/health`, `/demo`
- ❌ Cảnh báo nếu PUT/DELETE được chấp nhận (có thể có endpoint ẩn)

### Test 2.3: Error Messages Analysis

**Mục tiêu:** Thu thập thông tin từ error messages.

```powershell
# Test với input sai để xem error message
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{}' | ConvertTo-Json

# Test với format sai
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": null}' | ConvertTo-Json
```

**Kỳ vọng:**
- ✅ Error message generic, không lộ thông tin internal
- ❌ Cảnh báo nếu lộ: stacktrace, đường dẫn file, version Python/Flask, SQL error

---

## 3. Authentication Bypass

### Test 3.1: Không Gửi API Key

```powershell
# Không có header X-API-Key
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "079203012345"}'
```

**Kỳ vọng:**
- ✅ Nếu `API_KEY` được set trong `.env` → 401
- ❌ Nếu `API_KEY` trống → 200 (có thể là lỗ hổng nếu đây là production)

### Test 3.2: API Key Bypass Techniques

```powershell
$body = '{"cccd": "079203012345"}'

# Test 1: API key rỗng
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=""} -Body $body

# Test 2: API key là null
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="null"} -Body $body

# Test 3: SQL injection trong API key
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="' OR '1'='1"} -Body $body

# Test 4: API key với whitespace
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=" yourkey "} -Body $body

# Test 5: Case sensitivity
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="YOURKEY"} -Body $body
```

**Kỳ vọng:**
- ✅ Tất cả đều trả 401
- ❌ Cảnh báo nếu có trường hợp nào bypass được

### Test 3.3: Header Injection & Parameter Pollution

```powershell
# Test nhiều X-API-Key headers
$headers = @{
    "X-API-Key" = @("wrongkey", "yourkey")
    "Content-Type" = "application/json"
}
# Note: PowerShell không hỗ trợ duplicate headers, cần dùng curl hoặc Burp

# Test với Authorization header (có thể có fallback)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"Authorization"="Bearer fake"} -Body $body
```

**Kỳ vọng:**
- ✅ Chỉ `X-API-Key` được chấp nhận
- ❌ Cảnh báo nếu `Authorization` header cũng hoạt động (inconsistency)

---

## 4. Input Validation & Injection

### Test 4.1: SQL Injection trong Input

**Mục tiêu:** Kiểm tra xem input có được sanitize đúng không.

```powershell
$sqlPayloads = @(
    "' OR '1'='1",
    "'; DROP TABLE api_keys; --",
    "1' UNION SELECT * FROM api_keys--",
    "079203012345' OR 1=1--",
    "079203012345'; SELECT SLEEP(5)--"
)

foreach ($payload in $sqlPayloads) {
    $body = @{cccd = $payload} | ConvertTo-Json
    Write-Host "Testing: $payload"
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="yourkey"} -Body $body
        Write-Host "Response: $($response | ConvertTo-Json)"
    } catch {
        Write-Host "Error: $($_.Exception.Message)"
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả đều trả 400 (invalid format) vì không phải số
- ❌ Cảnh báo nếu có delay (time-based SQL injection) hoặc error message lộ cấu trúc DB

### Test 4.2: XSS (Cross-Site Scripting)

```powershell
# Test XSS trong input (nếu có web interface)
$xssPayloads = @(
    "<script>alert('XSS')</script>",
    "javascript:alert('XSS')",
    "<img src=x onerror=alert('XSS')>"
)

foreach ($payload in $xssPayloads) {
    $body = @{cccd = $payload} | ConvertTo-Json
    # Gửi request và kiểm tra response có chứa payload không
}
```

**Kỳ vọng:**
- ✅ Input được sanitize, không execute script
- ❌ Cảnh báo nếu payload xuất hiện nguyên vẹn trong response

### Test 4.3: Command Injection

```powershell
$cmdPayloads = @(
    "079203012345; ls",
    "079203012345 | cat /etc/passwd",
    "079203012345 && whoami"
)

foreach ($payload in $cmdPayloads) {
    $body = @{cccd = $payload} | ConvertTo-Json
    # Test xem có command được execute không
}
```

**Kỳ vọng:**
- ✅ Tất cả trả 400 (invalid format)
- ❌ Cảnh báo nếu có command được thực thi

### Test 4.4: Buffer Overflow & DoS qua Input

```powershell
# Test với chuỗi rất dài
$longString = "0" * 10000
$body = @{cccd = $longString} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="yourkey"} -Body $body -TimeoutSec 5
} catch {
    Write-Host "Timeout or error (expected for DoS)"
}
```

**Kỳ vọng:**
- ✅ Request bị reject ngay với 400 (đã có check `len(cccd) > 20`)
- ❌ Cảnh báo nếu server bị hang hoặc crash

### Test 4.5: Type Confusion

```powershell
# Test với các kiểu dữ liệu khác nhau
$testCases = @(
    @{cccd = 79203012345},           # Số thay vì chuỗi
    @{cccd = true},                   # Boolean
    @{cccd = @(0,7,9,2)},            # Array
    @{cccd = $null},                  # Null
    @{cccd = "079203012345"; extra = "malicious"}  # Extra fields
)

foreach ($testCase in $testCases) {
    $body = $testCase | ConvertTo-Json
    Write-Host "Testing: $body"
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="yourkey"} -Body $body
        Write-Host "Unexpected success!"
    } catch {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "Status: $statusCode (expected)"
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả trả 400 (validation error)
- ❌ Cảnh báo nếu có type confusion dẫn đến lỗi 500

### Test 4.6: Province Version Injection

```powershell
# Test với province_version có payload
$maliciousVersions = @(
    "../etc/passwd",
    "legacy_63'; DROP TABLE--",
    "../../../../etc/passwd",
    "current_34\0null",
    "legacy_63%00"
)

foreach ($version in $maliciousVersions) {
    $body = @{
        cccd = "079203012345"
        province_version = $version
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="yourkey"} -Body $body
        Write-Host "Response: $($response | ConvertTo-Json)"
    } catch {
        Write-Host "Error (expected): $($_.Exception.Message)"
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả trả 400 (invalid province_version)
- ❌ Cảnh báo nếu có path traversal hoặc SQL injection

---

## 5. Rate Limiting Bypass

### Test 5.1: Basic Rate Limit Test

```powershell
# Gửi 35 requests liên tiếp (vượt limit 30/phút)
$body = @{cccd = "079203012345"} | ConvertTo-Json
$headers = @{"X-API-Key" = "yourkey"}

for ($i = 1; $i -le 35; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers $headers -Body $body
        Write-Host "Request $i : 200 OK"
    } catch {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "Request $i : $statusCode"
        if ($statusCode -eq 429) {
            Write-Host "✅ Rate limit hoạt động!"
            break
        }
    }
    Start-Sleep -Milliseconds 100
}
```

**Kỳ vọng:**
- ✅ Request thứ 31+ trả 429
- ❌ Cảnh báo nếu không có rate limit hoặc bypass được

### Test 5.2: Rate Limit Bypass Techniques

```powershell
# Test 1: Đổi API key để bypass
$keys = @("key1", "key2", "key3")
foreach ($key in $keys) {
    # Gửi 35 requests với key khác nhau
    # Mỗi key có limit riêng
}

# Test 2: Đổi IP (nếu rate limit theo IP)
# Cần proxy hoặc VPN

# Test 3: Header manipulation
$headers1 = @{"X-API-Key" = "yourkey"; "X-Forwarded-For" = "1.1.1.1"}
$headers2 = @{"X-API-Key" = "yourkey"; "X-Forwarded-For" = "2.2.2.2"}
# Test xem X-Forwarded-For có ảnh hưởng không

# Test 4: Case sensitivity trong API key
# Có thể hệ thống tạo key mới với case khác
```

**Kỳ vọng:**
- ✅ Mỗi API key có limit riêng (đúng)
- ✅ IP không ảnh hưởng (vì rate limit theo API key)
- ❌ Cảnh báo nếu có cách bypass

### Test 5.3: Distributed Rate Limiting

```powershell
# Giả lập nhiều client gọi cùng lúc (cần script riêng)
# Test xem rate limit có chính xác không khi có nhiều requests đồng thời
```

**Kỳ vọng:**
- ✅ Rate limit chính xác kể cả khi có concurrent requests
- ❌ Cảnh báo nếu có race condition

---

## 6. Information Disclosure

### Test 6.1: Error Messages

```powershell
# Test các lỗi để xem có leak thông tin không
$testCases = @(
    @{cccd = ""},                    # Empty
    @{cccd = "abc"},                 # Invalid
    @{cccd = "079203012345"; province_version = "invalid"},  # Invalid version
)

foreach ($testCase in $testCases) {
    $body = $testCase | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="wrongkey"} -Body $body
    } catch {
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Error response: $responseBody"
        
        # Kiểm tra xem có lộ:
        # - Stacktrace
        # - File paths
        # - Database schema
        # - Python version
        # - Internal IPs
    }
}
```

**Kỳ vọng:**
- ✅ Error message generic, không có stacktrace
- ❌ Cảnh báo nếu lộ: `/app/routes/cccd.py`, `pymysql`, `MySQL connection`, etc.

### Test 6.2: Response Headers

```powershell
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method GET
Write-Host "Headers:"
$response.Headers | Format-List

# Kiểm tra các headers:
# - Server: có lộ version không?
# - X-Powered-By: có lộ framework không?
# - X-Debug: có debug header không?
```

**Kỳ vọng:**
- ✅ Không có header lộ thông tin (Server version, X-Powered-By, etc.)
- ❌ Cảnh báo nếu có: `Server: Werkzeug/2.0.0`, `X-Powered-By: Flask`

### Test 6.3: Directory Traversal

```powershell
# Test xem có thể truy cập file hệ thống không
$paths = @(
    "/.env",
    "/config.py",
    "/app/__init__.py",
    "/../etc/passwd",
    "/admin/../../etc/passwd",
    "/v1/cccd/parse/../../../.env"
)

foreach ($path in $paths) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000$path" -Method GET -ErrorAction Stop
        Write-Host "⚠️ VULNERABLE: $path returned $($response.StatusCode)"
        Write-Host "Content: $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))"
    } catch {
        Write-Host "✅ Safe: $path - $($_.Exception.Response.StatusCode)"
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả trả 404 hoặc 403
- ❌ Cảnh báo nếu có file bị expose

---

## 7. Admin Endpoint Security

### Test 7.1: Admin Authentication Bypass

```powershell
# Test không có admin key
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET

# Test với key sai
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"="wrongkey"}

# Test với key rỗng
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=""}
```

**Kỳ vọng:**
- ✅ Tất cả trả 403 hoặc 503
- ❌ Cảnh báo nếu có trường hợp nào bypass được

### Test 7.2: Admin Endpoints Enumeration

```powershell
# Test các admin endpoints có thể có
$adminEndpoints = @(
    "/admin/",
    "/admin/stats",
    "/admin/keys",
    "/admin/keys/create",
    "/admin/users",
    "/admin/config",
    "/admin/debug",
    "/admin/logs"
)

foreach ($endpoint in $adminEndpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000$endpoint" -Method GET -ErrorAction Stop
        Write-Host "✅ Found: $endpoint - $($response.StatusCode)"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ Not found or blocked: $endpoint - $statusCode"
    }
}
```

**Kỳ vọng:**
- ✅ Chỉ endpoints đã định nghĩa trả response
- ❌ Cảnh báo nếu có endpoint ẩn hoặc debug endpoint

### Test 7.3: SQL Injection trong Admin Endpoints (Tiered Mode)

```powershell
# Nếu đang dùng tiered mode, test SQL injection trong admin params
$adminKey = "your-admin-secret"  # Giả sử bạn có (chỉ test local!)

# Test trong key_prefix parameter
$sqlPayloads = @(
    "free' OR '1'='1",
    "prem'; DROP TABLE api_keys; --",
    "ultr' UNION SELECT * FROM api_keys--"
)

foreach ($payload in $sqlPayloads) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/keys/$payload/info" -Method GET -Headers @{"X-Admin-Key"=$adminKey}
        Write-Host "Response: $($response | ConvertTo-Json)"
    } catch {
        Write-Host "Error: $($_.Exception.Message)"
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả được sanitize, không có SQL injection
- ❌ Cảnh báo nếu có error message lộ database structure

### Test 7.4: IDOR (Insecure Direct Object Reference)

```powershell
# Test xem có thể truy cập key của người khác không
$adminKey = "your-admin-secret"

# Giả sử bạn biết key_prefix của người khác
$otherUserKey = "free_abc123def456"

# Thử truy cập thông tin key của họ
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/keys/$otherUserKey/info" -Method GET -Headers @{"X-Admin-Key"=$adminKey}

# Test vô hiệu hóa key của người khác
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/keys/$otherUserKey/deactivate" -Method POST -Headers @{"X-Admin-Key"=$adminKey}
```

**Kỳ vọng:**
- ✅ Admin có thể truy cập (đúng, vì đây là admin endpoint)
- ❌ Cảnh báo nếu user thường cũng có thể truy cập key của người khác

---

## 8. API Key Enumeration & Brute Force

### Test 8.1: API Key Format Discovery

```powershell
# Test các format key có thể có
$testKeys = @(
    "free_abc123def456",
    "prem_xyz789",
    "ultr_testkey",
    "admin_secret",
    "test123",
    "a" * 32,  # Key rất dài
    "",        # Key rỗng
)

foreach ($key in $testKeys) {
    $body = @{cccd = "079203012345"} | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$key} -Body $body -ErrorAction Stop
        Write-Host "✅ VALID KEY: $key"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 401) {
            Write-Host "❌ Invalid: $key"
        } else {
            Write-Host "⚠️ Unexpected: $key - $statusCode"
        }
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả trả 401 (invalid)
- ❌ Cảnh báo nếu có key mặc định hoặc key dễ đoán

### Test 8.2: Timing Attack

```powershell
# Test xem thời gian response có khác nhau giữa key đúng/sai không
function Measure-ResponseTime {
    param($key)
    $body = @{cccd = "079203012345"} | ConvertTo-Json
    $measure = Measure-Command {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$key} -Body $body -ErrorAction Stop
        } catch {}
    }
    return $measure.TotalMilliseconds
}

# Test với key đúng
$validKeyTime = Measure-ResponseTime "your-valid-key"

# Test với key sai
$invalidKeyTime = Measure-ResponseTime "wrong-key"

Write-Host "Valid key time: $validKeyTime ms"
Write-Host "Invalid key time: $invalidKeyTime ms"

# Nếu thời gian khác nhau đáng kể → có thể bị timing attack
```

**Kỳ vọng:**
- ✅ Thời gian response tương đương (không leak thông tin)
- ❌ Cảnh báo nếu thời gian khác nhau đáng kể

### Test 8.3: Brute Force Protection

```powershell
# Test xem có rate limit cho authentication failures không
$wrongKey = "wrong-key"
$body = @{cccd = "079203012345"} | ConvertTo-Json

# Gửi nhiều requests với key sai
for ($i = 1; $i -le 100; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$wrongKey} -Body $body -ErrorAction Stop
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            Write-Host "✅ Brute force protection active at request $i"
            break
        }
    }
}
```

**Kỳ vọng:**
- ✅ Có rate limit cho failed auth (trả 429 sau vài lần)
- ❌ Cảnh báo nếu không có protection, cho phép brute force không giới hạn

---

## 9. Denial of Service (DoS)

### Test 9.1: Resource Exhaustion

```powershell
# Test với payload lớn
$largeBody = @{
    cccd = "079203012345"
    province_version = "a" * 10000
} | ConvertTo-Json

# Gửi nhiều requests đồng thời
$jobs = @()
for ($i = 1; $i -le 100; $i++) {
    $job = Start-Job -ScriptBlock {
        param($uri, $headers, $body)
        Invoke-RestMethod -Uri $uri -Method POST -ContentType "application/json" -Headers $headers -Body $body
    } -ArgumentList "http://127.0.0.1:8000/v1/cccd/parse", @{"X-API-Key"="yourkey"}, $largeBody
    $jobs += $job
}

# Đợi và kiểm tra
Start-Sleep -Seconds 10
$jobs | Receive-Job
$jobs | Remove-Job
```

**Kỳ vọng:**
- ✅ Server vẫn hoạt động bình thường
- ✅ Rate limit ngăn chặn
- ❌ Cảnh báo nếu server bị crash hoặc hang

### Test 9.2: Slowloris Attack

```powershell
# Gửi request nhưng không gửi hết body (giữ connection mở)
# Cần script riêng hoặc tool như SlowHTTPTest
```

**Kỳ vọng:**
- ✅ Server có timeout cho connection
- ❌ Cảnh báo nếu không có timeout, dễ bị slowloris

---

## 10. CORS & Headers Security

### Test 10.1: CORS Configuration

```powershell
# Test CORS với origin khác
$headers = @{
    "Origin" = "https://evil.com"
    "Access-Control-Request-Method" = "POST"
}

# Preflight request
Invoke-WebRequest -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method OPTIONS -Headers $headers

# Kiểm tra response headers:
# - Access-Control-Allow-Origin
# - Access-Control-Allow-Methods
# - Access-Control-Allow-Headers
```

**Kỳ vọng:**
- ✅ Không có CORS headers (nếu API không cần CORS)
- ✅ Hoặc CORS chỉ cho phép domain cụ thể
- ❌ Cảnh báo nếu `Access-Control-Allow-Origin: *`

### Test 10.2: Security Headers

```powershell
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method GET

# Kiểm tra các security headers:
$securityHeaders = @(
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Strict-Transport-Security",
    "Content-Security-Policy"
)

foreach ($header in $securityHeaders) {
    if ($response.Headers[$header]) {
        Write-Host "✅ $header : $($response.Headers[$header])"
    } else {
        Write-Host "❌ Missing: $header"
    }
}
```

**Kỳ vọng:**
- ✅ Có các security headers phù hợp
- ❌ Cảnh báo nếu thiếu các headers quan trọng

---

## 11. SQL Injection (Tiered Mode)

### Test 11.1: SQL Injection trong API Key Validation

```powershell
# Nếu đang dùng tiered mode, test SQL injection trong API key
$sqlPayloads = @(
    "free_abc' OR '1'='1",
    "prem_xyz'; DROP TABLE api_keys; --",
    "ultr_test' UNION SELECT * FROM api_keys--",
    "admin' OR 1=1--"
)

foreach ($payload in $sqlPayloads) {
    $body = @{cccd = "079203012345"} | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$payload} -Body $body
        Write-Host "⚠️ Possible SQL injection: $payload returned success"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 500) {
            Write-Host "⚠️ SQL error possible: $payload caused 500"
        }
    }
}
```

**Kỳ vọng:**
- ✅ Tất cả trả 401 (key không hợp lệ)
- ✅ Không có SQL error message
- ❌ Cảnh báo nếu có SQL error hoặc bypass được

### Test 11.2: SQL Injection trong Admin Endpoints

```powershell
$adminKey = "your-admin-secret"

# Test SQL injection trong create key endpoint
$sqlPayloads = @(
    "test@email.com'; DROP TABLE api_keys; --",
    "test@email.com' OR '1'='1"
)

foreach ($payload in $sqlPayloads) {
    $body = @{
        tier = "free"
        email = $payload
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/keys/create" -Method POST -ContentType "application/json" -Headers @{"X-Admin-Key"=$adminKey} -Body $body
    } catch {
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        
        # Kiểm tra xem có SQL error không
        if ($responseBody -match "mysql|pymysql|SQL|syntax error") {
            Write-Host "⚠️ SQL error detected: $responseBody"
        }
    }
}
```

**Kỳ vọng:**
- ✅ Input được validate và sanitize
- ✅ Không có SQL error message
- ❌ Cảnh báo nếu có SQL injection

---

## 12. Logging & Data Leakage

### Test 12.1: Kiểm Tra Logging CCCD

**Mục tiêu:** Đảm bảo CCCD không được log đầy đủ.

```powershell
# Gửi request với CCCD thật
$body = @{cccd = "079203012345"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="yourkey"} -Body $body

# Sau đó kiểm tra log files (nếu có quyền truy cập)
# Hoặc kiểm tra response có chứa CCCD đầy đủ không
```

**Kiểm tra:**
- ✅ Log chỉ chứa CCCD dạng mask: `079******345`
- ❌ Cảnh báo nếu log chứa CCCD đầy đủ

### Test 12.2: API Key trong Logs

```powershell
# Gửi request với API key
$body = @{cccd = "079203012345"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="your-secret-key"} -Body $body

# Kiểm tra logs (nếu có quyền)
# API key KHÔNG được log đầy đủ
```

**Kỳ vọng:**
- ✅ API key không được log đầy đủ (chỉ log prefix hoặc hash)
- ❌ Cảnh báo nếu log chứa API key đầy đủ

### Test 12.3: Error Logs Leakage

```powershell
# Gửi request gây lỗi
$body = @{cccd = "invalid"} | ConvertTo-Json
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="free_49cc865e34f850d6d398d744b3ce2993"} -Body $body
} catch {
    # Kiểm tra xem error response có leak thông tin không
    $errorResponse = $_.Exception.Response
    $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
    $responseBody = $reader.ReadToEnd()
    
    # Kiểm tra xem có:
    # - Stacktrace
    # - File paths
    # - Database credentials
    # - Internal IPs
}
```

**Kỳ vọng:**
- ✅ Error response generic, không có stacktrace
- ❌ Cảnh báo nếu có thông tin nhạy cảm trong response

---

## 13. Checklist Tổng Kết

### ✅ Authentication & Authorization
- [X] API key được yêu cầu đúng cách
- [X] Không có cách bypass authentication
- [X] Admin endpoints được bảo vệ
- [X] Không có default credentials

### ✅ Input Validation
- [X] SQL injection được ngăn chặn
- [X] XSS được ngăn chặn
- [X] Command injection được ngăn chặn
- [X] Input được validate đúng type và format
- [X] Buffer overflow được ngăn chặn

### ✅ Rate Limiting
- [X] Rate limit hoạt động đúng
- [X] Không có cách bypass rate limit
- [X] Có protection cho brute force

### ✅ Information Disclosure
- [X] Error messages không leak thông tin
- [X] Response headers không leak version
- [X] Không có directory traversal
- [X] Stacktrace không được expose

### ✅ DoS Protection
- [X] Có rate limiting
- [X] Input size được giới hạn
- [X] Connection timeout được set
- [X] Server không crash với malicious input

### ✅ Logging & Privacy
- [X] CCCD được mask trong logs
- [X] API key không được log đầy đủ
- [X] Không có thông tin nhạy cảm trong logs

### ✅ SQL Injection (Tiered Mode)
- [X] API key validation không bị SQL injection
- [X] Admin endpoints không bị SQL injection
- [X] Prepared statements được sử dụng

### ✅ Security Headers
- [X] CORS được cấu hình đúng
- [X] Security headers được set (nếu cần)
- [X] Không có header leak thông tin

---

## 📝 Ghi Chú Quan Trọng

1. **Chỉ test trên môi trường của bạn:** Không test trên production hoặc hệ thống của người khác mà không có sự cho phép.

2. **Document findings:** Ghi lại tất cả các lỗ hổng phát hiện được và cách reproduce.

3. **Fix ngay:** Nếu phát hiện lỗ hổng, fix ngay lập tức trước khi deploy production.

4. **Automated scanning:** Cân nhắc sử dụng các tool như:
   - OWASP ZAP
   - Burp Suite
   - SQLMap (cho SQL injection)
   - Nikto (cho web server scanning)

5. **Regular testing:** Kiểm tra bảo mật định kỳ, đặc biệt sau mỗi lần thay đổi code.

---

## 🔗 Tài Liệu Tham Khảo

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

**Chúc bạn test thành công và tìm được tất cả các lỗ hổng! 🔍**
