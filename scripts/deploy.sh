#!/bin/bash
# Deployment script cho CCCD API
# Usage: ./scripts/deploy.sh [production|staging]

set -e

ENV=${1:-production}
echo "🚀 Deploying CCCD API to $ENV environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please copy env.example to .env and configure it."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests (optional, uncomment if needed)
# echo "🧪 Running tests..."
# python -m pytest tests/ -v

# Start with gunicorn
echo "✅ Starting server with gunicorn..."
gunicorn -w 4 -b 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    wsgi:app
