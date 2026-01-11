# Hướng dẫn xác nhận Admin Authorization

> Tài liệu này mô tả cách xác nhận rằng người dùng bình thường **KHÔNG THỂ** truy cập các endpoint admin.

---

## 1. Tổng quan

Hệ thống sử dụng **Admin Secret Key** (từ biến môi trường `ADMIN_SECRET`) để bảo vệ các admin endpoints. Chỉ có người có key đúng mới có thể truy cập.

### 1.1 Cơ chế bảo vệ

- **Header-based authentication**: Admin key được gửi qua header `X-Admin-Key`
- **Before request check**: Tất cả admin routes (trừ GET `/admin/`) đều được kiểm tra qua `@admin_bp.before_request`
- **Response**: Nếu key sai hoặc thiếu → trả về `403 Forbidden` với message `"Unauthorized - Admin key không hợp lệ"`

### 1.2 Endpoints được bảo vệ

Tất cả các endpoints sau yêu cầu `X-Admin-Key` header:

- `POST /admin/keys/create` - Tạo API key mới
- `GET /admin/keys/<prefix>/info` - Xem thông tin key
- `POST /admin/keys/<prefix>/deactivate` - Vô hiệu hóa key
- `GET /admin/keys/<prefix>/usage` - Xem usage của key
- `GET /admin/stats` - Xem thống kê
- `GET /admin/payments` - Xem danh sách payments
- `POST /admin/payments/<id>/approve` - Duyệt payment
- `POST /admin/payments/<id>/reject` - Từ chối payment
- `POST /admin/users/change-tier` - Đổi tier của user
- `GET /admin/users/search` - Tìm kiếm user
- `GET /admin/users` - Xem danh sách users
- `POST /admin/users/<id>/delete` - Xóa user

**Ngoại lệ**: `GET /admin/` - Không yêu cầu key (chỉ hiển thị form nhập key)

---

## 2. Test tự động (Unit Tests)

### 2.1 Chạy test suite

```bash
python -m pytest tests/test_admin_authorization.py -v
```

### 2.2 Các test cases

File `tests/test_admin_authorization.py` bao gồm các test:

1. **test_admin_dashboard_without_key**: GET `/admin/` không cần key
2. **test_admin_endpoints_without_key**: Tất cả admin API endpoints yêu cầu key
3. **test_admin_endpoints_with_wrong_key**: Key sai → 403
4. **test_admin_endpoints_with_correct_key**: Key đúng → không bị 403
5. **test_admin_key_case_sensitive**: Key phải case-sensitive
6. **test_admin_key_missing_header**: Thiếu header → 403
7. **test_admin_key_in_query_vs_header**: Key chỉ chấp nhận từ header, không từ query
8. **test_admin_dashboard_accessible_without_key**: Dashboard page accessible

---

## 3. Test thủ công (Manual Testing)

### 3.1 Chuẩn bị

1. **Set ADMIN_SECRET** trong `.env`:
   ```env
   ADMIN_SECRET=my-super-secret-admin-key-12345
   ```

2. **Khởi động server**:
   ```bash
   python run.py
   ```

3. **Lấy admin secret** từ `.env` (giả sử: `my-super-secret-admin-key-12345`)

### 3.2 Test Case 1: Không có Admin Key

**Mục tiêu**: Xác nhận không có key → 403

**Các bước**:

1. Gọi admin endpoint **KHÔNG có** header `X-Admin-Key`:

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET
```

**Kỳ vọng**:
- Status code: `403`
- Response body:
  ```json
  {
    "error": "Unauthorized - Admin key không hợp lệ"
  }
  ```

### 3.3 Test Case 2: Admin Key sai

**Mục tiêu**: Xác nhận key sai → 403

**Các bước**:

1. Gọi admin endpoint với key **SAI**:

```powershell
# PowerShell
$wrongKey = "wrong-key-12345"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=$wrongKey}
```

**Kỳ vọng**:
- Status code: `403`
- Response body:
  ```json
  {
    "error": "Unauthorized - Admin key không hợp lệ"
  }
  ```

### 3.4 Test Case 3: Admin Key đúng

**Mục tiêu**: Xác nhận key đúng → không bị 403

**Các bước**:

1. Gọi admin endpoint với key **ĐÚNG**:

```powershell
# PowerShell
$correctKey = "my-super-secret-admin-key-12345"  # Từ .env
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=$correctKey}
```

**Kỳ vọng**:
- Status code: `200` (hoặc `500` nếu DB chưa setup, nhưng **KHÔNG phải 403**)
- Response body: JSON với stats data (hoặc error message khác, nhưng không phải "Unauthorized")

### 3.5 Test Case 4: Key trong Query Parameter (không được chấp nhận)

**Mục tiêu**: Xác nhận key chỉ chấp nhận từ header, không từ query

**Các bước**:

1. Gọi admin endpoint với key trong **query parameter**:

```powershell
# PowerShell
$correctKey = "my-super-secret-admin-key-12345"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats?X-Admin-Key=$correctKey" -Method GET
```

**Kỳ vọng**:
- Status code: `403`
- Response body:
  ```json
  {
    "error": "Unauthorized - Admin key không hợp lệ"
  }
  ```

### 3.6 Test Case 5: Key Case-Sensitive

**Mục tiêu**: Xác nhận key phải match chính xác (case-sensitive)

**Các bước**:

1. Gọi admin endpoint với key viết **HOA**:

```powershell
# PowerShell
$correctKey = "my-super-secret-admin-key-12345"
$uppercaseKey = $correctKey.ToUpper()
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=$uppercaseKey}
```

**Kỳ vọng**:
- Status code: `403` (nếu key gốc là lowercase)
- Response body:
  ```json
  {
    "error": "Unauthorized - Admin key không hợp lệ"
  }
  ```

### 3.7 Test Case 6: Dashboard Page (không cần key)

**Mục tiêu**: Xác nhận GET `/admin/` không yêu cầu key

**Các bước**:

1. Truy cập dashboard page **KHÔNG có** key:

```powershell
# PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/admin/" -Method GET
```

**Kỳ vọng**:
- Status code: `200`
- Response body: HTML page với form nhập admin key
- **KHÔNG** có data nhạy cảm (pending payments, users list, etc.)

---

## 4. Test với cURL

### 4.1 Test không có key

```bash
curl -X GET http://127.0.0.1:8000/admin/stats
```

**Kỳ vọng**: `403 Forbidden`

### 4.2 Test với key sai

```bash
curl -X GET http://127.0.0.1:8000/admin/stats \
  -H "X-Admin-Key: wrong-key"
