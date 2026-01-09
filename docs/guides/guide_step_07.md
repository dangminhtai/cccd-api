# guide_step_07.md — Bước 7: Logging & theo dõi lỗi

## Mục tiêu

Khi có lỗi production, nhìn log là biết chuyện gì xảy ra (mà vẫn không lộ dữ liệu nhạy cảm).

## Việc cần làm

- Chuẩn hoá log:
  - info: request đến/response thành công
  - warn: input không hợp lệ / mapping không tìm thấy
  - error: exception/500
- Gắn request id (nếu có) để trace theo từng request.
- Quy ước response lỗi 500:
  - message chung (không lộ stacktrace)
  - stacktrace chỉ nằm ở log server

## Hoàn thành khi

- [x] Có log cho cả case success và error
- [x] 500 không lộ chi tiết nội bộ ra client
- [x] Có request_id để trace
- [x] (Optional) Database logging khi `API_KEY_MODE=tiered`

## Tự test (Self-check)

### 1. Test log success (INFO)

1. Mở `/demo`, nhập CCCD đúng 12 số, bấm Parse
2. Xem terminal:
   ```
   INFO:app:cccd_parsed | request_id=abc12345 | cccd_masked=079******345 | ...
   ```
3. ✅ Thấy `request_id` và `cccd_masked` (không thấy CCCD đầy đủ)

### 2. Test log warning (WARN)

1. Mở `/demo`, nhập CCCD sai (ví dụ "123"), bấm Parse
2. Xem terminal:
   ```
   WARNING:app:validation_failed | request_id=abc12345 | reason=invalid_cccd_format | length=3
   ```
3. ✅ Thấy `WARNING` với `request_id` và `reason`

### 3. Test 500 error handling

1. Mở trình duyệt: `http://127.0.0.1:8000/test-500`
2. **Client nhận**:
   ```json
   {
     "success": false,
     "message": "Lỗi hệ thống. Vui lòng thử lại sau.",
     "request_id": "abc12345"
   }
   ```
3. **Terminal log**:
   ```
   ERROR:app:unhandled_exception | request_id=abc12345 | RuntimeError: This is a test error...
   Traceback (most recent call last):
     ...
   ```
4. ✅ Client **không** thấy stacktrace, chỉ log server có

---

## ✅ DoD (Definition of Done) - Bước 7

| Tiêu chí | Cách verify | Kết quả |
|----------|-------------|---------|
| Log INFO cho success | Parse CCCD đúng → terminal có `INFO:app:cccd_parsed` | ✅ |
| Log WARNING cho validation error | Parse CCCD sai → terminal có `WARNING:app:validation_failed` | ✅ |
| Log ERROR cho 500 | Mở `/test-500` → terminal có `ERROR:app:unhandled_exception` + stacktrace | ✅ |
| 500 response generic | `/test-500` → JSON có `message` chung, **không** có stacktrace | ✅ |
| Request ID | Mọi log đều có `request_id=...` | ✅ |
| Database logging (tiered mode) | Set `API_KEY_MODE=tiered` → gọi API → check `request_logs` table | ✅ |

---

## Database Logging (Optional - chỉ khi tiered mode)

### Setup Database Logs

**Bước 1: Tạo bảng `request_logs`**

```sql
-- Chạy script
mysql -u root -p cccd_api < scripts/db_schema_logs.sql

-- Hoặc copy/paste nội dung scripts/db_schema_logs.sql vào MySQL
```

**Bước 2: Set `API_KEY_MODE=tiered` trong `.env`**

```env
API_KEY_MODE=tiered
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=cccd_api
```

**Bước 3: Restart server**

```powershell
python run.py
```

**Bước 4: Test và verify**

```powershell
# Gọi API
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" `
    -Method POST `
    -ContentType "application/json" `
    -Headers @{"X-API-Key"="free_xxx"} `
    -Body '{"cccd": "079203012345"}'

# Check database
mysql -u root -p cccd_api -e "SELECT * FROM request_logs ORDER BY created_at DESC LIMIT 5;"
```

**Kỳ vọng:**
- ✅ Thấy log trong bảng `request_logs`
- ✅ Có `request_id`, `status_code`, `cccd_masked`, `response_time_ms`
- ✅ Không có CCCD đầy đủ (chỉ có masked)

### Query Logs

```sql
-- Xem logs hôm nay
SELECT * FROM request_logs 
WHERE DATE(created_at) = CURDATE() 
ORDER BY created_at DESC;

-- Thống kê theo status code
SELECT status_code, COUNT(*) as count 
FROM request_logs 
GROUP BY status_code;

-- Thống kê theo API key
SELECT api_key_prefix, COUNT(*) as requests, AVG(response_time_ms) as avg_time_ms
FROM request_logs 
WHERE api_key_prefix IS NOT NULL
GROUP BY api_key_prefix;

-- Xóa logs cũ hơn 90 ngày
DELETE FROM request_logs 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```



