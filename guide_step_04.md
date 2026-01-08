# guide_step_04.md — Bước 4: Xử lý CCCD (parse dữ liệu)

## Mục tiêu

Từ `cccd` (chuỗi số) tách ra các thông tin cần trả về:

- `birth_year`
- `gender`
- (tuỳ chọn) `province_code`

## Việc cần làm

- Viết các hàm nhỏ, dễ test:
  - `parse_birth_year(cccd) -> int | None`
  - `parse_gender(cccd) -> str | None`
  - `parse_province_code(cccd) -> str | None`
- Nếu không parse được:
  - chọn 1 cách và dùng nhất quán:
    - Cách A: `is_valid_format=false`
    - Cách B: `is_valid_format=true` nhưng `data` có field `null` + `message`/warning

## Hoàn thành khi

- [X] Có thể parse đúng với một vài CCCD giả lập (đã thống nhất rule nội bộ)
- [X] Các hàm parse có unit test

## Tự test (Self-check)

Test bằng web local (không cần PowerShell):

1) Chạy server:

```bash
py .\run.py
```

2) Mở trình duyệt:

- `http://127.0.0.1:8000/demo`

3) Nhập CCCD giả lập (ví dụ `079203012345`) rồi bấm **Parse**

- OK khi thấy:
  - `Status: 200`
  - JSON có `success: true`
  - JSON có `is_valid_format: true`
  - `data.province_code` = `079`
  - `data.gender` = `Nam` (với ví dụ trên)
  - `data.century` = `21`
  - `data.birth_year` = `2003`

---

## Trạng thái

- **DoD**: ✅ Done
- **Đã verify**: ✅ Done (CCCD giả lập `079203012345` trả `province_code/gender/century/birth_year` đúng)

## Bước tiếp theo

Chuyển sang `guide_step_05.md` (Mapping tỉnh/thành).



