"""
User Repository - Database queries for user operations
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import pymysql

from services.user.models import Subscription, User

logger = logging.getLogger(__name__)


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


def create_user(email: str, password_hash: str, full_name: str, verification_token: Optional[str] = None, verification_expires: Optional[datetime] = None) -> int:
    """Tạo user mới trong database. Returns user_id."""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, full_name, status, 
                                    email_verified, verification_token, verification_token_expires)
                    VALUES (%s, %s, %s, 'active', FALSE, %s, %s)
                    """,
                    (email, password_hash, full_name, verification_token, verification_expires),
                )
            except Exception as e:
                # Columns don't exist yet, insert without email_verified columns
                logger.warning(f"Email verification columns not found, inserting without them: {str(e)}")
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, full_name, status)
                    VALUES (%s, %s, %s, 'active')
                    """,
                    (email, password_hash, full_name),
                )
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Lấy user theo ID"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, email, full_name, status, email_verified, created_at, last_login_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
            except Exception:
                cursor.execute(
                    """
                    SELECT id, email, full_name, status, created_at, last_login_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
            user = cursor.fetchone()
            if not user:
                return None
            # Ensure email_verified is present for backward compatibility
            if "email_verified" not in user:
                user["email_verified"] = False
            user["last_login_at"] = user.get("last_login_at")
            return user
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict]:
    """Lấy user theo email"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, email, full_name, status, email_verified, created_at, last_login_at
                    FROM users
                    WHERE email = %s
                    """,
                    (email,),
                )
            except Exception:
                cursor.execute(
                    """
                    SELECT id, email, full_name, status, created_at, last_login_at
                    FROM users
                    WHERE email = %s
                    """,
                    (email,),
                )
            user = cursor.fetchone()
            if not user:
                return None
            # Ensure email_verified is present for backward compatibility
            if "email_verified" not in user:
                user["email_verified"] = False
            user["last_login_at"] = user.get("last_login_at")
            return user
    finally:
        conn.close()


def get_users_list(page: int = 1, per_page: int = 20, search: Optional[str] = None) -> tuple[list[dict], int]:
    """Lấy danh sách users với pagination"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            offset = (page - 1) * per_page
            
            where_clause = ""
            params = []
            if search:
                where_clause = "WHERE email LIKE %s OR full_name LIKE %s"
                params.append(f"%{search}%")
                params.append(f"%{search}%")

            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM users {where_clause}", tuple(params))
            total_count = cursor.fetchone()["COUNT(*)"]

            # Get users with pagination
            try:
                cursor.execute(
                    f"""
                    SELECT u.id, u.email, u.full_name, u.status, u.email_verified, u.created_at, u.last_login_at,
                           s.tier AS current_tier, s.status AS subscription_status, s.expires_at
                    FROM users u
                    LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
                    {where_clause}
                    ORDER BY u.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    tuple(params + [per_page, offset])
                )
            except Exception:
                try:
                    cursor.execute(
                        f"""
                        SELECT u.id, u.email, u.full_name, u.status, u.created_at, u.last_login_at,
                               s.tier AS current_tier, s.status AS subscription_status, s.expires_at
                        FROM users u
                        LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
                        {where_clause}
                        ORDER BY u.created_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        tuple(params + [per_page, offset])
                    )
                except Exception:
                    cursor.execute(
                        f"""
                        SELECT u.id, u.email, u.full_name, u.status, u.created_at, u.last_login_at,
                               s.tier AS current_tier, s.status AS subscription_status, s.expires_at
                        FROM users u
                        LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
                        {where_clause}
                        LIMIT %s OFFSET %s
                        """,
                        tuple(params + [per_page, offset])
                    )
            
            users = cursor.fetchall()
            
            for user in users:
                if "email_verified" not in user:
                    user["email_verified"] = False
                user["last_login_at"] = user.get("last_login_at")
            
            return users, total_count
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}", exc_info=True)
        return [], 0
    finally:
        conn.close()


def update_user_last_login(user_id: int) -> None:
    """Update last_login_at cho user"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET last_login_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (user_id,),
                )
            except Exception:
                # Column doesn't exist, skip
                pass
            conn.commit()
    finally:
        conn.close()


