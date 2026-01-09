# Deployment script cho CCCD API (PowerShell)
# Usage: .\scripts\deploy.ps1 [production|staging]

param(
    [string]$Environment = "production"
)

Write-Host "🚀 Deploying CCCD API to $Environment environment..." -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "   Please copy env.example to .env and configure it." -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Run tests (optional, uncomment if needed)
# Write-Host "🧪 Running tests..." -ForegroundColor Cyan
# python -m pytest tests/ -v

# Start with Waitress (Windows production server)
# Note: Gunicorn không chạy được trên Windows (thiếu module fcntl)
# Xem issue #24 trong docs/project/issues_list.md
Write-Host "✅ Starting server with Waitress..." -ForegroundColor Green
Write-Host "   (Gunicorn không chạy trên Windows, dùng Waitress thay thế)" -ForegroundColor Yellow

# Install waitress if not already installed
pip install waitress

# Run with Waitress
# Waitress là WSGI server tốt cho Windows, tương đương Gunicorn trên Linux
Write-Host ""
Write-Host "🚀 Server đang chạy tại: http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "📝 Để test, mở terminal khác và chạy:" -ForegroundColor Cyan
Write-Host "   Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health'" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏹️  Nhấn Ctrl+C để dừng server" -ForegroundColor Gray
Write-Host ""

# Run Waitress (sẽ chạy mãi cho đến khi Ctrl+C)
waitress-serve --host=0.0.0.0 --port=8000 wsgi:app
