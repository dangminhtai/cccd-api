# 🔒 Hướng Dẫn Test Bảo Mật Bằng Postman

**Mục tiêu:** Hướng dẫn test các test case còn lại bằng Postman (thay vì PowerShell script)

**Yêu cầu:**
- Postman đã cài đặt và đăng nhập
- Server đang chạy tại `http://127.0.0.1:8000`
- API Keys để test (nếu cần)

---

## 📋 Danh Sách Test Case Còn Lại

### 1. Test 8.1: API Key Format Discovery
### 2. Test 8.2: Timing Attack
### 3. Test 8.3: Brute Force Protection
### 4. Test 9.1: Resource Exhaustion (DoS)
### 5. Test 9.2: Slowloris Attack
### 6. Test 10.1: CORS Configuration
### 7. Test 10.2: Security Headers
### 8. Test 11.1: SQL Injection trong API Key Validation
### 9. Test 12.1: Kiểm Tra Logging CCCD
### 10. Test 12.2: API Key trong Logs
### 11. Test 12.3: Error Logs Leakage

---

## 🚀 Setup Postman Collection

### Bước 1: Tạo Collection mới

1. Mở Postman
2. Click **"New"** → **"Collection"**
3. Đặt tên: `CCCD API Security Tests`
4. Click **"Create"**

### Bước 2: Tạo Environment Variables

