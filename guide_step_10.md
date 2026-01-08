# guide_step_10.md — Bước 10: Triển khai (deploy)

## Mục tiêu

Đưa API lên môi trường chạy thật, có kiểm tra sức khoẻ, có theo dõi lỗi cơ bản.

## Việc cần làm

- Chọn cách deploy:
  - VM (gunicorn + nginx) hoặc
  - Docker hoặc
  - K8s
- Tạo health check endpoint:
  - `GET /health` trả 200 + JSON đơn giản
- Thiết lập logging/monitoring cơ bản:
  - log file + rotate, hoặc đẩy log về hệ thống tập trung
- Thiết lập alert:
  - tăng 5xx bất thường
  - tăng 429 bất thường
- Cấu hình environment trên server:
  - `API_KEY`
  - `DEFAULT_PROVINCE_VERSION`
  - cấu hình rate limit

## Hoàn thành khi

- [ ] Có thể gọi `/health` và `/v1/cccd/parse` từ bên ngoài
- [ ] Khi API lỗi, có log để trace và có alert tối thiểu

## Tự test (Self-check)

- [ ] Chạy production server (ví dụ gunicorn) và đảm bảo vẫn gọi được `/health`:

```bash
gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app
```

- [ ] Từ máy khác (hoặc browser) gọi:
  - `http://<server-ip>:8000/health`
- [ ] Tắt gunicorn và chắc chắn port được giải phóng.



