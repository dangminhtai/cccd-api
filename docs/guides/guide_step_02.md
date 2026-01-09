# guide_step_02.md — Bước 2: Thiết kế API & chuẩn response

## Mục tiêu

Chốt “hình dạng” API để tất cả hệ thống gọi đều **nhất quán** và dễ tích hợp.

## Việc cần làm

- Chốt endpoint: `POST /v1/cccd/parse`
- Chốt request body:
  - `cccd` (bắt buộc)
  - `province_version` (tuỳ chọn)
- Chốt response schema (giữ ổn định):
  - `success`
  - `is_valid_format`
  - `data`
  - `message` (nếu cần)
- Chốt format `gender`:
  - Chọn **một chuẩn** và dùng thống nhất (vd: `Nam`/`Nữ`)
- Chốt có trả thêm hay không:
  - `province_code`, `age`, `century`

## Output mong muốn

- [X] `requirement.md` phản ánh đúng request/response cuối cùng
- [X] Mọi ví dụ JSON trong tài liệu thống nhất cùng một format

## Tự test (Self-check)

- [X] Mở `requirement.md` và xác nhận có đủ:
  - endpoint `POST /v1/cccd/parse`
  - request fields: `cccd`, `province_version`
  - response fields: `success`, `is_valid_format`, `data`, `message`
- [X] Chọn 1 chuẩn `gender` và đảm bảo toàn bộ doc dùng đúng 1 chuẩn đó
- [X] (Tuỳ chọn) dùng grep để rà nhanh:

```bash
git grep "/v1/cccd/parse"
```

Nếu đã implement endpoint, có thể test **bằng web** (không cần PowerShell):

1) Chạy server:

```bash
py .\run.py
```

2) Mở trình duyệt:

- `http://127.0.0.1:8000/demo`

3) Test 2 trường hợp và xem “OK” là gì:

- **Case A (đúng)**: nhập CCCD **đủ 12 số** (ví dụ `012345678901`) rồi bấm **Parse**
  - Kết quả OK khi thấy:
    - `Status: 200`
    - JSON có `success: true`
    - JSON có `is_valid_format: true`
- **Case B (sai)**: nhập CCCD sai (ví dụ `123`) rồi bấm **Parse**
  - Kết quả OK khi thấy:
    - `Status: 400`
    - JSON có `success: false`
    - JSON có `is_valid_format: false`

---

## Trạng thái

- **DoD**: ✅ Done
- **Đã verify**: ✅ Done (đã test trên `/demo` với case đúng và case sai)

## Bước tiếp theo

Chuyển sang `guide_step_03.md` (Validate đầu vào).