1. Click **"Environments"** (bên trái)
2. Click **"+"** để tạo environment mới
3. Đặt tên: `CCCD API Local`
4. Thêm các biến:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` |
| `api_key_free` | `free_a1c6062d52bdbff5762e07ec391dfb81` | `free_a1c6062d52bdbff5762e07ec391dfb81` |
| `api_key_prem` | `prem_31c65c426015522c069a6dc1cf57a3ad` | `prem_31c65c426015522c069a6dc1cf57a3ad` |
| `api_key_ultr` | `ultr_8d2caeeb47a7a46bd959c0f5423d1843` | `ultr_8d2caeeb47a7a46bd959c0f5423d1843` |
| `admin_key` | `(lấy từ .env ADMIN_SECRET)` | `(lấy từ .env ADMIN_SECRET)` |

5. Click **"Save"**
6. Chọn environment này để sử dụng (dropdown ở góc trên bên phải)

---

## 📝 Test Cases Chi Tiết

### Test 8.1: API Key Format Discovery

**Mục tiêu:** Test các format key có thể có để xem có key mặc định hoặc dễ đoán không.

#### Request 1: Test key format `free_abc123`
1. Tạo request mới: **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `free_abc123def456`
3. **Body** (raw JSON):
   ```json
   {
     "cccd": "079203012345"
   }
   ```
4. **Kỳ vọng:** Status `401 Unauthorized`

#### Request 2-7: Test các format khác
- `prem_xyz789` → Kỳ vọng: 401
- `ultr_testkey` → Kỳ vọng: 401
- `admin_secret` → Kỳ vọng: 401
- `test123` → Kỳ vọng: 401
- Key rất dài (32 ký tự `a`) → Kỳ vọng: 401
- Key rỗng (để trống) → Kỳ vọng: 401

**✅ Kết quả mong đợi:** Tất cả trả 401 (invalid key)

---

### Test 8.2: Timing Attack

**Mục tiêu:** Đo thời gian response giữa key đúng/sai để xem có leak thông tin không.

#### Request 1: Test với key đúng
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `{{api_key_free}}`
3. **Body:**
   ```json
   {
     "cccd": "079203012345"
   }
   ```
4. **Tab "Tests"** (dưới Body) - Thêm script này:
   ```javascript
   // Tự động ghi lại thời gian response
   const responseTime = pm.response.responseTime;
   console.log("✅ Valid Key Response Time: " + responseTime + "ms");
   
   // Lưu vào environment variable để so sánh
   pm.environment.set("valid_key_time", responseTime);
   
   // Test tự động
   pm.test("Response time < 1000ms", function () {
       pm.expect(responseTime).to.be.below(1000);
   });
   ```
5. **Xem kết quả:** 
   - Tab "Test Results" (bên dưới) sẽ hiển thị thời gian
   - Tab "Console" (View → Show Postman Console) sẽ log thời gian
   - Thời gian cũng hiển thị ở tab "Time" (màu xanh lá)

#### Request 2: Test với key sai
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `wrong_key_12345`
3. **Body:** Giống như trên
4. **Tab "Tests"** - Thêm script này:
   ```javascript
   // Tự động ghi lại và so sánh thời gian
   const responseTime = pm.response.responseTime;
   const validKeyTime = pm.environment.get("valid_key_time");
   
   console.log("❌ Invalid Key Response Time: " + responseTime + "ms");
   
   if (validKeyTime) {
       const diff = Math.abs(responseTime - validKeyTime);
       console.log("⏱️ Time Difference: " + diff + "ms");
       
       if (diff > 100) {
           console.log("⚠️ WARNING: Large time difference! Possible timing attack vulnerability.");
       } else {
           console.log("✅ OK: Time difference is acceptable (< 100ms)");
       }
   }
   
   // Test tự động
   pm.test("Response time < 1000ms", function () {
       pm.expect(responseTime).to.be.below(1000);
   });
   ```

**✅ Kết quả mong đợi:** Thời gian tương đương (chênh lệch < 50ms)
- Nếu chênh lệch lớn (> 100ms) → Có thể bị timing attack

**💡 Tips:**
1. **Xem Console:** View → Show Postman Console (Ctrl+Alt+C) để xem tất cả logs
2. **Chạy nhiều lần:** Dùng Collection Runner với iterations = 10 để tính trung bình
3. **Tự động so sánh:** Script trên sẽ tự động so sánh và cảnh báo nếu chênh lệch lớn

---

### Test 8.3: Brute Force Protection

**Mục tiêu:** Test xem có rate limit cho authentication failures không.

#### Request 1-15: Gửi nhiều request với key sai
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `wrong_key_1` (đổi mỗi lần: wrong_key_2, wrong_key_3, ...)
3. **Body:**
   ```json
   {
     "cccd": "079203012345"
   }
   ```
4. Gửi liên tiếp 15 requests

**✅ Kết quả mong đợi:**
- Request 1-10: Trả `401 Unauthorized`
- Request 11+: Có thể trả `429 Too Many Requests` (nếu có rate limit cho failed auth)

**💡 Tip:** Dùng Postman Collection Runner để chạy tự động:
1. Click vào Collection → **"Run"**
2. Chọn requests cần chạy
3. Set iterations = 15
4. Click **"Run CCCD API Security Tests"**

---

### Test 9.1: Resource Exhaustion (DoS)

**Mục tiêu:** Test với payload lớn và nhiều requests đồng thời.

#### Request 1: Payload lớn (nhưng đã bị reject sớm)
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `{{api_key_free}}`
3. **Body:**
   ```json
   {
     "cccd": "0123456789012345678901234567890123456789"
   }
   ```
   (CCCD dài > 20 ký tự)

**✅ Kết quả mong đợi:** Status `400 Bad Request` (reject sớm)

#### Request 2: Nhiều requests đồng thời
1. Tạo 20 requests giống nhau
2. **POST** `{{base_url}}/v1/cccd/parse`
3. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `{{api_key_free}}`
4. **Body:**
   ```json
   {
     "cccd": "079203012345"
   }
   ```
5. Chạy tất cả cùng lúc (dùng Collection Runner với delay = 0)

**✅ Kết quả mong đợi:**
- Một số requests thành công (200)
- Một số requests bị rate limit (429)
- Server vẫn hoạt động bình thường

---

### Test 9.2: Slowloris Attack

**Mục tiêu:** Test gửi request nhưng không gửi hết body (giữ connection mở).

**⚠️ Lưu ý:** Test này khó thực hiện bằng Postman vì Postman tự động gửi hết body. Có thể bỏ qua hoặc dùng tool khác (curl, Burp Suite).

**Cách test thủ công:**

**⚠️ Lưu ý:** Trong PowerShell, `curl` là alias của `Invoke-WebRequest`, không phải curl thật. Cần dùng `curl.exe` hoặc viết command trên một dòng.

**Option 1: Dùng curl.exe (khuyến nghị)**
```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/cccd/parse -H "Content-Type: application/json" -H "X-API-Key: free_a1c6062d52bdbff5762e07ec391dfb81" -d "{\"cccd\":\"079203012345\"}" --max-time 5
```

**Option 2: Dùng PowerShell Invoke-WebRequest với timeout**
```powershell
$body = '{"cccd":"079203012345"}' | ConvertTo-Json
$headers = @{
    "Content-Type" = "application/json"
    "X-API-Key" = "free_a1c6062d52bdbff5762e07ec391dfb81"
}
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -Headers $headers -Body $body -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    if ($_.Exception.Response) {
        $status = [int]$_.Exception.Response.StatusCode
        Write-Host "Status: $status" -ForegroundColor Yellow
        if ($status -eq 500) {
            Write-Host "Note: 500 may indicate server timeout/reset (not a vulnerability)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Timeout or connection error (expected for slowloris test)" -ForegroundColor Yellow
    }
}

