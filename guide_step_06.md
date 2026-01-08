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

Test ngay trên web `/demo` (không cần lệnh terminal).

### Bước A: Bật API Key (nếu chưa)

1. Mở file `.env` trong thư mục gốc project.
2. Sửa dòng `API_KEY=` thành `API_KEY=mysecretkey123` (hoặc bất kỳ chuỗi nào bạn muốn).
3. Restart server: `Ctrl+C` → `py run.py`

### Bước B: Test trên /demo

1. Mở `http://127.0.0.1:8000/demo`
2. Quan sát **hộp trạng thái** trên trang:
   - 🔐 **Xanh lá**: API Key đang BẬT → hiển thị luôn key cần nhập.
   - 🔓 **Cam**: API Key đang TẮT → làm lại Bước A.
3. Test các trường hợp:
   | Trường hợp | Ô API Key | Kỳ vọng |
   |------------|-----------|---------|
   | Sai key | `wrongkey` | **401** |
   | Không nhập | *(trống)* | **401** |
   | Đúng key | `mysecretkey123` | **200** |
4. Test rate limit: bấm Parse liên tục >30 lần/phút → sẽ có lúc thấy **429**.

### Đối chiếu nhanh

| Status | Ý nghĩa |
|--------|---------|
| 200 | OK |
| 400 | Sai định dạng CCCD |
| 401 | Thiếu/sai API key |
| 429 | Spam quá nhiều |



