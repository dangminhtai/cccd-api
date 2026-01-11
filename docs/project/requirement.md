# requirement.md

## 1) Mục tiêu sản phẩm

Xây dựng một **API dùng chung** (Flask/Python) nhận đầu vào là **CCCD** và trả về **thông tin cơ bản** để các hệ thống tự điền/đồng bộ dữ liệu:

- **Tỉnh/Thành** (`province_name`)
- **Giới tính** (`gender`)
- **Năm sinh** (`birth_year`)

Mục tiêu chính: giảm nhập tay, giảm sai dữ liệu, giảm công vận hành và giảm việc mỗi hệ thống tự “đọc CCCD” theo cách riêng.

---

## 2) Người dùng/đối tượng sử dụng

- **Frontend/Web/App**: tự điền form đăng ký/KYC.
- **Backend dịch vụ**: đồng bộ hồ sơ khách hàng vào CRM.
- **Đối tác tích hợp**: gọi API để lấy dữ liệu chuẩn mà không phải tự xử lý CCCD.

---

## 3) Phạm vi (Scope)

### In-scope

- Nhận CCCD (chuỗi số) và trả về:
  - `province_name`
  - `gender`
  - `birth_year`
- Trả về kết quả theo format JSON thống nhất cho mọi client.
- Có validate đầu vào cơ bản (độ dài/ký tự số).
- Có cơ chế quản lý danh sách tỉnh/thành để **cập nhật tập trung** khi thay đổi hành chính.
- Có logging an toàn (không log CCCD đầy đủ) và rate limit cơ bản.



---

## 4) Công nghệ & triển khai

- Ngôn ngữ: **Python 3.10+**
- Framework: **Flask**
- Khuyến nghị thư viện:
  - `Flask`
  - `gunicorn` (chạy production)
  - `python-dotenv` (cấu hình môi trường)
  - `Flask-Limiter` (rate limit)
  - `pytest` (test)

---

## 5) Định nghĩa API (API Contract)

### 5.1 Endpoint

- **POST** `/v1/cccd/parse`

### 5.2 Request

Header:

- `Content-Type: application/json`
- (Khuyến nghị) `X-API-Key: <key>` hoặc `Authorization: Bearer <token>` (tuỳ mô hình bảo mật)

Body (JSON):

- `cccd` (string, bắt buộc): chuỗi số CCCD
- `province_version` (string, tuỳ chọn): phiên bản “danh sách tỉnh/thành” để hiển thị tên
  - Ví dụ: `legacy_63` hoặc `current_34`
  - (Tương thích ngược) `legacy_64` được chấp nhận như alias của `legacy_63`
  - Nếu không truyền, dùng mặc định theo cấu hình hệ thống

### 5.3 Response (thành công)

HTTP 200:

- `success` (boolean)
- `is_valid_format` (boolean): CCCD có đúng định dạng cơ bản hay không
- `is_plausible` (boolean): dữ liệu có “hợp lý” theo ngữ cảnh hiện tại hay không (ví dụ năm sinh không ở tương lai)
- `province_version` (string): phiên bản mapping tỉnh/thành đã dùng để trả `province_name`
- `data` (object | null)
  - `province_code` (string | null): mã tỉnh lấy từ CCCD (nếu parse được)
  - `province_name` (string | null)
  - `gender` (string | null): chuẩn hoá giá trị: `Nam` / `Nữ` (chọn 1 chuẩn và dùng thống nhất)
  - `birth_year` (number | null)
  - `century` (number | null): thế kỷ (ví dụ 21 cho năm 2000–2099, nếu dùng)
  - `age` (number | null): tuổi (nếu dùng)
- `warnings` (array): danh sách cảnh báo (ví dụ `birth_year_in_future`)
- `message` (string | null): thông điệp ngắn gọn cho client (nếu cần)

Ví dụ (minh hoạ):

```json
{
  "success": true,
  "data": {
    "province_code": "079",
    "province_name": "Thành phố Hồ Chí Minh",
    "gender": "Nam",
    "birth_year": 1996,
    "century": 20,
    "age": 29
  },
  "is_valid_format": true,
  "is_plausible": true,
  "province_version": "legacy_63",
  "warnings": []
}
```

### 5.4 Response (lỗi)

Nguyên tắc: lỗi rõ ràng, dễ hiểu, không lộ dữ liệu nhạy cảm.

HTTP 400 (input sai):

```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
}
```

HTTP 429 (rate limit):

```json
{
  "success": false,
  "data": null,
  "message": "Quá nhiều yêu cầu, vui lòng thử lại sau."
}
```

HTTP 500 (lỗi hệ thống):

```json
{
  "success": false,
  "data": null,
  "message": "Hệ thống đang bận, vui lòng thử lại."
}
```

---

## 6) Quy tắc validate & xử lý dữ liệu

### Validate cơ bản (phiên bản đầu)

- Chỉ nhận **CCCD 12 chữ số**.
- Nếu:
  - thiếu trường `cccd`, hoặc
  - có ký tự không phải số, hoặc
  - không đúng độ dài 12
  → trả HTTP 400 và `is_valid_format=false`.

### Parse & mapping

- API sẽ trích xuất các phần cần thiết từ CCCD để suy ra:
  - mã tỉnh/thành (`province_code`) → map ra `province_name`
  - giới tính
  - năm sinh