# Verify server still works after timeout
Write-Host "`nVerifying server still works..." -ForegroundColor Cyan
try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method GET -ErrorAction Stop
    Write-Host "✅ Server OK - Health check: $($health.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Server may be hung" -ForegroundColor Red
}
```

**Option 3: Bỏ qua test này (khuyến nghị)**
- Test Slowloris khó thực hiện bằng Postman hoặc curl đơn giản
- Cần tool chuyên dụng như Burp Suite hoặc script Python
- Có thể bỏ qua nếu không có tool chuyên dụng

**✅ Kết quả mong đợi:** Server có timeout cho connection (không bị hang)

**⚠️ Lưu ý về Status 500:**
- Nếu nhận được **Status 500** khi test Slowloris, có thể do:
  1. **Server timeout:** Server đóng connection khi timeout → Flask trả 500 (Internal Server Error)
  2. **Connection reset:** Server reset connection → Client nhận 500
  3. **Đây là behavior bình thường** - Server có timeout và đóng connection (không bị hang)
- **Kết luận:** Status 500 trong trường hợp này **KHÔNG phải lỗ hổng**, mà là cách server xử lý timeout/connection reset
- **Điều quan trọng:** Server không bị hang, vẫn có thể xử lý requests khác bình thường

**Cách verify:**
1. Sau khi nhận 500, gửi request bình thường khác
2. Nếu request bình thường vẫn hoạt động (200) → Server OK, chỉ là timeout cho Slowloris
3. Nếu server không phản hồi → Có thể bị hang (vấn đề)

---

### Test 10.1: CORS Configuration

**Mục tiêu:** Test CORS với origin khác.

#### Request 1: Test với origin khác
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `{{api_key_free}}`
   - `Origin`: `https://evil.com`
3. **Body:**
   ```json
   {
     "cccd": "079203012345"
   }
   ```
4. **Quan sát:** Response headers (tab "Headers" trong Postman)

**✅ Kết quả mong đợi:**
- Không có header `Access-Control-Allow-Origin` (hoặc chỉ cho phép domain cụ thể)
- Nếu có `Access-Control-Allow-Origin: *` → VULNERABLE (cho phép mọi origin)

#### Request 2: Test OPTIONS preflight
1. **OPTIONS** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Origin`: `https://evil.com`
   - `Access-Control-Request-Method`: `POST`
   - `Access-Control-Request-Headers`: `X-API-Key, Content-Type`

**✅ Kết quả mong đợi:** Status `405 Method Not Allowed` (đã fix ở test 2.2)

