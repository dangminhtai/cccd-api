# CCCD API

API parse thông tin từ số CCCD (Căn cước công dân) Việt Nam.

## Tính năng

- ✅ Parse CCCD 12 số → tỉnh/thành, giới tính, năm sinh
- ✅ Hỗ trợ 2 phiên bản tỉnh/thành: `legacy_63` (63 tỉnh cũ) và `current_34` (34 tỉnh mới)
- ✅ Validate đầu vào, trả lỗi rõ ràng
- ✅ Rate limiting, API key authentication
- ✅ Log an toàn (che CCCD)

## 📚 Tài liệu

- **Quick Start:** Xem phần "Chạy Local" bên dưới
- **API Reference:** Xem [`docs/project/requirement.md`](docs/project/requirement.md)
- **Development Guides:** Xem [`docs/guides/`](docs/guides/)
- **Security Testing:** Xem [`docs/security/`](docs/security/)
- **Project Docs:** Xem [`docs/project/`](docs/project/)

---

## Chạy Local (5 phút)

### 1. Clone repo

```bash
git clone https://github.com/dangminhtai/cccd-api.git
cd cccd-api
```

### 2. Cài dependencies

```bash
pip install -r requirements.txt
```

### 3. Tạo file `.env`

Copy từ `env.example`:

```bash
copy env.example .env
```

Sửa `.env` nếu cần:

```env
PORT=8000
DEFAULT_PROVINCE_VERSION=current_34
API_KEY=                # Để trống = không yêu cầu API key
```

### 4. Chạy server

```bash
python run.py
```

Server sẽ chạy ở `http://127.0.0.1:8000`

### 5. Test nhanh

Mở trình duyệt: `http://127.0.0.1:8000/demo`

---

## API Reference

### `POST /v1/cccd/parse`

Parse thông tin từ CCCD.

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: <key>` (nếu đã cấu hình API_KEY trong .env)

**Body:**
```json
{
  "cccd": "079203012345",
  "province_version": "legacy_63"  // optional: legacy_63 | current_34
}
```

**Response (200):**
```json
{
  "success": true,
  "is_valid_format": true,
  "is_plausible": true,
  "province_version": "legacy_63",
  "data": {
    "province_code": "079",
    "province_name": "Hồ Chí Minh",
    "gender": "Nam",
    "birth_year": 2003,
    "century": 21,
    "age": 23
  },
  "warnings": []
}
```

**Response (400 - input sai):**
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12)."
}
```

**Response (401 - sai API key):**
```json
{
  "success": false,
  "message": "API key không hợp lệ hoặc thiếu."
}
```

---

## Ví dụ gọi API

### PowerShell (Windows)

```powershell
# Không có API key
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Body '{"cccd": "079203012345"}'

# Có API key
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" -Method POST -ContentType "application/json" -Headers @{"X-API-Key"="your-key"} -Body '{"cccd": "079203012345"}'
```

### curl (Linux/Mac)

```bash
curl -X POST http://127.0.0.1:8000/v1/cccd/parse \
  -H "Content-Type: application/json" \
  -d '{"cccd": "079203012345"}'
```

### Python

```python
import requests

resp = requests.post(
    "http://127.0.0.1:8000/v1/cccd/parse",
    json={"cccd": "079203012345"},
    headers={"X-API-Key": "your-key"}  # nếu cần
)
print(resp.json())
```

---

## Quy ước

| Quy ước | Giá trị |
|---------|---------|
| Độ dài CCCD | 12 chữ số |
| Format gender | `Nam` / `Nữ` |
| Province versions | `legacy_63`, `current_34` |
| Rate limit | 30 requests/phút (mặc định) |

---

## Cấu trúc project

```
CCCD-API/
├── app/                    # Flask app
│   ├── __init__.py         # App factory
│   ├── config.py           # Settings
│   └── templates/          # Demo page
├── routes/                 # API routes
│   ├── health.py           # Health check
│   └── cccd.py             # Main API
├── services/               # Business logic
│   ├── cccd_parser.py      # Parse CCCD
│   └── province_mapping.py # Province lookup
├── data/                   # Data files
│   ├── provinces_legacy_63.json
│   └── provinces_current_34.json
├── docs/                   # Documentation
│   ├── guides/             # Step-by-step guides
│   ├── security/           # Security testing docs & results
│   └── project/            # Project docs (requirement, rules, etc.)
├── scripts/                # Utility scripts
├── tests/                  # Unit tests
├── run.py                  # Entry point
├── requirements.txt        # Dependencies
└── env.example             # Environment template
```

---

## Chạy Tests

```bash
python -m pytest tests/ -v
```

---

## Production

Dùng gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

---

## License

MIT

