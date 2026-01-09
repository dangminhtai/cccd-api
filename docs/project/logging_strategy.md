# Logging Strategy - Chiến lược Logging

## Tổng quan

Hiện tại hệ thống có **2 cách logging**:

1. **Flask Logger (Terminal/File)** - Đang dùng
   - Log vào terminal khi chạy server
   - Có thể redirect vào file log
   - Nhanh, không ảnh hưởng performance
   - Khó query/search

2. **Database Logs** - Optional
   - Lưu vào bảng `request_logs`
   - Dễ query, phân tích
   - Có thể làm chậm nếu ghi sync
   - Cần cleanup strategy

---

## Khi nào cần Database Logs?

### ✅ Nên dùng Database Logs khi:
- **Production environment** với nhiều requests
- **Cần audit trail** (ai gọi API khi nào)
- **Cần phân tích usage patterns** (tỉnh nào được parse nhiều nhất, error rate, etc.)
- **Compliance requirements** (GDPR, security audit)
- **Debug production issues** (tìm request theo request_id)

### ❌ Không cần Database Logs khi:
- **Development/Testing** - Flask logger đủ
- **Small scale** (< 1000 requests/day)
- **Không cần query logs** - chỉ cần xem terminal/file
- **Performance critical** - ghi database có thể làm chậm

---

## So sánh

| Tính năng | Flask Logger | Database Logs |
|-----------|-------------|---------------|
| **Performance** | ⚡ Nhanh | 🐌 Có thể chậm |
| **Query/Search** | ❌ Khó | ✅ Dễ (SQL) |
| **Storage** | File/terminal | Database |
| **Retention** | File rotation | Cần cleanup |
| **Analytics** | ❌ Khó | ✅ Dễ |
| **Audit Trail** | ⚠️ Khó trace | ✅ Tốt |
| **Setup** | ✅ Sẵn có | ⚠️ Cần tạo bảng |

---

## Khuyến nghị

### Development/Testing:
- ✅ **Chỉ dùng Flask Logger** (terminal logs)
- Đủ để debug và test

### Production (Small scale):
- ✅ **Flask Logger** (file logs)
- ⚠️ **Optional:** Database logs nếu cần audit

### Production (Large scale):
- ✅ **Flask Logger** (file logs) - cho real-time monitoring
- ✅ **Database Logs** - cho analytics và audit
- 💡 **Cân nhắc:** Ghi async (background job) để không làm chậm API

---

## Implementation

### Option 1: Chỉ Flask Logger (Hiện tại)
```python
# Đã có sẵn
current_app.logger.info(f"cccd_parsed | request_id={req_id} | ...")
```

### Option 2: Thêm Database Logs (Optional)
```python
# Thêm vào routes/cccd.py sau khi xử lý request
from services.logging_service import log_to_database

log_to_database(
    request_id=req_id,
    api_key_id=key_info.id if key_info else None,
    status_code=200,
    cccd_masked=masked_cccd,
    ...
)
```

### Option 3: Hybrid (Khuyến nghị cho Production)
- Flask Logger: Real-time monitoring
- Database Logs: Analytics và audit (có thể async)

---

## Cleanup Strategy

Nếu dùng Database Logs, cần cleanup định kỳ:

```sql
-- Xóa logs cũ hơn 90 ngày
DELETE FROM request_logs 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

Có thể chạy bằng:
- Cron job (Linux)
- Scheduled task (Windows)
- Background worker (Celery, etc.)

---

## Kết luận

**Hiện tại:** Không cần Database Logs cho development/testing.

**Sau này:** Cân nhắc thêm Database Logs khi:
- Deploy production
- Cần analytics/audit
- Có nhiều requests

**File schema:** `scripts/db_schema_logs.sql` (đã tạo sẵn, chỉ cần chạy khi cần)