---

### Test 10.2: Security Headers

**Mục tiêu:** Test các security headers.

#### Request 1: Kiểm tra security headers
1. **GET** `{{base_url}}/health`
2. **Quan sát:** Response headers

**Các headers cần kiểm tra:**

| Header | Kỳ vọng | Mô tả |
|--------|---------|-------|
| `X-Content-Type-Options` | `nosniff` | Ngăn MIME type sniffing |
| `X-Frame-Options` | `DENY` hoặc `SAMEORIGIN` | Ngăn clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Bảo vệ XSS (legacy) |
| `Strict-Transport-Security` | `max-age=31536000` | Chỉ dùng HTTPS (nếu có HTTPS) |
| `Content-Security-Policy` | Có giá trị | Ngăn XSS, injection |
| `Server` | Không có | Đã fix (hoặc chỉ có trong dev) |

**✅ Kết quả mong đợi:**
- Có các security headers (tốt)
- Không có `Server` header (hoặc chỉ có trong dev - accepted)

---

### Test 11.1: SQL Injection trong API Key Validation

**Mục tiêu:** Test SQL injection trong API key khi validate (tiered mode).

#### Request 1-5: SQL injection trong API key
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `free_1' OR '1'='1`
3. **Body:**
   ```json
   {
     "cccd": "079203012345"
   }
   ```

**Test các payload:**
- `free_1' OR '1'='1`
- `free_1'; DROP TABLE api_keys--`
- `free_1' UNION SELECT * FROM api_keys--`
- `free_1' AND SLEEP(5)--`

**✅ Kết quả mong đợi:**
- Tất cả trả `401 Unauthorized`
- Không có SQL error trong response
- Không có delay (SLEEP không hoạt động)

---

### Test 12.1: Kiểm Tra Logging CCCD

**Mục tiêu:** Kiểm tra log files (nếu có quyền) xem CCCD có bị log đầy đủ không.

**⚠️ Lưu ý:** Test này cần quyền truy cập log files trên server.

#### Cách test:
1. Gửi request với CCCD: `079203012345`
2. Kiểm tra log terminal của server (nơi chạy `python run.py`)
3. Tìm log entry cho request này

**✅ Kết quả mong đợi:**
- Log chỉ chứa CCCD dạng mask: `079******345`
- Không có CCCD đầy đủ trong log

**Ví dụ log đúng:**
```
[INFO] cccd_parsed | request_id=abc123 | cccd_masked=079******345 | province_code=079
```

---

### Test 12.2: API Key trong Logs

**Mục tiêu:** Kiểm tra API key có bị log đầy đủ không.

#### Cách test:
1. Gửi request với API key: `free_a1c6062d52bdbff5762e07ec391dfb81`
2. Kiểm tra log terminal

**✅ Kết quả mong đợi:**
- API key không được log đầy đủ
- Chỉ log prefix: `free_...` hoặc hash

---

### Test 12.3: Error Logs Leakage

**Mục tiêu:** Test error response có leak thông tin không.

#### Request 1: Test với input sai để trigger error
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:**
   - `Content-Type`: `application/json`
   - `X-API-Key`: `{{api_key_free}}`
3. **Body:**
   ```json
   {
     "cccd": null
   }
   ```

#### Request 2: Test với format sai
1. **POST** `{{base_url}}/v1/cccd/parse`
2. **Headers:** Giống như trên
3. **Body:**
   ```json
   {
     "cccd": "abc123"
   }
   ```

**✅ Kết quả mong đợi:**
- Error response generic: `"Lỗi hệ thống. Vui lòng thử lại sau."`
- Không có stacktrace
- Không có file paths
- Không có database errors
- Có `request_id` để trace (nhưng không leak thông tin)

---

## 📊 Template Postman Collection

### Cấu trúc Collection đề xuất:

