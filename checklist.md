# checklist.md

## Checklist triển khai CCCD API (Flask/Python)

> Mục tiêu: API nhận `cccd` và trả về `province_name`, `gender`, `birth_year` (có thể kèm `province_code`, `age` nếu cần).



Yêu cầu trên github (Agent tự làm bước này)
git add <somefile>
git commit -m <current state commit>
git push

---

## 1) Chuẩn bị dự án

- [ ] Tạo cấu trúc project Flask (thư mục `app/`, `routes/`, `services/`, `data/`, `tests/`).
- [ ] Chốt cách chạy: dev (Flask) và production (gunicorn).
- [ ] Tạo file cấu hình môi trường: `.env` / biến môi trường (PORT, API_KEY, DEFAULT_PROVINCE_VERSION...).
- [ ] Thêm `.gitignore` (bỏ `.env`, cache, venv...).

---

## 2) Thiết kế API & chuẩn response

- [ ] Chốt endpoint: `POST /v1/cccd/parse`.
- [ ] Chốt format response thống nhất (success/data/is_valid_format/message).
- [ ] Chốt format `gender` (ví dụ: `Nam`/`Nữ` hoặc `male`/`female`) và dùng thống nhất.
- [ ] Chốt có/không trả thêm: `province_code`, `age`, `century`.
- [ ] Viết ví dụ request/response mẫu trong tài liệu.

---

## 3) Validate đầu vào (để giảm lỗi và giảm tải vận hành)

- [ ] Kiểm tra có trường `cccd`.
- [ ] Kiểm tra `cccd` là chuỗi số.
- [ ] Kiểm tra độ dài đúng (ví dụ 12 số).
- [ ] Trả lỗi 400 với message dễ hiểu khi input sai.

---

## 4) Xử lý CCCD (parse dữ liệu)

- [ ] Implement hàm parse ra `birth_year`.
- [ ] Implement hàm parse ra `gender`.
- [ ] Implement hàm parse ra `province_code` (nếu có trong logic CCCD của bạn).
- [ ] Với trường hợp không parse được: trả `is_valid_format=false` hoặc trả `data=null` (chọn 1 cách và nhất quán).

---

## 5) Mapping tỉnh/thành (giải quyết chuyện đổi tên/sáp nhập)

- [ ] Tạo nguồn dữ liệu mapping tỉnh/thành (ưu tiên file JSON trong repo cho bản đầu).
- [ ] Hỗ trợ `province_version`:
  - [ ] `legacy_64` (danh sách cũ)
  - [ ] `current_34` (danh sách mới)
- [ ] Mặc định theo cấu hình `DEFAULT_PROVINCE_VERSION` nếu client không truyền.
- [ ] Trường hợp `province_code` không có trong mapping: trả `province_name=null` + message/warning rõ ràng.

---

## 6) Bảo mật & an toàn dữ liệu

- [ ] Chọn cơ chế auth:
  - [ ] API Key (`X-API-Key`) hoặc
  - [ ] Bearer token
- [ ] Mask CCCD khi log (không log CCCD đầy đủ).
- [ ] Rate limit theo API key / IP.
- [ ] CORS: chỉ bật cho domain cần thiết (nếu frontend gọi trực tiếp).

---

## 7) Logging & theo dõi lỗi

- [ ] Log request id (nếu có) để dễ trace.
- [ ] Chuẩn hoá log level: info/warn/error.
- [ ] Lỗi 500: response không lộ chi tiết, nhưng log nội bộ có stacktrace.

---

## 8) Test (để tránh lỗi “mỗi nơi một kiểu”)

- [ ] Unit test validate: thiếu `cccd`, sai độ dài, có ký tự không phải số.
- [ ] Unit test parse: vài CCCD giả lập để ra đúng `birth_year`, `gender`, `province_code`.
- [ ] Unit test mapping: cùng `province_code` nhưng khác `province_version` ra đúng `province_name`.
- [ ] API test: gọi `POST /v1/cccd/parse` và kiểm tra response schema.

---

## 9) Tài liệu hoá & bàn giao

- [ ] Cập nhật `requirement.md` nếu có thay đổi format response.
- [ ] Viết hướng dẫn chạy local (cài deps, set env, chạy server).
- [ ] Ghi rõ các “quy ước” (độ dài CCCD, format gender, version tỉnh/thành).

---

## 10) Triển khai (deploy)

- [ ] Chọn môi trường deploy (VM/Docker/K8s…).
- [ ] Thiết lập health check endpoint (ví dụ `GET /health`).
- [ ] Thiết lập log tập trung/monitoring (tối thiểu: log file + rotate).
- [ ] Thiết lập alert cơ bản (tăng 5xx, tăng 429 bất thường).


