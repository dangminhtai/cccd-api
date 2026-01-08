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

- [ ] Repo có cấu trúc thư mục rõ ràng
- [ ] Có thể chạy “hello world” Flask (nếu đã tạo code)
- [ ] Không commit nhầm `.env`/venv

# guide_step_01.md — Git/GitHub: lưu trạng thái và đẩy lên repo

## Mục tiêu

Đảm bảo mọi thay đổi tài liệu/source code đều được **commit rõ ràng** và **push lên GitHub** để dễ review và rollback.

## Việc cần làm

- Kiểm tra thay đổi hiện có.
- Add đúng file cần commit.
- Commit với message ngắn gọn, mô tả đúng nội dung.
- Push lên nhánh đang làm việc.

## Lệnh gợi ý

```bash
git status
git add .
git commit -m "docs: add CCCD API requirements/checklist"
git push
```

> Lưu ý: Nếu repo dùng nhánh khác (vd: `main`/`master`/`dev`), hãy đảm bảo bạn đang ở đúng nhánh trước khi push.

## Hoàn thành khi

- [ ] `git status` sạch (working tree clean) sau khi push
- [ ] Nhìn thấy commit mới trên GitHub



