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
    user_id: int | None = None,
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
                INSERT INTO api_keys (key_hash, key_prefix, tier, owner_email, expires_at, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (key_hash, key_prefix, tier, owner_email, expires_at, user_id),
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


def deactivate_key_by_id(key_id: int, user_id: int) -> bool:
    """Vô hiệu hóa key theo ID (chỉ user sở hữu mới được) - DEPRECATED: dùng delete_key_by_id thay thế"""
    return delete_key_by_id(key_id, user_id)


def delete_key_by_id(key_id: int, user_id: int) -> bool:
    """Xóa key khỏi database (hard delete) - chỉ user sở hữu mới được
    
    Lưu ý: Xóa key sẽ cascade xóa:
    - api_key_history (ON DELETE CASCADE)
    - api_usage (ON DELETE CASCADE)
    - request_logs.api_key_id sẽ SET NULL (ON DELETE SET NULL)
    
    Returns:
        True nếu xóa thành công, False nếu không tìm thấy hoặc không có quyền
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # First verify ownership
            cursor.execute(
                "SELECT id FROM api_keys WHERE id = %s AND user_id = %s",
                (key_id, user_id),
            )
            key_row = cursor.fetchone()
            if key_row is None:
                return False  # Key không tồn tại hoặc không thuộc về user
            
            # Log deletion before deleting
            _log_key_history(key_id, "deleted", "exists", "deleted", user_id)
            
            # Hard delete - DELETE row khỏi database
            # Foreign key constraints sẽ tự động:
            # - DELETE api_key_history (CASCADE)
            # - DELETE api_usage (CASCADE)
            # - SET NULL request_logs.api_key_id (SET NULL)
            cursor.execute(
                "DELETE FROM api_keys WHERE id = %s AND user_id = %s",
                (key_id, user_id),
            )
            affected = cursor.rowcount
            
        conn.commit()
    finally:
        conn.close()
    
    return affected > 0


def get_user_api_keys(user_id: int) -> list[dict]:
    """Lấy danh sách API keys của user"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if new columns exist
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'api_keys'
                AND COLUMN_NAME IN ('label', 'rotated_from', 'suspended_at')
                """
            )
            available_columns = {row["COLUMN_NAME"] for row in cursor.fetchall()}
            
            # Build SELECT query based on available columns
            base_columns = "id, key_prefix, tier, owner_email, active, created_at, expires_at"
            if "label" in available_columns:
                base_columns += ", label"
            if "rotated_from" in available_columns:
                base_columns += ", rotated_from"
            if "suspended_at" in available_columns:
                base_columns += ", suspended_at"
            
            cursor.execute(
                f"""
                SELECT {base_columns}
                FROM api_keys
                WHERE user_id = %s
                AND active = TRUE
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
    finally:
        conn.close()
    
    result = []
    for row in rows:
        expired = False
        if row["expires_at"]:
            expired = datetime.now() > row["expires_at"]
        
        key_data = {
            "id": row["id"],
            "key_prefix": row["key_prefix"],
            "tier": row["tier"],
            "owner_email": row["owner_email"],
            "active": row["active"],
            "expired": expired,
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
        }
        
        # Add optional columns if they exist
        if "label" in row:
            key_data["label"] = row["label"]
        if "rotated_from" in row:
            key_data["rotated_from"] = row["rotated_from"]
        if "suspended_at" in row:
            key_data["suspended_at"] = row["suspended_at"]
            key_data["suspended"] = row["suspended_at"] is not None
        
        result.append(key_data)
    
    return result


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


def _log_key_history(key_id: int, action: str, old_value: str | None = None, new_value: str | None = None, performed_by: int | None = None):
    """Ghi lại lịch sử thay đổi của key"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if table exists
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_key_history'
                    """
                )
                if cursor.fetchone()["COUNT(*)"] == 0:
                    return  # Table doesn't exist yet
                
                cursor.execute(
                    """
                    INSERT INTO api_key_history (key_id, action, old_value, new_value, performed_by)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (key_id, action, old_value, new_value, performed_by),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass  # Silently fail if history logging fails


def rotate_key(key_id: int, user_id: int, grace_period_days: int = 7) -> tuple[bool, str | None, str | None]:
    """
    Rotate API key: tạo key mới, set expiry cho key cũ (grace period), link key mới với key cũ
    
    Returns: (success, error_message, new_api_key_plaintext)
    """
    from datetime import timedelta
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get old key info
            cursor.execute(
                """
                SELECT id, tier, owner_email, user_id, label
                FROM api_keys
                WHERE id = %s AND user_id = %s AND active = TRUE
                """,
                (key_id, user_id),
            )
            old_key = cursor.fetchone()
            
            if not old_key:
                return False, "Key không tồn tại hoặc không thuộc về bạn", None
            
            # Check if rotated_from column exists
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'api_keys'
                AND COLUMN_NAME = 'rotated_from'
                """
            )
            has_rotated_from = cursor.fetchone() is not None
            
            # Create new key
            new_key = generate_api_key(old_key["tier"])
            new_key_hash = _hash_key(new_key)
            new_key_prefix = new_key[:12]
            
            # Get expires_at from old key (if it has expiry, new key inherits it)
            cursor.execute(
                """
                SELECT expires_at FROM api_keys WHERE id = %s
                """,
                (key_id,),
            )
            old_expires = cursor.fetchone()["expires_at"]
            
            # Insert new key
            cursor.execute(
                """
                INSERT INTO api_keys (key_hash, key_prefix, tier, owner_email, expires_at, user_id, label, rotated_from)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    new_key_hash,
                    new_key_prefix,
                    old_key["tier"],
                    old_key["owner_email"],
                    old_expires,  # New key inherits expiry from old key
                    old_key["user_id"],
                    old_key.get("label"),  # Inherit label
                    key_id if has_rotated_from else None,  # Link to old key
                ),
            )
            new_key_id = cursor.lastrowid
            
            # Set expiry for old key (grace period)
            grace_expiry = datetime.now() + timedelta(days=grace_period_days)
            cursor.execute(
                """
                UPDATE api_keys
                SET expires_at = %s, active = FALSE
                WHERE id = %s
                """,
                (grace_expiry, key_id),
            )
            
            # Log history
            _log_key_history(key_id, "rotated", f"Key ID {key_id}", f"Rotated to Key ID {new_key_id}", user_id)
            _log_key_history(new_key_id, "created", None, f"Rotated from Key ID {key_id}", user_id)
            
        conn.commit()
        return True, None, new_key
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi khi rotate key: {str(e)}", None
    finally:
        conn.close()


def suspend_key(key_id: int, user_id: int) -> tuple[bool, str | None]:
    """Suspend key (tạm dừng, không xóa)"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check ownership
            cursor.execute(
                """
                SELECT id, active, suspended_at
                FROM api_keys
                WHERE id = %s AND user_id = %s
                """,
                (key_id, user_id),
            )
            key = cursor.fetchone()
            
            if not key:
                return False, "Key không tồn tại hoặc không thuộc về bạn"
            
            if key["suspended_at"]:
                return False, "Key đã bị suspend rồi"
            
            # Check if suspended_at column exists
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'api_keys'
                AND COLUMN_NAME = 'suspended_at'
                """
            )
            has_suspended_at = cursor.fetchone() is not None
            
            if has_suspended_at:
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET active = FALSE, suspended_at = NOW()
                    WHERE id = %s
                    """,
                    (key_id,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET active = FALSE
                    WHERE id = %s
                    """,
                    (key_id,),
                )
            
            _log_key_history(key_id, "suspended", "active", "suspended", user_id)
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi khi suspend key: {str(e)}"
    finally:
        conn.close()


def resume_key(key_id: int, user_id: int) -> tuple[bool, str | None]:
    """Resume key (kích hoạt lại)"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check ownership
            cursor.execute(
                """
                SELECT id, expires_at, suspended_at
                FROM api_keys
                WHERE id = %s AND user_id = %s
                """,
                (key_id, user_id),
            )
            key = cursor.fetchone()
            
            if not key:
                return False, "Key không tồn tại hoặc không thuộc về bạn"
            
            # Check if expired
            if key["expires_at"] and datetime.now() > key["expires_at"]:
                return False, "Key đã hết hạn, không thể resume"
            
            # Check if suspended_at column exists
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'api_keys'
                AND COLUMN_NAME = 'suspended_at'
                """
            )
            has_suspended_at = cursor.fetchone() is not None
            
            if has_suspended_at:
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET active = TRUE, suspended_at = NULL
                    WHERE id = %s
                    """,
                    (key_id,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET active = TRUE
                    WHERE id = %s
                    """,
                    (key_id,),
                )
            
            _log_key_history(key_id, "resumed", "suspended", "active", user_id)
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi khi resume key: {str(e)}"
    finally:
        conn.close()


def update_key_label(key_id: int, user_id: int, label: str | None) -> tuple[bool, str | None]:
    """Update label cho key"""
    if label and len(label) > 100:
        return False, "Label không được quá 100 ký tự"
    
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check ownership
            cursor.execute(
                """
                SELECT id, label
                FROM api_keys
                WHERE id = %s AND user_id = %s
                """,
                (key_id, user_id),
            )
            key = cursor.fetchone()
            
            if not key:
                return False, "Key không tồn tại hoặc không thuộc về bạn"
            
            # Check if label column exists
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'api_keys'
                AND COLUMN_NAME = 'label'
                """
            )
            has_label = cursor.fetchone() is not None
            
            if has_label:
                old_label = key.get("label")
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET label = %s
                    WHERE id = %s
                    """,
                    (label, key_id),
                )
                _log_key_history(key_id, "label_updated", old_label, label, user_id)
            else:
                return False, "Label feature chưa được kích hoạt"
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi khi update label: {str(e)}"
    finally:
        conn.close()


def get_key_usage_per_key(key_id: int, user_id: int, days: int = 30) -> dict | None:
    """Lấy usage stats cho một key cụ thể (chỉ user sở hữu mới được)"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify ownership
            cursor.execute(
                """
                SELECT id, key_prefix, tier
                FROM api_keys
                WHERE id = %s AND user_id = %s
                """,
                (key_id, user_id),
            )
            key = cursor.fetchone()
            
            if not key:
                return None
            
            # Get usage from request_logs
            cursor.execute(
                """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error,
                    AVG(response_time_ms) as avg_response_time
                FROM request_logs
                WHERE api_key_id = %s
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                """,
                (key_id, days),
            )
            daily_rows = cursor.fetchall()
            
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success_requests,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_requests,
                    AVG(response_time_ms) as avg_response_time_ms
                FROM request_logs
                WHERE api_key_id = %s
                AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                """,
                (key_id, days),
            )
            total_row = cursor.fetchone()
            
    finally:
        conn.close()
    
    return {
        "key_id": key["id"],
        "key_prefix": key["key_prefix"],
        "tier": key["tier"],
        "total_requests": total_row["total_requests"] or 0,
        "success_requests": total_row["success_requests"] or 0,
        "error_requests": total_row["error_requests"] or 0,
        "avg_response_time_ms": float(total_row["avg_response_time_ms"] or 0),
        "daily_stats": [
            {
                "date": str(row["date"]),
                "count": row["count"],
                "success": row["success"] or 0,
                "error": row["error"] or 0,
                "avg_response_time": float(row["avg_response_time"] or 0),
            }
            for row in daily_rows
        ],
    }

