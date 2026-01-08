# guide_step_06.md — Bước 6: Bảo mật & an toàn dữ liệu

## Mục tiêu

API xử lý dữ liệu nhạy cảm nên cần “an toàn ngay từ đầu”: không lộ CCCD, hạn chế lạm dụng, kiểm soát ai được gọi.

## Việc cần làm

- Chọn cơ chế auth:
  - API Key (`X-API-Key`) là đơn giản nhất cho bản đầu
- Rate limit:
  - theo API key hoặc theo IP (tuỳ nhu cầu)
- Logging an toàn:
  - không log CCCD đầy đủ
  - chỉ log dạng che (mask), ví dụ `0123******01`
- CORS (nếu frontend gọi trực tiếp):
  - chỉ cho phép domain cần thiết

## Hoàn thành khi

- [ ] Gọi thiếu/ sai API key bị từ chối (401 theo quy ước hiện tại)
- [ ] Spam request bị 429
- [ ] Log không có CCCD đầy đủ (chỉ log dạng mask)

## Tự test (Self-check)

Test ngay trên web `/demo` (không cần lệnh terminal):

1) Mở `http://127.0.0.1:8000/demo`
2) Nếu bạn đã đặt `API_KEY` trong `.env`, nhập nó vào ô “API Key”; nếu chưa đặt, để trống.
3) Bấm **Parse**:
   - Thiếu/ sai API key (khi có cấu hình) → thấy status 401.
   - Đúng API key → status 200, có dữ liệu parse.
4) Test rate limit: bấm nhanh nhiều lần (khoảng >30 lần/phút) sẽ có lúc thấy 429.

Đối chiếu nhanh:
- 200 khi hợp lệ, 400 khi sai định dạng, 401 khi thiếu/sai API key (nếu bật), 429 khi spam.