```
CCCD API Security Tests
├── 8. API Key Enumeration & Brute Force
│   ├── 8.1 - API Key Format Discovery
│   │   ├── Format: free_abc123
│   │   ├── Format: prem_xyz789
│   │   └── ...
│   ├── 8.2 - Timing Attack
│   │   ├── Valid Key (measure time)
│   │   └── Invalid Key (measure time)
│   └── 8.3 - Brute Force Protection
│       └── Multiple Failed Auth (15 requests)
├── 9. Denial of Service
│   ├── 9.1 - Resource Exhaustion
│   │   ├── Large Payload
│   │   └── Concurrent Requests
│   └── 9.2 - Slowloris (skip - use curl)
├── 10. CORS & Headers Security
│   ├── 10.1 - CORS Configuration
│   │   ├── Origin: evil.com
│   │   └── OPTIONS Preflight
│   └── 10.2 - Security Headers
│       └── Check Headers
├── 11. SQL Injection (Tiered Mode)
│   └── 11.1 - SQL Injection in API Key
│       ├── Payload: OR '1'='1
│       └── ...
└── 12. Logging & Data Leakage
    ├── 12.1 - CCCD Logging (manual check)
    ├── 12.2 - API Key Logging (manual check)
    └── 12.3 - Error Logs Leakage
        ├── Null CCCD
        └── Invalid Format
```

---

## ✅ Checklist Sau Khi Test

Sau khi test xong, cập nhật `security_test_report.md`:

- [ ] Test 8.1: API Key Format Discovery → Ghi kết quả
- [ ] Test 8.2: Timing Attack → Ghi thời gian response
- [ ] Test 8.3: Brute Force Protection → Ghi kết quả
- [ ] Test 9.1: Resource Exhaustion → Ghi kết quả
- [ ] Test 9.2: Slowloris → Ghi kết quả (hoặc skip)
- [ ] Test 10.1: CORS Configuration → Ghi headers
- [ ] Test 10.2: Security Headers → Ghi headers
- [ ] Test 11.1: SQL Injection in API Key → Ghi kết quả
- [ ] Test 12.1: CCCD Logging → Ghi kết quả (manual)
- [ ] Test 12.2: API Key Logging → Ghi kết quả (manual)
- [ ] Test 12.3: Error Logs Leakage → Ghi kết quả

---

## 💡 Tips & Tricks

### 1. Dùng Collection Runner cho test lặp lại
- Click vào Collection → **"Run"**
- Chọn requests cần chạy
- Set iterations và delay
- Xem kết quả trong tab "Run Results"

### 2. Dùng Tests Script trong Postman
Thêm script để tự động kiểm tra:

```javascript
// Test response status
pm.test("Status is 401", function () {
    pm.response.to.have.status(401);
});

// Test response body
pm.test("No SQL error in response", function () {
    pm.response.to.not.have.body("mysql");
    pm.response.to.not.have.body("pymysql");
    pm.response.to.not.have.body("SQL");
});
```

### 3. Export/Import Collection
- Export collection để backup: **Collection → ... → Export**
- Import collection từ file: **Import → File**

### 4. Dùng Variables cho dễ quản lý
- Tạo variables trong Environment
- Dùng `{{variable_name}}` trong requests
- Dễ thay đổi giá trị mà không cần sửa từng request

---

## 📝 Ghi Chú Kết Quả

Sau mỗi test, ghi lại:

1. **Status code:** 200, 400, 401, 403, 429, 500?
2. **Response body:** Có chứa thông tin nhạy cảm không?
3. **Response headers:** Có security headers không?
4. **Timing:** Thời gian response (nếu test timing attack)
5. **Logs:** CCCD/API key có bị log đầy đủ không? (manual check)

---

## 🎯 Kết Luận

Sau khi test xong, bạn sẽ có:
- ✅ Hiểu rõ hơn về bảo mật API
- ✅ Biết cách test bằng Postman
- ✅ Kết quả test chi tiết để cập nhật `security_test_report.md`

**Chúc bạn test thành công!** 🚀
