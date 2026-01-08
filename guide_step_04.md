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

- [ ] Có thể parse đúng với một vài CCCD giả lập (đã thống nhất rule nội bộ)
- [ ] Các hàm parse có unit test



