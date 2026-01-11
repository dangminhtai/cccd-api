# API Test Checklist - CCCD API

Tài liệu này liệt kê toàn bộ các API endpoints và test cases để verify hệ thống hoạt động đúng.

## 📋 Mục Lục

1. [Health Check APIs](#health-check-apis)
2. [CCCD Parse APIs](#cccd-parse-apis)
3. [Portal APIs (User)](#portal-apis-user)
4. [Admin APIs](#admin-apis)
5. [Test Scenarios](#test-scenarios)

---

## 1. Health Check APIs

### 1.1 GET `/health`
**Mục đích**: Kiểm tra server có đang chạy không

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Expected Response** (200 OK):
```json
{
  "status": "ok",
  "timestamp": "2026-01-11T12:00:00",
  "version": "1.0.0"
}
```

**Test Cases**:
- ✅ Server đang chạy → 200 OK
- ✅ Response có đủ các field: status, timestamp, version

---

## 2. CCCD Parse APIs

### 2.1 POST `/v1/cccd/parse`
**Mục đích**: Parse CCCD 12 số thành thông tin (province, gender, birth year, age)

**Request**:
```http
POST /v1/cccd/parse HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "cccd": "001123456789"
}
```

**Expected Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "province_code": "001",
    "province_name": "Hà Nội",
    "gender": "Nam",
    "birth_year": 2001,
    "age": 25,
    "century": 21
  },
  "is_valid_format": true,
  "is_plausible": true,
  "request_id": "abc123"
}
```

**Test Cases**:

**Case 1: CCCD hợp lệ (12 số)**
- Input: `"cccd": "001123456789"`
- Expected: 200 OK, `success: true`, `is_valid_format: true`

**Case 2: CCCD sai độ dài (< 12 số)**
- Input: `"cccd": "00112345678"`
- Expected: 400 Bad Request, `success: false`, `is_valid_format: false`

**Case 3: CCCD sai độ dài (> 12 số)**
- Input: `"cccd": "0011234567890"`
- Expected: 400 Bad Request, `success: false`, `is_valid_format: false`

**Case 4: CCCD có ký tự không phải số**
- Input: `"cccd": "00112345678a"`
- Expected: 400 Bad Request, `success: false`, `is_valid_format: false`

**Case 5: CCCD thiếu field**
- Input: `{}` hoặc không có field `cccd`
- Expected: 400 Bad Request, `success: false`

**Case 6: API Key Required (nếu bật tiered mode)**
- Request không có `X-API-Key` header
- Expected: 401 Unauthorized

**Case 7: API Key không hợp lệ**
- Request có `X-API-Key: invalid_key`
- Expected: 401 Unauthorized

**Case 8: API Key hết hạn**
- Request có `X-API-Key` nhưng key đã expired
- Expected: 401 Unauthorized hoặc 403 Forbidden

**Case 9: Rate Limit (nếu bật)**
- Gửi nhiều requests trong thời gian ngắn
- Expected: 429 Too Many Requests sau khi vượt limit

---

## 3. Portal APIs (User)

### 3.1 GET `/portal/` hoặc `/portal/login`
**Mục đích**: Trang đăng nhập

**Test Cases**:
- ✅ Truy cập URL → Hiển thị form đăng nhập
- ✅ Có các field: email, password, remember_me checkbox
- ✅ Có link "Đăng ký" và "Quên mật khẩu"

### 3.2 POST `/portal/login`
**Mục đích**: Đăng nhập user

**Request**:
```
POST /portal/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=password123&remember_me=on
```

**Test Cases**:

**Case 1: Đăng nhập thành công**
- Email/password đúng
- Expected: 302 Redirect to `/portal/dashboard`, session được set

**Case 2: Email/password sai**
- Email hoặc password không đúng
- Expected: 200 OK, hiển thị error message

**Case 3: Tài khoản bị khóa**
- User có status != "active"
- Expected: 200 OK, hiển thị error message "Tài khoản đã bị khóa"

**Case 4: Remember me checked**
- Checkbox "remember_me" = on
- Expected: Session cookie có max_age (24h)

**Case 5: Remember me unchecked**
- Checkbox "remember_me" = off
- Expected: Session cookie không có max_age (session cookie)

### 3.3 GET `/portal/register`
**Mục đích**: Trang đăng ký

**Test Cases**:
- ✅ Truy cập URL → Hiển thị form đăng ký
- ✅ Có các field: email, password, confirm_password, full_name
- ✅ Có client-side validation

### 3.4 POST `/portal/register`
**Mục đích**: Đăng ký user mới

**Request**:
```
POST /portal/register HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=newuser@example.com&password=password123&full_name=Nguyen Van A
```

**Test Cases**:

**Case 1: Đăng ký thành công**
- Email chưa tồn tại, password >= 8 ký tự, full_name hợp lệ
- Expected: 302 Redirect to `/portal/login`, user được tạo, email verification được gửi (nếu bật)

**Case 2: Email đã tồn tại**
- Email đã được sử dụng
- Expected: 200 OK, hiển thị error "Email đã được sử dụng"

**Case 3: Password quá ngắn (< 8 ký tự)**
- Password = "1234567"
- Expected: 200 OK, hiển thị error "Mật khẩu phải có ít nhất 8 ký tự"

**Case 4: Email không hợp lệ**
- Email = "invalid-email"
- Expected: 200 OK, hiển thị error "Email không hợp lệ"

**Case 5: Email quá dài (> 255 ký tự)**
- Email = "a" * 250 + "@example.com"
- Expected: 200 OK, hiển thị error "Email quá dài"

**Case 6: Full name quá dài (> 255 ký tự)**
- Full name = "A" * 256
- Expected: 200 OK, hiển thị error "Họ tên quá dài"

### 3.5 GET `/portal/dashboard`
**Mục đích**: Dashboard user (yêu cầu login)

**Test Cases**:
- ✅ Chưa login → 302 Redirect to `/portal/login`
- ✅ Đã login → Hiển thị dashboard với thông tin user, subscription, API keys list

### 3.6 GET `/portal/keys`
**Mục đích**: Quản lý API keys (yêu cầu login)

**Test Cases**:
- ✅ Chưa login → 302 Redirect to `/portal/login`
- ✅ Đã login nhưng email chưa verify → Hiển thị warning "Vui lòng verify email"
- ✅ Đã login và email đã verify → Hiển thị danh sách API keys

### 3.7 POST `/portal/keys/create`
**Mục đích**: Tạo API key mới (yêu cầu login)

**Request**:
```
POST /portal/keys/create HTTP/1.1
Content-Type: application/x-www-form-urlencoded

tier=premium&days=30
```

**Test Cases**:
- ✅ Chưa login → 302 Redirect
- ✅ Email chưa verify → Hiển thị error
- ✅ Tạo key thành công → Redirect to `/portal/keys`, hiển thị key (chỉ 1 lần)
- ✅ Tier không hợp lệ → Error message
- ✅ Days không hợp lệ → Error message

### 3.8 POST `/portal/keys/<key_id>/delete`
**Mục đích**: Xóa API key (yêu cầu login, AJAX)

**Test Cases**:
- ✅ Chưa login → 401 JSON error
- ✅ Key không tồn tại → 404 JSON error
- ✅ Key không thuộc về user → 403 JSON error
- ✅ Xóa thành công → 200 JSON success

### 3.9 POST `/portal/keys/<key_id>/update-label`
**Mục đích**: Update label cho API key (yêu cầu login, AJAX)

**Test Cases**:
- ✅ Chưa login → 401 JSON error
- ✅ Update thành công → 200 JSON success
- ✅ Label quá dài → 400 JSON error

### 3.10 GET `/portal/keys/<key_id>/usage`
**Mục đích**: Xem usage stats của API key (yêu cầu login, AJAX)

**Test Cases**:
- ✅ Chưa login → 401 JSON error
- ✅ Key không tồn tại → 404 JSON error
- ✅ Load thành công → 200 JSON với usage data

### 3.11 GET `/portal/usage`
**Mục đích**: Trang usage statistics (yêu cầu login)

**Test Cases**:
- ✅ Chưa login → 302 Redirect
- ✅ Đã login → Hiển thị charts/statistics

### 3.12 GET `/portal/billing`
**Mục đích**: Trang billing/payment (yêu cầu login)

**Test Cases**:
- ✅ Chưa login → 302 Redirect
- ✅ Đã login → Hiển thị subscription info, payment history

### 3.13 GET `/portal/upgrade`
**Mục đích**: Trang nâng cấp gói (yêu cầu login)

**Test Cases**:
- ✅ Chưa login → 302 Redirect
- ✅ Đã login → Hiển thị pricing plans, nút upgrade
- ✅ Đã có pending payment → Hiển thị warning, không cho tạo mới

### 3.14 POST `/portal/upgrade`
**Mục đích**: Nâng cấp gói (yêu cầu login)

**Request**:
```
POST /portal/upgrade HTTP/1.1
Content-Type: application/x-www-form-urlencoded

tier=premium
```

**Test Cases**:
- ✅ Chưa login → 302 Redirect
- ✅ Đã có pending payment → Redirect to billing với warning
- ✅ Tạo payment thành công → Redirect to billing
- ✅ Tier không hợp lệ → Error message

### 3.15 GET `/portal/verify-email/<token>`
**Mục đích**: Verify email với token

**Test Cases**:
- ✅ Token hợp lệ → 302 Redirect to login, flash success message
- ✅ Token không hợp lệ → 302 Redirect to login, flash error message
- ✅ Token đã hết hạn → 302 Redirect to login, flash error message

### 3.16 POST `/portal/resend-verification`
**Mục đích**: Gửi lại email verification (yêu cầu login)

**Test Cases**:
- ✅ Chưa login → 302 Redirect
- ✅ Email đã verify → Flash info message
- ✅ Gửi thành công → Flash success message

### 3.17 GET `/portal/forgot-password`
**Mục đích**: Trang quên mật khẩu

**Test Cases**:
- ✅ Truy cập URL → Hiển thị form nhập email

### 3.18 POST `/portal/forgot-password`
**Mục đích**: Request password reset

**Test Cases**:
- ✅ Email tồn tại → Gửi email reset password
- ✅ Email không tồn tại → Không reveal (security), hiển thị success message
- ✅ Rate limit (3 requests/hour) → 429 Too Many Requests sau 3 requests

### 3.19 GET `/portal/reset-password/<token>`
**Mục đích**: Trang reset password

**Test Cases**:
- ✅ Token hợp lệ → Hiển thị form reset password
- ✅ Token không hợp lệ → 302 Redirect to login, flash error
- ✅ Token đã hết hạn → 302 Redirect to login, flash error

### 3.20 POST `/portal/reset-password/<token>`
**Mục đích**: Reset password với token

**Test Cases**:
- ✅ Token hợp lệ, password hợp lệ → Reset thành công, redirect to login
- ✅ Token không hợp lệ → Error message
- ✅ Password quá ngắn → Error message
- ✅ Password không match confirm_password → Error message

### 3.21 GET `/portal/logout`
**Mục đích**: Đăng xuất

**Test Cases**:
- ✅ Logout thành công → Clear session, redirect to login

---

## 4. Admin APIs

**Lưu ý**: Tất cả admin APIs yêu cầu `X-Admin-Key` header hoặc `admin_key` query parameter (trừ GET `/admin/`)

### 4.1 GET `/admin/`
**Mục đích**: Admin dashboard (không yêu cầu admin key, chỉ hiển thị form)

**Test Cases**:
- ✅ Truy cập URL → Hiển thị form nhập admin key, không load sensitive data

### 4.2 GET `/admin/stats`
**Mục đích**: Thống kê tổng quan (yêu cầu admin key)

**Request**:
```http
GET /admin/stats HTTP/1.1
X-Admin-Key: your_admin_secret
```

**Test Cases**:
- ✅ Không có admin key → 403 Forbidden
- ✅ Admin key sai → 403 Forbidden
- ✅ Admin key đúng → 200 OK, JSON với stats

### 4.3 POST `/admin/keys/create`
**Mục đích**: Tạo API key mới (yêu cầu admin key)

**Request**:
```http
POST /admin/keys/create HTTP/1.1
X-Admin-Key: your_admin_secret
Content-Type: application/json

{
  "tier": "premium",
  "email": "user@example.com",
  "days": 30
}
```

**Test Cases**:
- ✅ Không có admin key → 403 Forbidden
- ✅ Tạo thành công → 200 OK, JSON với API key
- ✅ Tier không hợp lệ → 400 Bad Request
- ✅ Email không hợp lệ → 400 Bad Request

### 4.4 GET `/admin/keys/<key_prefix>/info`
**Mục đích**: Xem thông tin key (yêu cầu admin key)

**Test Cases**:
- ✅ Key tồn tại → 200 OK, JSON với key info
- ✅ Key không tồn tại → 404 Not Found

### 4.5 POST `/admin/keys/<key_prefix>/disable`
**Mục đích**: Vô hiệu hóa key (yêu cầu admin key)

**Test Cases**:
- ✅ Disable thành công → 200 OK, JSON success
- ✅ Key không tồn tại → 404 Not Found

### 4.6 GET `/admin/keys/<key_prefix>/usage`
**Mục đích**: Xem usage của key (yêu cầu admin key)

**Test Cases**:
- ✅ Key tồn tại → 200 OK, JSON với usage data
- ✅ Key không tồn tại → 404 Not Found

### 4.7 GET `/admin/payments/pending`
**Mục đích**: Lấy danh sách pending payments (yêu cầu admin key, AJAX)

**Request**:
```http
GET /admin/payments/pending HTTP/1.1
X-Admin-Key: your_admin_secret
X-Requested-With: XMLHttpRequest
```

**Test Cases**:
- ✅ Không có admin key → 403 Forbidden
- ✅ Load thành công → 200 OK, JSON với pending payments list

### 4.8 POST `/admin/payments/<payment_id>/approve`
**Mục đích**: Approve payment (yêu cầu admin key, AJAX)

**Test Cases**:
- ✅ Approve thành công → 200 OK, JSON success
- ✅ Payment không tồn tại → 404 Not Found
- ✅ Payment không phải pending → Error message

### 4.9 POST `/admin/payments/<payment_id>/reject`
**Mục đích**: Reject payment (yêu cầu admin key, AJAX)

**Test Cases**:
- ✅ Reject thành công → 200 OK, JSON success
- ✅ Payment không tồn tại → 404 Not Found

### 4.10 POST `/admin/users/change-tier`
**Mục đích**: Đổi tier cho user (yêu cầu admin key, AJAX)

**Request**:
```http
POST /admin/users/change-tier HTTP/1.1
X-Admin-Key: your_admin_secret
X-Requested-With: XMLHttpRequest
Content-Type: application/json

{
  "user_id": 1,
  "target_tier": "premium"
}
```

**Test Cases**:
- ✅ Đổi tier thành công → 200 OK, JSON success
- ✅ User không tồn tại → 404 Not Found
- ✅ Tier không hợp lệ → 400 Bad Request

### 4.11 GET `/admin/users/search`
**Mục đích**: Tìm user theo email (yêu cầu admin key, AJAX)

**Request**:
```http
GET /admin/users/search?email=user@example.com HTTP/1.1
X-Admin-Key: your_admin_secret
X-Requested-With: XMLHttpRequest
```

**Test Cases**:
- ✅ User tồn tại → 200 OK, JSON với user data
- ✅ User không tồn tại → 404 Not Found
- ✅ Email không được cung cấp → 400 Bad Request

### 4.12 GET `/admin/users`
**Mục đích**: Lấy danh sách users với pagination (yêu cầu admin key, AJAX)

**Request**:
```http
GET /admin/users?page=1&per_page=20&search=user HTTP/1.1
X-Admin-Key: your_admin_secret
X-Requested-With: XMLHttpRequest
```

**Test Cases**:
- ✅ Load thành công → 200 OK, JSON với users list và pagination
- ✅ Page không hợp lệ → Tự động điều chỉnh về 1
- ✅ Per_page quá lớn → Tự động điều chỉnh về 20

### 4.13 POST `/admin/users/<user_id>/delete`
**Mục đích**: Xóa user (yêu cầu admin key, AJAX)

**Test Cases**:
- ✅ Xóa thành công → 200 OK, JSON success
- ✅ User không tồn tại → 404 Not Found

---

## 5. Test Scenarios

### Scenario 1: User Registration & Email Verification Flow
1. User đăng ký tài khoản mới
2. Nhận email verification
3. Click link trong email để verify
4. Đăng nhập thành công
5. Tạo API key

### Scenario 2: API Key Usage Flow
1. User tạo API key
2. Sử dụng API key để gọi `/v1/cccd/parse`
3. Kiểm tra usage stats trên dashboard
4. Xem usage per key

### Scenario 3: Upgrade Subscription Flow
1. User đăng nhập với free tier
2. Vào trang upgrade
3. Chọn tier premium/ultra
4. Tạo payment request (pending)
5. Admin approve payment
6. User tier được update
7. API keys được extend expiration

### Scenario 4: Password Reset Flow
1. User click "Quên mật khẩu"
2. Nhập email
3. Nhận email reset password
4. Click link trong email
5. Nhập password mới
6. Đăng nhập với password mới

### Scenario 5: Admin Management Flow
1. Admin đăng nhập (nhập admin key)
2. Xem thống kê tổng quan
3. Xem pending payments
4. Approve/reject payments
5. Quản lý users (search, change tier, delete)
6. Quản lý API keys (create, disable, view usage)

### Scenario 6: Rate Limiting Flow
1. Gửi nhiều requests đến `/v1/cccd/parse` trong thời gian ngắn
2. Kiểm tra rate limit được áp dụng (429 Too Many Requests)
3. Đợi một chút
4. Requests tiếp tục hoạt động bình thường

### Scenario 7: Error Handling Flow
1. Test các invalid inputs (CCCD sai format, email sai, v.v.)
2. Kiểm tra error messages rõ ràng, user-friendly
3. Kiểm tra không có sensitive information leak trong error messages

---

## 📝 Testing Checklist Summary

### Critical Paths
- [ ] User registration → Email verification → Login → Create API key → Use API key
- [ ] User login → Dashboard → View usage → Upgrade subscription
- [ ] Admin login → View stats → Approve payments → Manage users
- [ ] Password reset flow hoàn chỉnh

### Security
- [ ] API key authentication hoạt động đúng
- [ ] Admin key authentication hoạt động đúng
- [ ] Session management đúng (login, logout, remember me)
- [ ] Password hashing (không lưu plaintext)
- [ ] Rate limiting hoạt động
- [ ] Input validation (prevent SQL injection, XSS)

### Edge Cases
- [ ] CCCD sai format (độ dài, ký tự không hợp lệ)
- [ ] Email đã tồn tại khi đăng ký
- [ ] Password quá ngắn/dài
- [ ] API key hết hạn
- [ ] User đã có pending payment
- [ ] Token verification hết hạn
- [ ] Rate limit exceeded

### UI/UX
- [ ] Forms có client-side validation
- [ ] Error messages rõ ràng, user-friendly
- [ ] Loading states cho AJAX requests
- [ ] Toast notifications cho success/error
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Navigation hoạt động đúng

---

## 🔧 Tools for Testing

### Manual Testing
- Browser (Chrome, Firefox, Safari)
- Postman/Insomnia cho API testing
- Browser DevTools (Network, Console, Application tabs)

### Automated Testing (Future)
- pytest cho backend tests
- Selenium/Playwright cho E2E tests
- Locust/JMeter cho load testing

---

## 📌 Notes

- **Base URL**: `http://localhost:8000` (development) hoặc production URL
- **Admin Secret**: Lấy từ `.env` file (`ADMIN_SECRET`)
- **API Keys**: Tạo từ portal hoặc admin panel
- **Database**: Đảm bảo MySQL đang chạy và schema đã được setup

---

**Last Updated**: 2026-01-11