def delete_user(user_id: int) -> None:
    """Xóa user từ database (CASCADE sẽ xóa related records)"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
    finally:
        conn.close()


def create_subscription(user_id: int, tier: str = "free") -> int:
    """Tạo subscription mới. Returns subscription_id."""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO subscriptions (user_id, tier, status)
                VALUES (%s, %s, 'active')
                """,
                (user_id, tier),
            )
            subscription_id = cursor.lastrowid
            conn.commit()
            return subscription_id
    finally:
        conn.close()


def get_user_subscription(user_id: int) -> Optional[dict]:
    """Lấy subscription hiện tại của user"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT tier, status, expires_at
                    FROM subscriptions
                    WHERE user_id = %s AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (user_id,),
                )
            except Exception:
                cursor.execute(
                    """
                    SELECT tier, status, expires_at
                    FROM subscriptions
                    WHERE user_id = %s AND status = 'active'
                    LIMIT 1
                    """,
                    (user_id,),
                )
            subscription = cursor.fetchone()
            return subscription
    finally:
        conn.close()


def create_password_reset_token(user_id: int, token: str, expires_at: datetime) -> None:
    """Tạo password reset token"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET password_reset_token = %s, password_reset_token_expires = %s
                    WHERE id = %s
                    """,
                    (token, expires_at, user_id),
                )
            except Exception:
                # Try with password_reset_expires (backward compatibility)
                try:
                    cursor.execute(
                        """
                        UPDATE users
                        SET password_reset_token = %s, password_reset_expires = %s
                        WHERE id = %s
                        """,
                        (token, expires_at, user_id),
                    )
                except Exception:
                    # Columns don't exist, skip
                    pass
            conn.commit()
    finally:
        conn.close()


def get_password_reset_token(token: str) -> Optional[dict]:
    """Lấy password reset token"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, email, password_reset_expires
                    FROM users
                    WHERE password_reset_token = %s
                    """,
                    (token,),
                )
            except Exception:
                return None
            return cursor.fetchone()
    finally:
        conn.close()


def update_password(user_id: int, password_hash: str) -> None:
    """Update password cho user"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = %s, password_reset_token = NULL, password_reset_token_expires = NULL
                    WHERE id = %s
                    """,
                    (password_hash, user_id),
                )
            except Exception:
                # Try with password_reset_expires (backward compatibility)
                try:
                    cursor.execute(
                        """
                        UPDATE users
                        SET password_hash = %s, password_reset_token = NULL, password_reset_expires = NULL
                        WHERE id = %s
                        """,
                        (password_hash, user_id),
                    )
                except Exception:
                    # Columns don't exist, just update password
                    cursor.execute(
                        """
                        UPDATE users
                        SET password_hash = %s
                        WHERE id = %s
                        """,
                        (password_hash, user_id),
                    )
            conn.commit()
    finally:
        conn.close()


def get_email_verification_token(token: str) -> Optional[dict]:
    """Lấy email verification token"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, email, verification_token_expires
                    FROM users
                    WHERE verification_token = %s AND email_verified = FALSE
                    """,
                    (token,),
                )
            except Exception:
                return None
            return cursor.fetchone()
    finally:
        conn.close()


def update_email_verified(user_id: int) -> None:
    """Update email_verified = TRUE cho user"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL
                    WHERE id = %s
                    """,
                    (user_id,),
                )
            except Exception:
                # Columns don't exist, skip
                pass
            conn.commit()
    finally:
        conn.close()


def update_verification_token(user_id: int, token: str, expires_at: datetime) -> None:
    """Update verification token cho user"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET verification_token = %s, verification_token_expires = %s
                    WHERE id = %s
                    """,
                    (token, expires_at, user_id),
                )
            except Exception:
                # Columns don't exist, skip
                pass
            conn.commit()
    finally:
        conn.close()


def check_email_exists(email: str) -> bool:
    """Kiểm tra email đã tồn tại chưa"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            return cursor.fetchone() is not None
    finally:
        conn.close()
