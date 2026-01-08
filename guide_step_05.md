# guide_step_05.md — Bước 5: Mapping tỉnh/thành

## Mục tiêu

Đổi từ `province_code` sang `province_name` theo “danh sách tỉnh/thành” quản lý tập trung, để khi đổi tên/sáp nhập chỉ phải cập nhật 1 nơi.

## Việc cần làm

- Tạo dữ liệu mapping (khuyến nghị bản đầu là JSON trong `data/`), ví dụ:
  - `data/provinces_legacy_64.json`
  - `data/provinces_current_34.json`
- Hỗ trợ tham số `province_version`:
  - `legacy_64`
  - `current_34`
- Nếu client không truyền `province_version`:
  - dùng `DEFAULT_PROVINCE_VERSION` (config)
- Trường hợp không tìm thấy `province_code`:
  - trả `province_name=null`
  - kèm `message`/warning để client biết

## Hoàn thành khi

- [ ] Cùng một `province_code`, đổi `province_version` cho ra `province_name` đúng theo từng danh sách
- [ ] Có test mapping cơ bản



