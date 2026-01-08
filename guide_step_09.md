# guide_step_09.md — Bước 9: Tài liệu hoá & bàn giao

## Mục tiêu

Người khác đọc là triển khai/tích hợp được ngay, không cần hỏi lại quá nhiều.

## Việc cần làm

- Cập nhật `requirement.md` nếu thực tế implement có thay đổi:
  - response field nào có/không
  - format `gender` dùng chuẩn nào
- Viết hướng dẫn chạy local:
  - cài dependency
  - set env
  - chạy server
  - ví dụ gọi API bằng curl/Postman
- Ghi rõ các quy ước:
  - CCCD dài bao nhiêu số
  - `province_version` hỗ trợ gì

## Hoàn thành khi

- [ ] Một dev mới clone repo có thể chạy local trong 10–15 phút
- [ ] Một đối tác đọc doc có thể gọi API và hiểu response

## Tự test (Self-check)

- [ ] “Dry-run” tài liệu theo đúng hướng dẫn:
  - cài deps
  - chạy server
  - gọi `/health` và `/v1/cccd/parse`
- [ ] Nhờ một người khác đọc doc và thử gọi API theo ví dụ (nếu họ làm được mà không hỏi lại nhiều → doc đạt).