```

**Kỳ vọng**: `403 Forbidden`

### 4.3 Test với key đúng

```bash
curl -X GET http://127.0.0.1:8000/admin/stats \
  -H "X-Admin-Key: my-super-secret-admin-key-12345"
```

**Kỳ vọng**: `200 OK` (hoặc error khác, nhưng không phải 403)

---

## 5. Test với Postman

### 5.1 Setup

1. Tạo request mới
2. Method: `GET`
3. URL: `http://127.0.0.1:8000/admin/stats`

### 5.2 Test Case 1: Không có header

1. **KHÔNG** thêm header `X-Admin-Key`
2. Send request

**Kỳ vọng**: `403 Forbidden`

### 5.2 Test Case 2: Header với key sai

1. Thêm header:
   - Key: `X-Admin-Key`
   - Value: `wrong-key-12345`
2. Send request

**Kỳ vọng**: `403 Forbidden`

### 5.3 Test Case 3: Header với key đúng

1. Thêm header:
   - Key: `X-Admin-Key`
   - Value: `my-super-secret-admin-key-12345` (từ `.env`)
2. Send request

**Kỳ vọng**: `200 OK` (hoặc error khác, nhưng không phải 403)

---

## 6. Checklist xác nhận

Sau khi test, đảm bảo:

- [ ] **Không có key** → Tất cả admin API endpoints trả về `403`
- [ ] **Key sai** → Tất cả admin API endpoints trả về `403`
- [ ] **Key đúng** → Không bị `403` (có thể `200` hoặc error khác)
- [ ] **Key trong query parameter** → Không được chấp nhận (vẫn `403`)
- [ ] **Key case-sensitive** → Key viết hoa/thường khác nhau → `403`
- [ ] **GET /admin/** → Không yêu cầu key, nhưng không expose data nhạy cảm
- [ ] **Tất cả admin endpoints** đều được bảo vệ (không có endpoint nào bị bỏ sót)

---

## 7. Lưu ý bảo mật

### 7.1 Admin Secret Key

- **Độ dài**: Nên >= 32 ký tự
- **Độ phức tạp**: Nên chứa chữ, số, ký tự đặc biệt
- **Bảo mật**: 
  - Không commit vào Git
  - Chỉ lưu trong `.env` (đã có trong `.gitignore`)
  - Không log ra console hoặc file log
  - Không hiển thị trong error messages

### 7.2 Rate Limiting

Hiện tại admin endpoints **chưa có rate limiting riêng**. Nên xem xét thêm:

- Rate limit cho admin endpoints (ví dụ: 100 requests/minute)
- IP whitelist (chỉ cho phép IP cụ thể)
- 2FA cho admin operations

### 7.3 Logging

- Log tất cả attempts truy cập admin endpoints (thành công và thất bại)
- Log IP address, timestamp, endpoint, và kết quả (success/failed)
- Alert khi có nhiều failed attempts từ cùng IP

---

## 8. Kết luận

Sau khi hoàn thành tất cả test cases trên, bạn có thể **xác nhận** rằng:

✅ **Người dùng bình thường KHÔNG THỂ truy cập admin endpoints** nếu không có admin secret key đúng.

✅ **Hệ thống đã được bảo vệ đúng cách** với header-based authentication.

✅ **Không có lỗ hổng** như:
- Key trong query parameter
- Key không case-sensitive
- Endpoint bị bỏ sót không check auth
