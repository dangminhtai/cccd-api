# guide_step_10.md — Bước 10: Hệ thống API Key theo Tier (bán gói)

## Mục tiêu

Tạo hệ thống bán API theo 3 gói: Free, Premium, Ultra với rate limit khác nhau.

| Tier | Rate Limit | Giá (ví dụ) |
|------|------------|-------------|
| `free` | 10 req/phút | Miễn phí |
| `premium` | 100 req/phút | $9/tháng |
| `ultra` | 1000 req/phút | $49/tháng |

---

## Checklist

### A. Chuẩn bị MySQL

- [X] Đã cài MySQL trên máy
- [X] Đã tạo database `cccd_api`
- [X] Đã chạy script tạo bảng

**Cách làm:**

1. Mở MySQL Workbench hoặc terminal MySQL
2. Chạy file `scripts/db_schema.sql`:
   ```
   mysql -u root -p < scripts/db_schema.sql
   ```
3. Verify: chạy `SHOW TABLES;` → thấy 3 bảng: `api_keys`, `api_usage`, `tier_config`

---

### B. Cấu hình .env

- [X] Đã set `API_KEY_MODE=tiered`
- [X] Đã điền thông tin MySQL
- [ ] Đã đặt `ADMIN_SECRET`

**Cách làm:**

1. Mở file `.env`
2. Sửa các dòng sau:

```env
API_KEY_MODE=tiered

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=cccd_api

ADMIN_SECRET=change-this-to-random-string
```

3. Lưu file

---

### C. Cài thư viện MySQL

- [X] Đã cài PyMySQL

**Cách làm:**

```powershell
pip install PyMySQL==1.1.0
```

---

### D. Restart server

- [X] Server đang chạy với mode tiered

**Cách làm:**

1. Dừng server cũ: `Ctrl+C`
2. Chạy lại: `python run.py`
3. Verify: không có lỗi kết nối MySQL

---

### E. Tạo API key đầu tiên

- [ ] Đã tạo được key free
- [ ] Đã lưu key (chỉ hiển thị 1 lần!)

**Cách làm:**

```powershell
python scripts/generate_keys.py --tier free --email test@example.com
```

Output mẫu:
```
Tạo 1 key(s) tier 'free' cho test@example.com...
------------------------------------------------------------
  [1] free_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
------------------------------------------------------------
Đã tạo 1/1 key(s)

⚠️  LƯU Ý: Key chỉ hiển thị 1 lần này. Hãy lưu lại!
```

**Copy và lưu key này!**

---

### F. Test API với key mới

- [X] Gọi API với key → 200 success
- [X] Gọi API không có key → 401

**Cách làm:**

1. Mở `/demo` trên browser
2. Nhập key vừa tạo vào ô "API Key"
3. Nhập CCCD `079203012345`
4. Bấm Parse → **200** success

Hoặc test bằng PowerShell:

```powershell
# Thay YOUR_KEY bằng key vừa tạo
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="free_70f0e1c4350f756a97c785db25633ea2"} -Body '{"cccd": "079203012345"}'
```

---

### G. Tạo key hàng loạt (cho khách hàng)

- [X] Biết cách tạo nhiều key cùng lúc
- [X] Biết cách tạo key có thời hạn

**Cách làm:**

```powershell
# Tạo 10 key premium, hết hạn sau 30 ngày
python scripts/generate_keys.py --tier premium --count 10 --email bulk@company.com --days 30

# Tạo 5 key ultra vĩnh viễn
python scripts/generate_keys.py --tier ultra --count 5 --email vip@company.com
```

---

### H. Sử dụng Admin Dashboard

- [X] Biết cách xem thống kê trên web
- [X] Biết cách tạo key trên web
- [ ] Biết cách tạo key qua API (nếu cần tự động hoá)

**Xem thống kê trên web:**

1. Mở trình duyệt: `http://127.0.0.1:8000/admin/`
2. Nhập Admin Secret Key (từ `.env`, biến `ADMIN_SECRET`)
3. Bấm "Tải thống kê"
4. Xem:
   - Requests hôm nay
   - Tổng số keys theo tier (free/premium/ultra)
   - Số keys đang hoạt động

**Tạo key trên web:**

1. Trên trang `/admin/`, scroll xuống phần "🔑 Tạo API Key mới"
2. Chọn Tier (Free/Premium/Ultra)
3. Nhập Email chủ sở hữu
4. (Tuỳ chọn) Nhập số ngày hợp lệ (để trống = vĩnh viễn)
5. Bấm "Tạo Key"
6. **Copy key ngay** - chỉ hiển thị 1 lần!

**Tạo key qua API (nếu cần tự động hoá):**

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/keys/create" -Method POST -ContentType "application/json" -Headers @{"X-Admin-Key"="your-admin-secret"} -Body '{"tier": "premium", "email": "customer@example.com", "days": 30}' | ConvertTo-Json -Depth 3
```

**Vô hiệu hóa key:**

```powershell
# Thay free_abc123 bằng prefix của key cần vô hiệu
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/keys/free_abc123/deactivate" -Method POST -Headers @{"X-Admin-Key"="your-admin-secret"} | ConvertTo-Json
```

---

## Hoàn thành khi

- [x] MySQL đã setup với 3 bảng
- [x] `.env` đã cấu hình `API_KEY_MODE=tiered`
- [x] Tạo được key bằng script
- [x] Gọi API với key → thành công
- [x] Gọi API không có key → 401
- [x] Admin API hoạt động

---

## Tự test (Self-check)

### Test trên /demo

| Bước | Hành động | Kỳ vọng |
|------|-----------|---------|
| 1 | Mở `/demo` | Trang hiển thị |
| 2 | Để trống API Key, bấm Parse | **401** - thiếu key |
| 3 | Nhập key free vừa tạo, bấm Parse | **200** - success |
| 4 | Nhập key sai `wrong_key`, bấm Parse | **401** - key không hợp lệ |

### Test tạo key

| Lệnh | Kỳ vọng |
|------|---------|
| `python scripts/generate_keys.py --tier free --email x@y.com` | Tạo `free_xxx` |
| `python scripts/generate_keys.py --tier premium --email x@y.com` | Tạo `prem_xxx` |
| `python scripts/generate_keys.py --tier ultra --email x@y.com` | Tạo `ultr_xxx` |

### Test Admin Dashboard

| Bước | Hành động | Kỳ vọng |
|------|-----------|---------|
| 1 | Mở `http://127.0.0.1:8000/admin/` | Trang admin hiển thị |
| 2 | Nhập Admin Secret Key (từ .env) | Input nhận được |
| 3 | Bấm "Tải thống kê" | Thấy stats: requests_today, tiers table |
| 4 | Nhập sai Admin Key | **403** - Unauthorized |

