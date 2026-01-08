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

> Thực hiện được sau khi bật auth/rate limit cho `POST /v1/cccd/parse`. Nếu `API_KEY` để trống thì API không yêu cầu key.

- [ ] Test thiếu API key (kỳ vọng 401 nếu đã cấu hình `API_KEY`):

```powershell
try {
  Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse `
    -ContentType "application/json" `
    -Body '{"cccd":"012345678901"}'
} catch { $_.Exception.Response.StatusCode.Value__ }
```

- [ ] Test có API key (thay `YOUR_KEY`):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/cccd/parse `
  -Headers @{ "X-API-Key"="YOUR_KEY" } `
  -ContentType "application/json" `
  -Body '{"cccd":"012345678901"}'
```

- [ ] Test rate limit: gửi nhanh 20–30 request; kỳ vọng có lúc nhận 429.



