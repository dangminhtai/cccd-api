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

- [ ] `requirement.md` phản ánh đúng request/response cuối cùng
- [ ] Mọi ví dụ JSON trong tài liệu thống nhất cùng một format



