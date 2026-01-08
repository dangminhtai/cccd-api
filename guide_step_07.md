# guide_step_07.md — Bước 7: Logging & theo dõi lỗi

## Mục tiêu

Khi có lỗi production, nhìn log là biết chuyện gì xảy ra (mà vẫn không lộ dữ liệu nhạy cảm).

## Việc cần làm

- Chuẩn hoá log:
  - info: request đến/response thành công
  - warn: input không hợp lệ / mapping không tìm thấy
  - error: exception/500
- Gắn request id (nếu có) để trace theo từng request.
- Quy ước response lỗi 500:
  - message chung (không lộ stacktrace)
  - stacktrace chỉ nằm ở log server

## Hoàn thành khi

- [ ] Có log cho cả case success và error
- [ ] 500 không lộ chi tiết nội bộ ra client



