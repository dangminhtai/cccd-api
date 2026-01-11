# checklist.md

## Checklist triển khai CCCD API (Flask/Python)

> Mục tiêu: API nhận `cccd` và trả về `province_name`, `gender`, `birth_year` (có thể kèm `province_code`, `age` nếu cần).



Yêu cầu trên github (Agent tự làm bước này)
git add <somefile>
git commit -m <current state commit>
git push

---

## 1) Chuẩn bị dự án

- [x] Tạo cấu trúc project Flask (thư mục `app/`, `routes/`, `services/`, `data/`, `tests/`).
- [x] Chốt cách chạy: dev (Flask) và production ().
- [x] Tạo file cấu hình môi trường: `.env` / biến môi trường (PORT, API_KEY, DEFAULT_PROVINCE_VERSION...).
- [x] Thêm `.gitignore` (bỏ `.env`, cache, venv...).

---

## 2) Thiết kế API & chuẩn response

- [x] Chốt endpoint: `POST /v1/cccd/parse`.
- [x] Chốt format response thống nhất (success/data/is_valid_format/message).
- [x] Chốt format `gender` (ví dụ: `Nam`/`Nữ` hoặc `male`/`female`) và dùng thống nhất.
- [x] Chốt có trả thêm: `province_code`, `age`, `century`.
- [x] Viết ví dụ request/response mẫu trong tài liệu.

---

## 3) Validate đầu vào (để giảm lỗi và giảm tải vận hành)

- [x] Kiểm tra có trường `cccd`.
- [x] Kiểm tra `cccd` là chuỗi số.
- [x] Kiểm tra độ dài đúng (ví dụ 12 số).
- [x] Trả lỗi 400 với message dễ hiểu khi input sai.

---

## 4) Xử lý CCCD (parse dữ liệu)

- [x] Implement hàm parse ra `birth_year`.
- [x] Implement hàm parse ra `gender`.
- [x] Implement hàm parse ra `province_code` (nếu có trong logic CCCD của bạn).
- [x] Với trường hợp không parse được: trả `is_valid_format=false` hoặc trả `data=null` (chọn 1 cách và nhất quán).

---

## 5) Mapping tỉnh/thành (giải quyết chuyện đổi tên/sáp nhập)

- [x] Tạo nguồn dữ liệu mapping tỉnh/thành (ưu tiên file JSON trong repo cho bản đầu).
- [x] Hỗ trợ `province_version`:
  - [x] `legacy_63` (danh sách cũ)
  - [x] `current_34` (danh sách mới)
- [x] Mặc định theo cấu hình `DEFAULT_PROVINCE_VERSION` nếu client không truyền.
- [x] Trường hợp `province_code` không có trong mapping: trả `province_name=null` + message/warning rõ ràng.

---

## 6) Bảo mật & an toàn dữ liệu

- [x] Chọn cơ chế auth:
  - [x] API Key (`X-API-Key`) hoặc
  - [x] Bearer token
- [x] Mask CCCD khi log (không log CCCD đầy đủ).
- [x] Rate limit theo API key / IP.
- [x] CORS: chỉ bật cho domain cần thiết (nếu frontend gọi trực tiếp).

---

## 7) Logging & theo dõi lỗi

- [x] Log request id (nếu có) để dễ trace.
- [x] Chuẩn hoá log level: info/warn/error.
- [x] Lỗi 500: response không lộ chi tiết, nhưng log nội bộ có stacktrace.

---

## 8) Test (để tránh lỗi "mỗi nơi một kiểu")

- [x] Unit test validate: thiếu `cccd`, sai độ dài, có ký tự không phải số.
- [x] Unit test parse: vài CCCD giả lập để ra đúng `birth_year`, `gender`, `province_code`.
- [x] Unit test mapping: cùng `province_code` nhưng khác `province_version` ra đúng `province_name`.
- [x] API test: gọi `POST /v1/cccd/parse` và kiểm tra response schema.

---

## 9) Tài liệu hoá & bàn giao

- [x] Cập nhật `requirement.md` nếu có thay đổi format response.
- [x] Viết hướng dẫn chạy local (cài deps, set env, chạy server).
- [x] Ghi rõ các "quy ước" (độ dài CCCD, format gender, version tỉnh/thành).

---

## 10) Hệ thống API Key theo Tier (bán gói)

> Xem chi tiết: `guide_step_10.md`

- [x] Thiết kế database lưu API key (JSON/SQLite/PostgreSQL)
- [x] Script tạo key hàng loạt theo tier (free/premium/ultra)
- [x] Rate limit động theo tier
- [x] Admin API quản lý key (list, deactivate)
- [x] Usage tracking để tính tiền

---

## 11) Triển khai (deploy)

> Xem chi tiết: `guide_step_11.md`

- [x] Chọn môi trường deploy (VM/Docker/K8s…).
- [x] Thiết lập health check endpoint (ví dụ `GET /health`).
- [x] Thiết lập log tập trung/monitoring (tối thiểu: log file + rotate).
- [x] Thiết lập alert cơ bản (tăng 5xx, tăng 429 bất thường).

---

## 12) Portal & User Management (Tính năng bổ sung)

- [x] User registration với email verification
- [x] Login/Logout với session management
- [x] Password reset flow (forgot password → email → reset)
- [x] Dashboard hiển thị thống kê usage
- [x] API Key management (create, delete, rotate, label)
- [x] Usage statistics với charts
- [x] Billing & subscription management
- [x] Upgrade tier flow với payment requests
- [x] Admin dashboard để quản lý users, keys, payments
- [x] Custom 404 error page với dark theme

---

# BONUS (Tính năng nâng cao - tuỳ chọn)

## Bonus A) Tích hợp thanh toán

- [x] Manual payment flow với admin approval (đã implement)
- [x] Dashboard cho khách hàng xem usage (đã implement)
- [ ] Stripe/PayPal để tự động tạo key khi thanh toán (tùy chọn)


