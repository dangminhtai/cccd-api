# Bảo vệ chống Brute Force Attack cho Admin Endpoints

> Tài liệu này mô tả các biện pháp bảo vệ chống brute force attack trên admin endpoints.

---

## 1. Vấn đề

Nếu attacker có thể brute force admin key, họ có thể:
- Truy cập toàn bộ admin endpoints
- Xem thông tin nhạy cảm (users, payments, API keys)
- Thao tác dữ liệu (approve/reject payments, delete users, etc.)

**Rủi ro**: Admin key có thể bị đoán nếu:
- Key quá ngắn hoặc dễ đoán
- Không có rate limiting
- Không có IP blocking
- Không có logging failed attempts

---

## 2. Các biện pháp đã triển khai

### 2.1 IP Blocking

**Cơ chế**:
- Sau **5 failed attempts** trong **60 giây**, IP sẽ bị block
- Thời gian block: **5 phút** (300 giây)
- Tự động unblock sau khi hết thời gian

**Implementation**:
- File: `services/admin_security.py`
- Function: `is_ip_blocked()`, `record_failed_attempt()`
- Storage: In-memory (trong production nên dùng Redis)

**Response khi bị block**:
```json
{
  "error": "IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau 300 giây.",
  "blocked_until": 1234567890,
  "remaining_seconds": 300
}
```
Status code: `429 Too Many Requests`

### 2.2 Exponential Backoff Delay

**Cơ chế**:
- Mỗi lần failed attempt, response sẽ bị delay
- Delay tăng dần theo số lần failed:
  - Lần 1: 0.1 giây
  - Lần 2: 0.2 giây
  - Lần 3: 0.4 giây
  - Lần 4: 0.8 giây
  - Lần 5+: 1.6 giây (max 2 giây)

**Mục đích**: Làm chậm brute force attack, tăng thời gian cần thiết để thử nhiều keys.

### 2.3 Rate Limiting

**Cơ chế**:
- Sử dụng Flask-Limiter
- Giới hạn số requests per minute cho từng IP
- Áp dụng cho tất cả admin endpoints

**Limits**:
- `/admin/keys/create`: 10 requests/minute
- `/admin/stats`: 30 requests/minute
- `/admin/security-stats`: 10 requests/minute
- Các endpoints khác: Default limit (30/minute)

### 2.4 Logging Failed Attempts

**Cơ chế**:
- Log tất cả failed attempts với:
  - IP address
  - Endpoint
  - Timestamp
  - Số lần failed trong window
  - Request ID

**Log format**:
```
admin_auth_failed | request_id=abc123 | ip=192.168.1.1 | endpoint=admin.get_stats | failed_count=3
admin_blocked_ip | request_id=abc123 | ip=192.168.1.1 | endpoint=admin.get_stats | unblock_in=300s
```

**Mục đích**: 
- Monitor và alert khi có nhiều failed attempts
- Phân tích attack patterns
- Forensic investigation

### 2.5 Security Stats Endpoint

**Endpoint**: `GET /admin/security-stats`

**Response**:
```json
{
  "success": true,
  "security": {
    "blocked_ips_count": 2,
    "total_failed_attempts": 15,
    "unique_ips_with_failures": 5
  }
}
```

**Mục đích**: Admin có thể monitor security status real-time.

---

## 3. Configuration

### 3.1 Các tham số có thể điều chỉnh

Trong `services/admin_security.py`:

```python
MAX_FAILED_ATTEMPTS = 5  # Số lần thử sai tối đa
BLOCK_DURATION_SECONDS = 300  # Block 5 phút
WINDOW_SECONDS = 60  # Time window để đếm failed attempts (60 giây)
```

### 3.2 Admin Secret Key Best Practices

**Độ dài**: Nên >= 32 ký tự (khuyến nghị: 64 ký tự)

**Độ phức tạp**: 
- Chữ hoa, chữ thường
- Số
- Ký tự đặc biệt
- Không dùng từ điển (dictionary words)

**Ví dụ tốt**:
```
ADMIN_SECRET=Kx9#mP2$vL8@nQ4&wR6!tY7*uI1^oE3%aS5
```

**Ví dụ không tốt**:
```
ADMIN_SECRET=admin123
ADMIN_SECRET=password
ADMIN_SECRET=dangminhtai  # Quá ngắn và dễ đoán
```

---

## 4. Test Brute Force Protection

### 4.1 Test IP Blocking

```powershell
# Test với key sai nhiều lần
$wrongKey = "wrong-key"
for ($i = 1; $i -le 6; $i++) {
    Write-Host "Attempt $i"
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=$wrongKey} -ErrorAction Stop
        Write-Host "Response: $($response | ConvertTo-Json)"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status: $statusCode"
        if ($statusCode -eq 429) {
            Write-Host "✅ IP BLOCKED - Protection working!"
            break
        }
    }
    Start-Sleep -Seconds 1
}
```

