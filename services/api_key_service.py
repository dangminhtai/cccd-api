"""
API Key Service - Quản lý API key với MySQL và SHA256 hash
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pymysql

TierType = Literal["free", "premium", "ultra"]

# Rate limits per tier (requests per minute)
TIER_RATE_LIMITS = {
    "free": "10 per minute",
    "premium": "100 per minute",
    "ultra": "1000 per minute",
}


@dataclass
class APIKeyInfo:
    id: int
    key_prefix: str
    tier: TierType
    owner_email: str
    active: bool
    expired: bool
    rate_limit: str


def _get_db_connection():
    """Tạo connection MySQL từ environment variables"""
    import os
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def _hash_key(api_key: str) -> str:
    """Hash API key bằng SHA256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(tier: TierType) -> str:
    """
    Tạo API key mới với prefix theo tier
    Format: {tier_prefix}_{random_32_chars}
    """
    prefix_map = {"free": "free", "premium": "prem", "ultra": "ultr"}
    prefix = prefix_map.get(tier, "unkn")
    random_part = secrets.token_hex(16)  # 32 hex chars
    return f"{prefix}_{random_part}"


def create_api_key(
    tier: TierType,
    owner_email: str,
    days_valid: int | None = None,
) -> str:
    """
    Tạo và lưu API key mới vào database
    Returns: API key plaintext (chỉ hiển thị 1 lần)
    """
    api_key = generate_api_key(tier)
    key_hash = _hash_key(api_key)
    key_prefix = api_key[:12]  # e.g., "free_abc123de"
    
    expires_at = None
    if days_valid:
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(days=days_valid)
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO api_keys (key_hash, key_prefix, tier, owner_email, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (key_hash, key_prefix, tier, owner_email, expires_at),
            )
        conn.commit()
    finally:
        conn.close()
    
    return api_key


def get_key_info(api_key: str) -> APIKeyInfo | None:
    """
    Tra cứu thông tin key từ database
    Returns: APIKeyInfo hoặc None nếu không tìm thấy
    """
    key_hash = _hash_key(api_key)
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, key_prefix, tier, owner_email, active, expires_at
                FROM api_keys
                WHERE key_hash = %s
                """,
                (key_hash,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    
    if not row:
        return None
    
    # Check expired
    expired = False
    if row["expires_at"]:
        expired = datetime.now() > row["expires_at"]
    
    return APIKeyInfo(
        id=row["id"],
        key_prefix=row["key_prefix"],
        tier=row["tier"],
        owner_email=row["owner_email"],
        active=row["active"],
        expired=expired,
        rate_limit=TIER_RATE_LIMITS.get(row["tier"], "10 per minute"),
    )


def validate_api_key(api_key: str) -> tuple[bool, str, APIKeyInfo | None]:
    """
    Validate API key
    Returns: (is_valid, error_message, key_info)
    """
    if not api_key:
        return False, "API key không được để trống.", None
    
    info = get_key_info(api_key)
    
    if info is None:
        return False, "API key không hợp lệ.", None
    
    if not info.active:
        return False, "API key đã bị vô hiệu hóa.", None
    
    if info.expired:
        return False, "API key đã hết hạn.", None
    
    return True, "", info


def get_rate_limit_for_key(api_key: str) -> str:
    """Lấy rate limit string cho key (dùng với Flask-Limiter)"""
    info = get_key_info(api_key)
    if info and info.active and not info.expired:
        return info.rate_limit
    return "10 per minute"  # Default cho invalid key


def deactivate_key(api_key: str) -> bool:
    """Vô hiệu hóa key"""
    key_hash = _hash_key(api_key)
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE api_keys SET active = FALSE WHERE key_hash = %s",
                (key_hash,),
            )
            affected = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    
    return affected > 0


def log_request(api_key: str):
    """Ghi nhận 1 request cho tracking usage"""
    info = get_key_info(api_key)
    if not info:
        return
    
    today = datetime.now().date()
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO api_usage (key_id, request_date, request_count)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE request_count = request_count + 1
                """,
                (info.id, today),
            )
        conn.commit()
    finally:
        conn.close()


def get_usage_stats(api_key: str, days: int = 30) -> dict:
    """Lấy thống kê usage trong N ngày gần nhất"""
    info = get_key_info(api_key)
    if not info:
        return {"error": "Key not found"}
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT request_date, request_count
                FROM api_usage
                WHERE key_id = %s
                AND request_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY request_date DESC
                """,
                (info.id, days),
            )
            rows = cursor.fetchall()
            
            cursor.execute(
                """
                SELECT SUM(request_count) as total
                FROM api_usage
                WHERE key_id = %s
                AND request_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                """,
                (info.id, days),
            )
            total_row = cursor.fetchone()
    finally:
        conn.close()
    
    return {
        "key_prefix": info.key_prefix,
        "tier": info.tier,
        "total_requests": total_row["total"] or 0,
        "daily": [{"date": str(r["request_date"]), "count": r["request_count"]} for r in rows],
    }