### Test tạo key trên web

| Bước | Hành động | Kỳ vọng |
|------|-----------|---------|
| 1 | Scroll xuống phần "Tạo API Key mới" | Form hiển thị |
| 2 | Chọn Tier = Premium | Dropdown chọn được |
| 3 | Nhập email `test@example.com` | Input nhận được |
| 4 | Nhập days = 30 | Input nhận được |
| 5 | Bấm "Tạo Key" | Thấy key `prem_xxx` hiển thị |
| 6 | Copy key và test trên `/demo` | **200** - success |

### Test Rate Limit theo Tier

| Tier | Test | Kỳ vọng |
|------|------|---------|
| **Free** | Tạo key free, gọi API 10 lần liên tiếp | 10 lần đầu → **200**, lần 11 → **429** |
| **Premium** | Tạo key premium, gọi API 100 lần | 100 lần đầu → **200**, lần 101 → **429** |
| **Ultra** | Tạo key ultra, gọi API nhiều lần | Không bị 429 (1000 req/phút) |

**Cách test Free tier (10 req/phút):**

1. Tạo key free: `/admin/` → Tạo key free cho `test@example.com`
2. Copy key (ví dụ: `free_abc123...`)
3. Mở PowerShell, chạy script:

```powershell
$key = "free_abc123..."  # Thay bằng key thật
for ($i=1; $i -le 11; $i++) {
    Write-Host "Request $i"
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"=$key} -Body '{"cccd": "079203012345"}'
        Write-Host "  Status: 200 OK"
    } catch {
        Write-Host "  Status: $($_.Exception.Response.StatusCode.value__)"
        if ($_.Exception.Response.StatusCode.value__ -eq 429) {
            Write-Host "  ✅ Rate limit hoạt động đúng!"
            break
        }
    }
    Start-Sleep -Milliseconds 100
}
```

4. Kỳ vọng: Request 1-10 → 200, Request 11 → **429**

**Cách test Premium tier (100 req/phút):**

Tương tự, nhưng tạo key premium và test 101 requests.

### Test Email Validation

| Email nhập | Kỳ vọng |
|------------|---------|
| `test@example.com` | ✅ **200** - hợp lệ |
| `user.name@example.com` | ✅ **200** - hợp lệ |
| `not-an-email` | ❌ **400** - "Email không hợp lệ" |
| `@example.com` | ❌ **400** - "Email không hợp lệ" |
| `user@` | ❌ **400** - "Email không hợp lệ" |
| `user@.com` | ❌ **400** - "Email không hợp lệ" |
| *(để trống)* | ❌ **400** - "email là bắt buộc" |

**Cách test:**

1. Mở `/admin/`
2. Scroll xuống form "Tạo API Key mới"
3. Nhập email sai format → Bấm "Tạo Key"
4. Xem error message

### Test Days Validation

| Days nhập | Kỳ vọng |
|-----------|---------|
| `30` | ✅ **200** - hợp lệ |
| `1` | ✅ **200** - hợp lệ |
| `0` | ❌ **400** - "Số ngày phải >= 1" |
| `-1` | ❌ **400** - "Số ngày phải >= 1" |
| `abc` | ❌ **400** - "Số ngày phải là số nguyên" |
| *(để trống)* | ✅ **200** - vĩnh viễn |

### Verify trong MySQL

```sql
SELECT key_prefix, tier, owner_email, active FROM api_keys;
```

→ Thấy các key vừa tạo

---

## ✅ DoD (Definition of Done) - Bước 10

| Tiêu chí | Cách verify | ✓ |
|----------|-------------|---|
| MySQL setup | `SHOW TABLES;` → 3 bảng | |
| Tạo key script | `python scripts/generate_keys.py --tier free --email x@y.com` | |
| API với key | `/demo` + key → 200 | |
| API không key | `/demo` không key → 401 | |
| Admin Dashboard | `/admin/` → nhập key → thấy stats | |
| Tạo key trên web | `/admin/` → form → tạo key thành công | |
| Rate limit Free | Key free → 11 requests → lần 11 = 429 | |
| Rate limit Premium | Key premium → 101 requests → lần 101 = 429 | |
| Email validation | Email sai format → 400 | |
| Days validation | Days < 1 hoặc không phải số → 400 | |
| Automated tests | `python -m pytest tests/` → all pass | |

---

## Lưu ý bảo mật

1. **Key chỉ hiển thị 1 lần** - sau khi tạo, chỉ lưu hash trong DB
2. **ADMIN_SECRET** - đặt chuỗi dài, ngẫu nhiên, không để mặc định
3. **MySQL password** - không commit vào git (đã ignore trong .gitignore)