**Kỳ vọng**:
- Attempts 1-5: `403 Forbidden` (với delay tăng dần)
- Attempt 6+: `429 Too Many Requests` (IP blocked)

### 4.2 Test Exponential Backoff

```powershell
# Đo thời gian response
$wrongKey = "wrong-key"
$times = @()

for ($i = 1; $i -le 5; $i++) {
    $start = Get-Date
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=$wrongKey} -ErrorAction Stop
    } catch {
        # Ignore
    }
    $end = Get-Date
    $duration = ($end - $start).TotalSeconds
    $times += $duration
    Write-Host "Attempt $i: $duration seconds"
}

Write-Host "Delays should increase: $($times -join ', ')"
```

**Kỳ vọng**: Thời gian response tăng dần (0.1s → 0.2s → 0.4s → 0.8s → 1.6s)

### 4.3 Test Rate Limiting

```powershell
# Gửi nhiều requests nhanh
$correctKey = "your-admin-secret"
for ($i = 1; $i -le 35; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/stats" -Method GET -Headers @{"X-Admin-Key"=$correctKey} -ErrorAction Stop
        Write-Host "Request $i: OK"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 429) {
            Write-Host "Request $i: ✅ RATE LIMITED"
            break
        }
    }
}
```

**Kỳ vọng**: Sau 30 requests trong 1 phút → `429 Too Many Requests`

---

## 5. Monitoring & Alerting

### 5.1 Log Monitoring

Monitor logs để phát hiện:
- Nhiều failed attempts từ cùng IP
- Nhiều IPs khác nhau cùng thử failed
- Pattern của brute force attack

**Ví dụ log query** (nếu dùng log aggregation tool):
```
admin_auth_failed | count by ip | where count > 10
```

### 5.2 Alert Thresholds

Nên alert khi:
- **> 10 failed attempts** từ cùng IP trong 5 phút
- **> 50 failed attempts** tổng cộng trong 10 phút
- **> 5 IPs bị block** cùng lúc

### 5.3 Security Stats Dashboard

Sử dụng endpoint `/admin/security-stats` để:
- Hiển thị số IPs đang bị block
- Hiển thị tổng số failed attempts
- Monitor real-time security status

---

## 6. Production Recommendations

### 6.1 Use Redis for Storage

**Hiện tại**: In-memory storage (mất khi restart server)

**Production**: Nên dùng Redis để:
- Persist blocked IPs across server restarts
- Share blocked IPs giữa multiple server instances
- Better performance và scalability

**Implementation**:
```python
# Thay đổi storage trong admin_security.py
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

### 6.2 IP Whitelist (Optional)

Cho phép whitelist một số IPs (ví dụ: office IP) để:
- Không bị block khi test
- Faster access từ trusted locations

### 6.3 2FA for Admin (Future)

Thêm 2FA (Two-Factor Authentication) cho admin operations:
- Admin key + OTP code
- Hoặc Admin key + Biometric
- Tăng cường bảo mật đáng kể

### 6.4 Honeypot Endpoints

Tạo fake admin endpoints để:
- Detect reconnaissance attacks
- Log attacker behavior
- Waste attacker time

---

## 7. Checklist Bảo mật

Sau khi triển khai, đảm bảo:

- [x] **IP Blocking**: Sau 5 failed attempts → block 5 phút
- [x] **Exponential Backoff**: Delay tăng dần khi failed
- [x] **Rate Limiting**: Giới hạn requests per minute
- [x] **Logging**: Log tất cả failed attempts
- [x] **Security Stats**: Endpoint để monitor
- [ ] **Redis Storage**: (Optional, cho production)
- [ ] **IP Whitelist**: (Optional, cho trusted IPs)
- [ ] **2FA**: (Future enhancement)
- [ ] **Monitoring Alerts**: Setup alerts cho failed attempts

---

## 8. Kết luận

Với các biện pháp trên, hệ thống đã được bảo vệ chống brute force attack:

✅ **IP Blocking**: Ngăn chặn attacker sau nhiều failed attempts  
✅ **Exponential Backoff**: Làm chậm brute force  
✅ **Rate Limiting**: Giới hạn số requests  
✅ **Logging**: Monitor và alert  
✅ **Security Stats**: Real-time monitoring  

**Lưu ý quan trọng**: 
- Admin secret key phải **đủ dài và phức tạp** (>= 32 ký tự)
- Không commit admin key vào Git
- Monitor logs thường xuyên
- Consider thêm 2FA cho production
