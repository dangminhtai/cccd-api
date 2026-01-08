# guide_step_09.md — Bước 9: Tài liệu hoá & bàn giao

## Mục tiêu

Người khác đọc là triển khai/tích hợp được ngay, không cần hỏi lại quá nhiều.

## Việc cần làm

- [x] Cập nhật `requirement.md` nếu thực tế implement có thay đổi
- [x] Viết `README.md` hướng dẫn chạy local
- [x] Ghi rõ các quy ước (CCCD 12 số, gender Nam/Nữ, province_version)
- [x] Ví dụ gọi API bằng PowerShell/curl/Python

## Hoàn thành khi

- [x] Một dev mới clone repo có thể chạy local trong 5–10 phút
- [x] Một đối tác đọc doc có thể gọi API và hiểu response

## Tài liệu đã tạo

| File | Nội dung |
|------|----------|
| `README.md` | Quick start, API reference, ví dụ code |
| `requirement.md` | Yêu cầu chi tiết, API contract |
| `env.example` | Template cấu hình |
| `guide_step_00.md` → `guide_step_10.md` | Hướng dẫn từng bước |

## Tự test (Self-check)

### 1. Dry-run: Clone mới và chạy theo README

Giả lập như một dev mới:

```powershell
# 1. Clone repo (hoặc vào thư mục project)
cd F:\X-FILE\Code_UNI\Python\FPT\CCCD-API

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Copy env
copy env.example .env

# 4. Chạy server
python run.py
```

### 2. Test API theo ví dụ trong README

Mở PowerShell mới:

```powershell
# Health check
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
# Kỳ vọng: status: ok

# Parse CCCD (nếu không bật API_KEY)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "079203012345"}'
# Kỳ vọng: success: True, province_code: 079, gender: Nam
```

### 3. Checklist đọc doc

| Câu hỏi | Trả lời được từ doc? |
|---------|---------------------|
| CCCD cần bao nhiêu số? | ✅ 12 số (README + requirement.md) |
| Gender format là gì? | ✅ Nam/Nữ |
| Province version hỗ trợ gì? | ✅ legacy_63, current_34 |
| Cách bật API key? | ✅ Sửa .env, set API_KEY=... |
| Cách gọi API từ Python? | ✅ Có ví dụ trong README |

### 4. (Optional) Nhờ người khác test

Gửi link repo cho 1 người chưa biết project:
- Họ đọc README
- Họ clone, cài, chạy
- Họ gọi được API

**Đạt** nếu họ làm được trong 10-15 phút mà không hỏi lại nhiều.

---

## ✅ DoD (Definition of Done) - Bước 9

| Tiêu chí | Kết quả |
|----------|---------|
| README.md có Quick Start | ✅ |
| README.md có API Reference | ✅ |
| README.md có ví dụ PowerShell/curl/Python | ✅ |
| requirement.md đã cập nhật | ✅ |
| Quy ước ghi rõ ràng | ✅ |



