# guide_step_08.md — Bước 8: Test

## Mục tiêu

Đảm bảo API chạy ổn định và không bị "mỗi nơi một kiểu" khi đổi người làm/đổi phiên bản.

## Việc cần làm

- Unit test validate:
  - thiếu `cccd`
  - `cccd` có chữ
  - sai độ dài
- Unit test parse:
  - vài CCCD giả lập để ra đúng `birth_year`, `gender`, `province_code`
- Unit test mapping:
  - cùng `province_code` nhưng `legacy_63` vs `current_34`
- API test:
  - gọi `POST /v1/cccd/parse` và kiểm tra response có đủ field

## Hoàn thành khi

- [x] Chạy test pass hết (18 tests)
- [x] Khi đổi mapping/tên tỉnh, test giúp phát hiện sai lệch ngay

## Tự test (Self-check)

Mở `/demo` trên trình duyệt và test từng trường hợp sau:

### 1. Test Validation (input không hợp lệ)

| Nhập vào ô CCCD | Kỳ vọng |
|-----------------|---------|
| *(để trống)* | **400** - "Thiếu trường cccd" |
| `123` | **400** - "CCCD không hợp lệ" |
| `12345678901234567890` | **400** - (quá dài, bị reject) |
| `07920301234a` | **400** - (có chữ) |
| `079203012345` | **200** - success=true ✅ |

### 2. Test API Key (nếu đã bật trong .env)

| API Key nhập | Kỳ vọng |
|--------------|---------|
| *(để trống)* | **401** - "API key không hợp lệ" |
| `wrongkey` | **401** |
| *(đúng key)* | **200** ✅ |

### 3. Test Parse đúng

Nhập `079203012345` (CCCD hợp lệ):

| Field | Kỳ vọng |
|-------|---------|
| `province_code` | `079` |
| `gender` | `Nam` |
| `birth_year` | `2003` |
| `century` | `21` |
| `province_name` | `Hồ Chí Minh` (nếu legacy_63) |

### 4. Test Province Version

| Chọn dropdown | Kỳ vọng |
|---------------|---------|
| `legacy_63` | `province_version: "legacy_63"` |
| `current_34` | `province_version: "current_34"` |

### 5. Test Plausibility (năm sinh tương lai)

Nhập `052399012345` (năm sinh 2099):
- `is_plausible: false`
- `warnings` có `birth_year_in_future`

### 6. Test Backend trực tiếp (Terminal)

Nếu nghi ngờ lỗi từ backend, copy-paste các lệnh sau vào PowerShell.

> ⚠️ **Nếu bạn đã bật `API_KEY` trong `.env`**: thêm `-Headers @{"X-API-Key"="your-key"}` vào mỗi lệnh, hoặc tắt API_KEY tạm thời bằng cách comment dòng `API_KEY=...` trong `.env` rồi restart server.

#### A. Nếu CHƯA bật API_KEY (hoặc đã tắt tạm):

**Test CCCD hợp lệ:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "079203012345"}'
```
→ Kỳ vọng: `success: True`, `province_code: 079`, `gender: Nam`

**Test CCCD sai format:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "123"}'
```
→ Kỳ vọng: Lỗi 400 "CCCD không hợp lệ"

**Test thiếu CCCD:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{}'
```
→ Kỳ vọng: Lỗi 400 "Thiếu trường cccd"

**Test string cực dài (DoS protection):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "000000000000000000000000000000000000000000000000000"}'
```
→ Kỳ vọng: Lỗi 400 (reject ngay, không xử lý)

#### B. Nếu ĐÃ bật API_KEY:

Thay `YOUR_API_KEY` bằng key thật trong `.env`:

**Test CCCD hợp lệ (có API Key):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="YOUR_API_KEY"} -Body '{"cccd": "079203012345"}'
```
→ Kỳ vọng: `success: True`

**Test sai API Key:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="wrong-key"} -Body '{"cccd": "079203012345"}'
```
→ Kỳ vọng: Lỗi 401 "API key không hợp lệ"

**Test thiếu API Key:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "079203012345"}'
```
→ Kỳ vọng: Lỗi 401 "API key không hợp lệ hoặc thiếu"

---

### 7. (Bonus) Chạy automated tests

```bash
python -m pytest tests/ -v
```
Kỳ vọng: **18 passed**

---

## ✅ DoD (Definition of Done) - Bước 8

| Tiêu chí | Kết quả |
|----------|---------|
| Validation tests (8 cases) | ✅ |
| API Key tests (4 cases) | ✅ |
| Parser tests (2 cases) | ✅ |
| Mapping tests (3 cases) | ✅ |
| Plausibility tests (1 case) | ✅ |
| Tổng: **18 tests pass** | ✅ |



