# Hướng dẫn: Tạo hệ thống API Key theo Tier (Free/Premium/Ultra)

## Tổng quan

Bạn muốn bán API theo 3 gói:

| Tier | Rate Limit | Giá |
|------|------------|-----|
| `free` | 10 requests/phút | Miễn phí |
| `premium` | 100 requests/phút | $9/tháng |
| `ultra` | 1000 requests/phút | $49/tháng |

---

## Bước 1: Thiết kế Database lưu API Key

Tạo file `data/api_keys.json` (đơn giản) hoặc dùng SQLite/PostgreSQL (production):

```json
{
  "keys": [
    {
      "key": "free_abc123",
      "tier": "free",
      "owner_email": "user1@example.com",
      "created_at": "2026-01-09",
      "expires_at": null,
      "active": true
    },
    {
      "key": "premium_xyz789",
      "tier": "premium",
      "owner_email": "user2@example.com",
      "created_at": "2026-01-09",
      "expires_at": "2026-02-09",
      "active": true
    }
  ]
}
```

---

## Bước 2: Tạo script sinh API Key hàng loạt

Tạo file `scripts/generate_keys.py`:

```python
import json
import secrets
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path("data/api_keys.json")

def load_keys():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"keys": []}

def save_keys(data):
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def generate_key(tier: str) -> str:
    """Tạo key có prefix theo tier"""
    prefix = {"free": "free", "premium": "prem", "ultra": "ultr"}
    random_part = secrets.token_hex(16)  # 32 chars
    return f"{prefix.get(tier, 'unkn')}_{random_part}"

def create_keys(tier: str, count: int, owner_email: str, days_valid: int = None):
    """Tạo nhiều key cùng lúc"""
    data = load_keys()
    
    created_at = datetime.now().strftime("%Y-%m-%d")
    expires_at = None
    if days_valid:
        expires_at = (datetime.now() + timedelta(days=days_valid)).strftime("%Y-%m-%d")
    
    new_keys = []
    for _ in range(count):
        key = generate_key(tier)
        entry = {
            "key": key,
            "tier": tier,
            "owner_email": owner_email,
            "created_at": created_at,
            "expires_at": expires_at,
            "active": True
        }
        data["keys"].append(entry)
        new_keys.append(key)
    
    save_keys(data)
    return new_keys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate API keys")
    parser.add_argument("--tier", required=True, choices=["free", "premium", "ultra"])
    parser.add_argument("--count", type=int, default=1, help="Số key cần tạo")
    parser.add_argument("--email", required=True, help="Email chủ sở hữu")
    parser.add_argument("--days", type=int, help="Số ngày hợp lệ (để trống = vĩnh viễn)")
    
    args = parser.parse_args()
    keys = create_keys(args.tier, args.count, args.email, args.days)
    
    print(f"Đã tạo {len(keys)} key(s) tier '{args.tier}':")
    for k in keys:
        print(f"  {k}")
```

**Cách dùng:**

```powershell
# Tạo 1 key free
python scripts/generate_keys.py --tier free --email user@example.com

# Tạo 10 key premium, hết hạn sau 30 ngày
python scripts/generate_keys.py --tier premium --count 10 --email bulk@company.com --days 30

# Tạo 5 key ultra vĩnh viễn
python scripts/generate_keys.py --tier ultra --count 5 --email vip@company.com
```

---

## Bước 3: Sửa logic validate API Key theo tier

Tạo file `services/api_key_service.py`:

```python
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

DATA_FILE = Path("data/api_keys.json")

@dataclass
class APIKeyInfo:
    key: str
    tier: str
    owner_email: str
    active: bool
    expired: bool

TIER_LIMITS = {
    "free": "10 per minute",
    "premium": "100 per minute",
    "ultra": "1000 per minute",
}

def get_key_info(api_key: str) -> APIKeyInfo | None:
    """Tra cứu thông tin key"""
    if not DATA_FILE.exists():
        return None
    
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    
    for entry in data.get("keys", []):
        if entry["key"] == api_key:
            # Check expired
            expired = False
            if entry.get("expires_at"):
                exp_date = datetime.strptime(entry["expires_at"], "%Y-%m-%d")
                expired = datetime.now() > exp_date
            
            return APIKeyInfo(
                key=api_key,
                tier=entry["tier"],
                owner_email=entry["owner_email"],
                active=entry.get("active", True),
                expired=expired,
            )
    
    return None

def get_rate_limit(api_key: str) -> str:
    """Lấy rate limit theo tier của key"""
    info = get_key_info(api_key)
    if info and info.active and not info.expired:
        return TIER_LIMITS.get(info.tier, "10 per minute")
    return "10 per minute"  # default cho key không hợp lệ
```

---

## Bước 4: Cập nhật route để dùng tier-based rate limit

Sửa `routes/cccd.py`:

