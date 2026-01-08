# guide_step_01.md — Bước 1: Chuẩn bị dự án

## Mục tiêu

Tạo “khung” dự án Flask rõ ràng để sau này thêm route/logic/test không bị rối.

## Việc cần làm

- Tạo cấu trúc thư mục cơ bản:
  - `app/` (main app)
  - `routes/` (định nghĩa endpoint)
  - `services/` (logic parse CCCD, mapping tỉnh)
  - `data/` (file mapping tỉnh/thành)
  - `tests/` (unit test / api test)
- Chốt cách chạy:
  - dev: Flask
  - prod: gunicorn
- Chuẩn bị cấu hình môi trường:
  - `PORT`
  - `API_KEY` (nếu dùng API key)
  - `DEFAULT_PROVINCE_VERSION` (vd: `legacy_64` hoặc `current_34`)
- Thêm `.gitignore` (bỏ `.env`, venv, cache, v.v.)

## Kết quả mong muốn

- [X] Repo có cấu trúc thư mục rõ ràng
- [] Có thể chạy “hello world” Flask (nếu đã tạo code)
- [ ] Không commit nhầm `.env`/venv

## Tự test (Self-check)

1) Cài dependency:

```bash
python -m pip install -r requirements.txt
```

2) (Tuỳ chọn) tạo `.env` (hoặc bỏ qua để dùng port mặc định 8000):

```bash
PORT=8000
```

3) Chạy server:

```bash
python run.py
```

4) Gọi health check (PowerShell):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Kết quả đúng: `{"status":"ok"}`

Ghi chú: nếu bạn mở `http://127.0.0.1:8000/` thì trước đây sẽ thấy 404; hiện tại đã có route `/` trả message hướng dẫn để dễ kiểm tra.

5) Dừng server: `Ctrl + C`


