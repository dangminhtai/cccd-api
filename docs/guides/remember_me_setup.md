# Hướng Dẫn: Cấu Hình "Ghi Nhớ Đăng Nhập" (Remember Me)

## Vấn Đề

Khi restart server, bạn phải đăng nhập lại mặc dù đã check "Ghi nhớ đăng nhập". Điều này xảy ra vì Flask secret key thay đổi mỗi lần restart server.

## Nguyên Nhân

Flask sử dụng `secret_key` để ký (sign) session cookies. Nếu `secret_key` thay đổi:
- Tất cả session cookies cũ trở nên không hợp lệ
- User phải đăng nhập lại
- "Remember Me" không hoạt động qua các lần restart server

## Giải Pháp

### Bước 1: Tạo Secret Key Cố Định

Tạo một secret key ngẫu nhiên và lưu vào `.env`:

**Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**Linux/Mac:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy kết quả (ví dụ: `a1b2c3d4e5f6...`)

### Bước 2: Thêm Vào File `.env`

Mở file `.env` (hoặc tạo từ `env.example`) và thêm:

```env
FLASK_SECRET_KEY=a1b2c3d4e5f6...  # Paste secret key từ bước 1
```

### Bước 3: Restart Server

```bash
# Dừng server (Ctrl+C)
# Khởi động lại
python run.py
```

### Bước 4: Test

1. Đăng nhập với checkbox "Ghi nhớ đăng nhập" được check
2. Đóng browser
3. Mở lại browser và truy cập `/portal/dashboard`
4. **Kết quả mong đợi**: Bạn vẫn đăng nhập (không cần nhập lại password)
5. Restart server
6. Refresh trang
7. **Kết quả mong đợi**: Bạn vẫn đăng nhập (session vẫn valid)

## Lưu Ý

- **Secret key phải giữ bí mật**: Không commit vào git, không chia sẻ
- **Secret key phải cố định**: Không thay đổi sau khi đã set (nếu thay đổi, tất cả users phải đăng nhập lại)
- **Production**: Luôn set `FLASK_SECRET_KEY` trong production environment
- **Development**: Có thể dùng random key, nhưng sẽ mất session khi restart

## Kiểm Tra

Để kiểm tra secret key đã được set:

```python
# Trong Python shell hoặc debug
import os
print("FLASK_SECRET_KEY set:", bool(os.getenv("FLASK_SECRET_KEY")))
```

Nếu in ra `False`, bạn cần thêm `FLASK_SECRET_KEY` vào `.env`.

## Troubleshooting

### Vẫn phải đăng nhập lại sau restart?

1. Kiểm tra `.env` có `FLASK_SECRET_KEY` chưa
2. Kiểm tra secret key không thay đổi giữa các lần restart
3. Xóa cookies cũ trong browser và đăng nhập lại
4. Kiểm tra browser không ở chế độ "Incognito/Private"

### Session hết hạn quá nhanh?

- Check `PERMANENT_SESSION_LIFETIME` trong `app/__init__.py` (mặc định: 24 giờ)
- Check checkbox "Ghi nhớ đăng nhập" đã được check khi đăng nhập

### Session không persist sau khi đóng browser?

- Đảm bảo checkbox "Ghi nhớ đăng nhập" được check
- Check `session.permanent = True` được set trong login route
- Check browser không tự động xóa cookies khi đóng