```python
from services.api_key_service import get_key_info, get_rate_limit, TIER_LIMITS

@cccd_bp.post("/v1/cccd/parse")
def cccd_parse():
    # ... existing code ...
    
    # API Key check with tier
    provided_api_key = request.headers.get("X-API-Key")
    key_info = get_key_info(provided_api_key) if provided_api_key else None
    
    if key_info is None:
        return jsonify({"success": False, "message": "API key không hợp lệ."}), 401
    
    if not key_info.active:
        return jsonify({"success": False, "message": "API key đã bị vô hiệu hóa."}), 401
    
    if key_info.expired:
        return jsonify({"success": False, "message": "API key đã hết hạn."}), 401
    
    # ... rest of the code ...
```

Sửa `app/__init__.py` để rate limit theo tier:

```python
from services.api_key_service import get_rate_limit

def _dynamic_rate_limit():
    api_key = request.headers.get("X-API-Key")
    return get_rate_limit(api_key)

limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[_dynamic_rate_limit],  # Dynamic!
    storage_uri="memory://"
)
```

---

## Bước 5: Tạo Admin API để quản lý key

Tạo file `routes/admin.py`:

```python
from flask import Blueprint, jsonify, request
from services.api_key_service import get_key_info
import json
from pathlib import Path

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
DATA_FILE = Path("data/api_keys.json")
ADMIN_SECRET = "your-admin-secret"  # Đặt trong .env

@admin_bp.before_request
def check_admin_auth():
    if request.headers.get("X-Admin-Key") != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

@admin_bp.get("/keys")
def list_keys():
    """Liệt kê tất cả key"""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return jsonify(data)

@admin_bp.post("/keys/<key>/deactivate")
def deactivate_key(key):
    """Vô hiệu hóa key"""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for entry in data["keys"]:
        if entry["key"] == key:
            entry["active"] = False
            DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return jsonify({"message": f"Key {key} đã bị vô hiệu hóa"})
    return jsonify({"error": "Key not found"}), 404

@admin_bp.get("/keys/<key>/usage")
def key_usage(key):
    """Xem usage của key (cần thêm tracking)"""
    # TODO: Implement usage tracking
    return jsonify({"key": key, "requests_today": 0, "requests_month": 0})
```

---

## Bước 6: Tracking Usage (để tính tiền)

Tạo file `services/usage_tracker.py`:

```python
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

USAGE_FILE = Path("data/usage.json")

def log_request(api_key: str):
    """Ghi nhận 1 request"""
    data = _load_usage()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if api_key not in data:
        data[api_key] = {}
    if today not in data[api_key]:
        data[api_key][today] = 0
    
    data[api_key][today] += 1
    _save_usage(data)

def get_usage(api_key: str, days: int = 30) -> dict:
    """Lấy usage trong N ngày gần nhất"""
    data = _load_usage()
    return data.get(api_key, {})

def _load_usage():
    if USAGE_FILE.exists():
        return json.loads(USAGE_FILE.read_text())
    return {}

def _save_usage(data):
    USAGE_FILE.write_text(json.dumps(data, indent=2))
```

Thêm vào `routes/cccd.py`:

```python
from services.usage_tracker import log_request

# Sau khi validate key thành công:
log_request(provided_api_key)
```

---

## Tóm tắt cấu trúc file

```
CCCD-API/
├── data/
│   ├── api_keys.json      # Lưu danh sách key
│   └── usage.json         # Lưu usage tracking
├── scripts/
│   └── generate_keys.py   # Script tạo key hàng loạt
├── services/
│   ├── api_key_service.py # Logic validate key + tier
│   └── usage_tracker.py   # Tracking usage
├── routes/
│   ├── admin.py           # Admin API quản lý key
│   └── cccd.py            # (sửa) validate key theo tier
```

---

## Self-check

| Test | Lệnh | Kỳ vọng |
|------|------|---------|
| Tạo key free | `python scripts/generate_keys.py --tier free --email test@x.com` | Tạo key `free_xxx` |
| Tạo 5 key premium | `... --tier premium --count 5 --days 30` | 5 key `prem_xxx` |
| Dùng key free | Gọi API với key | Rate limit 10/phút |
| Dùng key premium | Gọi API với key | Rate limit 100/phút |
| Key hết hạn | Gọi API với key đã expire | 401 "đã hết hạn" |
| Deactivate key | `POST /admin/keys/{key}/deactivate` | Key bị vô hiệu |

---

## Production Notes

1. **Đừng dùng JSON file** cho production → dùng PostgreSQL/MySQL
2. **Mã hóa key** trong database (hash, không lưu plaintext)
3. **Redis** cho rate limiting (thay vì memory)
4. **Stripe/PayPal** để tự động tạo key khi thanh toán
5. **Dashboard** cho khách hàng xem usage của họ

