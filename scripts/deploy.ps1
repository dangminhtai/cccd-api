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

# Start with gunicorn
Write-Host "✅ Starting server with gunicorn..." -ForegroundColor Green
gunicorn -w 4 -b 0.0.0.0:8000 `
    --access-logfile - `
    --error-logfile - `
    --log-level info `
    --timeout 120 `
    --graceful-timeout 30 `
    --keep-alive 5 `
    wsgi:app
