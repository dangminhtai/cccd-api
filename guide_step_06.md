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

- [ ] Gọi thiếu/ sai API key bị từ chối (401/403 theo quy ước)
- [ ] Spam request bị 429
- [ ] Log không có CCCD đầy đủ



