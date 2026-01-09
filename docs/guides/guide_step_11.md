# guide_step_11.md — Bước 11: Triển khai (deploy)

## Mục tiêu

Đưa API lên môi trường chạy thật, có kiểm tra sức khoẻ, có theo dõi lỗi cơ bản.

---

## Checklist

### A. Health Check Endpoint

- [x] Đã có endpoint `/health` trả 200 + JSON

**Verify:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
# Kỳ vọng: {"status": "ok"}
```

---

### B. Chọn phương thức deploy

Có 3 options:

#### Option 1: Docker (Khuyến nghị cho development/testing)

- [x] Đã tạo `Dockerfile`
- [x] Đã tạo `docker-compose.yml`
- [x] Đã tạo `.dockerignore`

**Cách deploy:**

```powershell
# Build và chạy
docker-compose up -d

# Xem logs
docker-compose logs -f

# Stop
docker-compose down
```

**⚠️ Troubleshooting:**

Nếu gặp lỗi network khi build Docker (`failed to resolve source metadata` hoặc `EOF`):

**Option 1: Retry với timeout dài hơn**
```powershell
# Set timeout dài hơn
$env:DOCKER_CLIENT_TIMEOUT=300
$env:COMPOSE_HTTP_TIMEOUT=300
docker-compose build --no-cache
docker-compose up -d
```

**Option 2: Pull image từng bước**
```powershell
# Pull base image trước
docker pull python:3.12-slim

# Nếu vẫn lỗi, thử với tag khác
docker pull python:3.11-slim

# Sau đó sửa Dockerfile: FROM python:3.11-slim
```

**Option 3: Dùng Waitress (Windows) hoặc Gunicorn (Linux)**

⚠️ **Lưu ý:** Gunicorn **KHÔNG chạy được trên Windows** (thiếu module `fcntl`).

**Trên Windows:**
```powershell
# Cài waitress (WSGI server cho Windows)
pip install waitress

# Chạy
waitress-serve --host=0.0.0.0 --port=8000 wsgi:app
```

**Trên Linux/Mac:**
```bash
# Cài gunicorn
pip install gunicorn

# Chạy
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

**Option 4: Kiểm tra Docker Desktop settings**
1. Mở Docker Desktop → Settings → Resources → Network
2. Thử disable/enable "Use kernel networking"
3. Restart Docker Desktop

**Option 5: Dùng mirror registry (nếu ở VN)**
Cấu hình Docker daemon để dùng mirror (nếu có):
- Docker Desktop → Settings → Docker Engine
- Thêm registry mirrors (tùy vào provider)

**Verify:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

---

#### Option 2: VM với Gunicorn + Nginx (Production)

- [x] Đã có script `scripts/deploy.sh` và `scripts/deploy.ps1`
- [x] Đã có `nginx.conf.example`

**Cách deploy:**

**Bước 1: Cài đặt trên server**

```bash
# Cài Python và dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip nginx

# Clone repo
git clone https://github.com/dangminhtai/cccd-api.git
cd cccd-api

# Cài dependencies
pip3 install -r requirements.txt
```

**Bước 2: Cấu hình .env**

```bash
cp env.example .env
nano .env  # Sửa các giá trị cần thiết
```

**Bước 3: Chạy với Gunicorn (Linux) hoặc Waitress (Windows)**

⚠️ **Lưu ý:** Gunicorn chỉ chạy trên Linux/Mac, không chạy trên Windows.

**Trên Linux/Mac:**
```bash
# Chạy trực tiếp (test)
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

# Hoặc dùng systemd service (xem phần C)
```

**Trên Windows (development/testing):**
```powershell
# Dùng Waitress thay vì Gunicorn
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 wsgi:app

# Hoặc dùng Flask dev server (chỉ cho testing)
python run.py
```

**Bước 4: Cấu hình Nginx**

```bash
# Copy config
sudo cp nginx.conf.example /etc/nginx/sites-available/cccd-api

# Sửa domain trong config
sudo nano /etc/nginx/sites-available/cccd-api

# Enable site
sudo ln -s /etc/nginx/sites-available/cccd-api /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

#### Option 3: Systemd Service (Tự động restart)

- [x] Đã có template `cccd-api.service.example`

**Cách setup:**

```bash
# Copy service file
sudo cp cccd-api.service.example /etc/systemd/system/cccd-api.service

# Sửa paths trong file (nếu cần)
sudo nano /etc/systemd/system/cccd-api.service

# Enable và start
sudo systemctl daemon-reload
sudo systemctl enable cccd-api
sudo systemctl start cccd-api

# Check status
sudo systemctl status cccd-api