> Lưu ý: chi tiết quy tắc parse (vị trí ký tự, quy tắc giới tính/năm sinh) sẽ được implement theo chuẩn CCCD mà team đang áp dụng nội bộ. File này tập trung vào yêu cầu sản phẩm/API.

---

## 7) Quản lý danh sách tỉnh/thành (để xử lý chuyện sáp nhập/đổi tên)

Vì tên tỉnh/thành có thể thay đổi theo thời gian, yêu cầu như sau:

- Có một nơi duy nhất quản lý “danh sách tỉnh/thành” (ví dụ file JSON trong repo hoặc bảng DB).
- Cho phép có **2 chế độ hiển thị**:
  - `legacy_63`: theo danh sách cũ (63 tỉnh/thành)
  - `current_34`: theo danh sách mới (phục vụ hệ thống mới)
- Mặc định dùng chế độ theo cấu hình (`DEFAULT_PROVINCE_VERSION`).

Mục tiêu: khi có thay đổi hành chính, chỉ cần cập nhật danh sách tại API → các hệ thống khác không phải tự sửa.

---

## 8) Bảo mật, quyền truy cập, và logging

- **Không log CCCD đầy đủ**:
  - chỉ log dạng che: ví dụ `0123******01`
- **Rate limit**:
  - ví dụ: 60 requests/phút/API key (cấu hình được)
- **Auth**:
  - tối thiểu: API Key
  - (tuỳ chọn) JWT/Bearer nếu tích hợp hệ thống có sẵn
- **CORS**:
  - chỉ bật cho domain cần thiết (nếu frontend gọi trực tiếp)

---

## 9) Yêu cầu phi chức năng (Non-functional)

- **Latency**: p95 < 100ms (mục tiêu, tuỳ hạ tầng)
- **Uptime**: 99.9% (mục tiêu)
- **Quan sát**:
  - Có request id (trace id) trong log/response header (khuyến nghị)
  - Log lỗi đầy đủ stacktrace (server-side) nhưng response không lộ chi tiết nội bộ

---

## 10) Kiểm thử (Testing)

Tối thiểu cần:

- Test validate: thiếu `cccd`, sai độ dài, có ký tự chữ.
- Test parse: một vài CCCD giả lập để ra đúng `birth_year`, `gender`, `province_code`.
- Test mapping: `province_version=legacy_63` và `province_version=current_34` cho cùng `province_code`.

---

## 11) Tiêu chí nghiệm thu (Acceptance Criteria)

- Gọi API với CCCD hợp lệ → trả về đủ `province_name`, `gender`, `birth_year` theo format thống nhất.
- CCCD sai định dạng → trả 400, `success=false`, message dễ hiểu.
- Không có log chứa CCCD đầy đủ.
- Rate limit hoạt động (429 khi spam).
- Có thể chuyển đổi chế độ hiển thị tỉnh/thành bằng `province_version` hoặc cấu hình mặc định.

---

## 12) Portal & User Management (Tính năng bổ sung)

### 12.1 User Authentication & Registration

- **User Registration**: 
  - Đăng ký tài khoản với email, password, full_name
  - Email verification với token (24h expiry)
  - Resend verification email
- **Login/Logout**:
  - Session-based authentication
  - "Remember Me" với permanent session (24h)
  - Logout và clear session
- **Password Reset**:
  - Forgot password flow: nhập email → nhận reset link qua email
  - Reset password với token (có expiry)
  - Invalidate tất cả sessions sau khi reset password

### 12.2 Portal Dashboard

- **Dashboard**: Hiển thị thống kê usage, subscription tier, API keys
- **API Key Management**:
  - Tạo API key theo tier (free/premium/ultra)
  - Xóa key (hard delete)
  - Rotate key (tạo key mới, xóa key cũ)
  - Edit label cho key
  - Suspend/Resume key
- **Usage Statistics**:
  - Charts hiển thị usage theo thời gian (7/30/90/365 ngày)
  - Usage theo từng API key
  - Export data
- **Billing & Subscription**:
  - Xem lịch sử thanh toán
  - Upgrade tier với payment request
  - Admin approval flow cho payments

### 12.3 Admin Dashboard

- **User Management**:
  - List users, search by email
  - Change user tier manually
  - Delete user
- **API Key Management**:
  - List all API keys
  - Deactivate keys
- **Payment Management**:
  - List pending payments
  - Approve/Reject payments
  - Update subscription sau khi approve
- **Statistics**:
  - User stats (total, by tier)
  - API key stats
  - Usage stats

### 12.4 Error Handling

- **Custom 404 Page**: 
  - Dark theme với glass-panel styling
  - Phân biệt API requests (JSON) và Web requests (HTML)
  - Navigation thông minh (dashboard nếu logged in, login nếu not)
- **Error Handlers**:
  - 404: Custom page cho web, JSON cho API
  - 429: JSON response với rate limit message
  - 500: Generic error message, detailed log server-side

### 12.5 UI/UX

- **Dark Theme**: Consistent dark theme across all pages
- **Responsive Design**: Mobile-friendly với Tailwind CSS
- **Material Symbols Icons**: Consistent iconography
- **Custom Scrollbars**: Styled scrollbars cho dark theme
- **Flash Messages**: User-friendly notifications


