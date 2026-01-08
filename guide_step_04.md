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

## Tự test (Self-check)

> Thực hiện được sau khi bạn đã implement endpoint `POST /v1/cccd/parse` và logic parse.

- [ ] Gọi API với 1 CCCD giả lập (không dùng CCCD thật):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse -ContentType "application/json" -Body "{\"cccd\":\"012345678901\"}"
```

- [ ] Kết quả đúng:
  - HTTP 200
  - `success=true`
  - `data.birth_year` có giá trị
  - `data.gender` có giá trị theo chuẩn đã chốt