# View logs
sudo journalctl -u cccd-api -f
```

---

### C. Logging & Monitoring

- [x] Gunicorn log ra stdout/stderr (có thể redirect vào file)
- [x] Flask logger đã có request_id để trace
- [x] Error handler không expose stacktrace ra client

**Cấu hình log rotation (Linux):**

```bash
# Tạo logrotate config
sudo nano /etc/logrotate.d/cccd-api

# Nội dung:
/var/log/cccd-api/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload cccd-api > /dev/null 2>&1 || true
    endscript
}
```

**Cấu hình log trong systemd service:**

```ini
[Service]
StandardOutput=append:/var/log/cccd-api/app.log
StandardError=append:/var/log/cccd-api/error.log
```

---

### D. Alerting (Optional)

**Có thể setup với:**

1. **Prometheus + Grafana** (advanced)
2. **Simple script** monitor log files
3. **Cloud monitoring** (AWS CloudWatch, Google Cloud Monitoring, etc.)

**Ví dụ script đơn giản monitor 5xx:**

```bash
#!/bin/bash
# scripts/monitor_errors.sh

LOG_FILE="/var/log/cccd-api/error.log"
THRESHOLD=10  # Số lỗi 5xx trong 5 phút

ERROR_COUNT=$(tail -n 1000 "$LOG_FILE" | grep -c "500\|502\|503\|504" || echo "0")

if [ "$ERROR_COUNT" -gt "$THRESHOLD" ]; then
    echo "ALERT: $ERROR_COUNT errors detected in last 5 minutes!"
    # Gửi email/notification ở đây
fi
```

---

### E. Environment Configuration

**Các biến môi trường cần set:**

| Biến | Mô tả | Ví dụ |
|------|-------|-------|
| `PORT` | Port server chạy | `8000` |
| `FLASK_ENV` | Environment mode | `production` |
| `DEFAULT_PROVINCE_VERSION` | Version mặc định | `current_34` |
| `API_KEY_MODE` | Simple hoặc tiered | `simple` hoặc `tiered` |
| `API_KEY` | API key (nếu simple mode) | `your-secret-key` |
| `MYSQL_HOST` | MySQL host (nếu tiered) | `localhost` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_USER` | MySQL user | `root` |
| `MYSQL_PASSWORD` | MySQL password | `***` |
| `MYSQL_DATABASE` | Database name | `cccd_api` |
| `ADMIN_SECRET` | Admin secret key | `***` |

**Lưu ý bảo mật:**
- ✅ Không commit `.env` vào git (đã có trong `.gitignore`)
- ✅ Dùng secrets management (AWS Secrets Manager, HashiCorp Vault, etc.) cho production
- ✅ Set file permissions: `chmod 600 .env`

---

## Hoàn thành khi

- [x] Health check endpoint `/health` hoạt động
- [x] Có thể deploy bằng Docker hoặc Gunicorn
- [x] Logging được cấu hình
- [ ] (Optional) Có alerting cho 5xx/429
- [ ] API có thể truy cập từ bên ngoài

---

## Tự test (Self-check)

### Test 1: Health Check

```powershell
# Local
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
# Kỳ vọng: {"status": "ok"}

# Từ máy khác (thay <server-ip>)
Invoke-RestMethod -Uri "http://<server-ip>:8000/health"
```

### Test 2: API Endpoint

```powershell
# Test parse CCCD
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cccd/parse" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"cccd": "079203012345"}'
# Kỳ vọng: success: true, province_code: 079
```

### Test 3: Production Server

**Trên Linux/Mac:**
```bash
# Chạy gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

# Test từ terminal khác
curl http://127.0.0.1:8000/health
```

**Trên Windows:**
```powershell
# Chạy waitress (Gunicorn không chạy được trên Windows)
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 wsgi:app

# Test từ terminal khác
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

### Test 4: Docker

```powershell
# Build và chạy
docker-compose up -d

# Check logs
docker-compose logs -f

# Test
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Stop
docker-compose down
```

---

## ✅ DoD (Definition of Done) - Bước 11

| Tiêu chí | Cách verify | ✓ |
|----------|-------------|---|
| Health check hoạt động | `GET /health` → 200 | ✅ |
| Deploy được bằng Docker | `docker-compose up` → API chạy | ✅ |
| Deploy được bằng Gunicorn | `gunicorn wsgi:app` → API chạy | ✅ |
| Logging hoạt động | Xem logs trong terminal/file | ✅ |
| API truy cập được từ ngoài | Test từ máy khác → 200 | |
| (Optional) Alerting setup | Có script/daemon monitor errors | |

---

## 📚 Tài liệu tham khảo

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Flask Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)



