# guide_step_08.md — Bước 8: Test

## Mục tiêu

Đảm bảo API chạy ổn định và không bị “mỗi nơi một kiểu” khi đổi người làm/đổi phiên bản.

## Việc cần làm

- Unit test validate:
  - thiếu `cccd`
  - `cccd` có chữ
  - sai độ dài
- Unit test parse:
  - vài CCCD giả lập để ra đúng `birth_year`, `gender`, `province_code`
- Unit test mapping:
  - cùng `province_code` nhưng `legacy_64` vs `current_34`
- API test:
  - gọi `POST /v1/cccd/parse` và kiểm tra response có đủ field

## Hoàn thành khi

- [ ] Chạy test pass hết
- [ ] Khi đổi mapping/tên tỉnh, test giúp phát hiện sai lệch ngay



