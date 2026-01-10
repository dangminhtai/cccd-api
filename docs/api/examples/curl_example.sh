#!/bin/bash

# CCCD API - cURL Examples
# ========================
# Example commands để gọi CCCD API sử dụng cURL

API_BASE_URL="http://127.0.0.1:8000"
API_KEY="your-api-key-here"  # Thay bằng API key của bạn

echo "=== Health Check ==="
curl -X GET "${API_BASE_URL}/health" \
  -H "Content-Type: application/json"

echo -e "\n\n=== Parse CCCD - Basic ==="
curl -X POST "${API_BASE_URL}/v1/cccd/parse" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "cccd": "079203012345"
  }'

echo -e "\n\n=== Parse CCCD - With province_version ==="
curl -X POST "${API_BASE_URL}/v1/cccd/parse" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "cccd": "079203012345",
    "province_version": "legacy_63"
  }'

echo -e "\n\n=== Error Handling - Invalid CCCD ==="
curl -X POST "${API_BASE_URL}/v1/cccd/parse" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "cccd": "invalid"
  }'

echo -e "\n\n=== Error Handling - Missing API Key ==="
curl -X POST "${API_BASE_URL}/v1/cccd/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "cccd": "079203012345"
  }'

echo -e "\n"
