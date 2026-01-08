# guide_step_05.md — Bước 5: Mapping tỉnh/thành

## Mục tiêu

Đổi từ `province_code` sang `province_name` theo “danh sách tỉnh/thành” quản lý tập trung, để khi đổi tên/sáp nhập chỉ phải cập nhật 1 nơi.

## Việc cần làm

- Tạo dữ liệu mapping (khuyến nghị bản đầu là JSON trong `data/`), ví dụ:
  - `data/provinces_legacy_63.json`
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

- [X] `data.province_name` được resolve từ `data.provinces_*.json` theo `province_version`
- [X] Nếu `province_code` không có trong mapping → `province_name=null` và có warning
- [X] Có test mapping cơ bản

## Tự test (Self-check)

Test bằng web local (không cần PowerShell):

1) Chạy server:

```bash
py .\run.py
```

2) Mở trình duyệt:

- `http://127.0.0.1:8000/demo`

3) Nhập CCCD giả lập có mã tỉnh rõ ràng (ví dụ `079203012345` → `province_code=079`)

4) Chọn `province_version` và bấm **Parse**:

- [ ] `legacy_64` → `data.province_name` phải ra tên theo file `data/provinces_legacy_63.json`
- [ ] `current_34` → `data.province_name` phải ra tên theo file `data/provinces_current_34.json`

Nếu `province_code` không tồn tại trong mapping thì:

- OK khi thấy `data.province_name = null` và `warnings` có `"province_code_not_found"`.

Ghi chú: hiện mapping đang là **starter subset** (001/048/079) để demo/triển khai trước; có thể mở rộng sau.

---

## Trạng thái

- **DoD**: ✅ Done
- **Đã verify**: ✅ Done (đã test `/demo` load 200 và unit tests pass)

## Bước tiếp theo

Chuyển sang `guide_step_06.md` (Bảo mật & an toàn dữ liệu).



