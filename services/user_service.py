"""
User Service - Quản lý users, authentication, registration
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

import bcrypt
import pymysql

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


def hash_password(password: str) -> str:
    """Hash password bằng bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password với hash"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)


def register_user(email: str, password: str, full_name: str) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
    """
    Đăng ký user mới
    
    Returns:
        (success, error_message, user_id, verification_token)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, "Email đã được sử dụng", None, None
                
                # Hash password
                password_hash = hash_password(password)
                
                # Generate verification token
                verification_token = generate_verification_token()
                verification_expires = datetime.now() + timedelta(hours=24)
                
                # Insert user - try with email_verified columns first, fallback if columns don't exist
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
                    # Set verification_token to None to indicate columns don't exist
                    verification_token = None
                user_id = cursor.lastrowid
                
                # Create default free subscription
                cursor.execute(
                    """
                    INSERT INTO subscriptions (user_id, tier, status)
                    VALUES (%s, 'free', 'active')
                    """,
                    (user_id,),
                )
            conn.commit()
            return True, None, user_id, verification_token
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}", None, None


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Xác thực user login
    
    Returns:
        (success, user_dict, error_message)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Try with email_verified first, fallback if column doesn't exist
                try:
                    cursor.execute(
                        """
                        SELECT id, email, password_hash, full_name, status, email_verified
                        FROM users
                        WHERE email = %s
                        """,
                        (email,),
                    )
                except Exception:
                    # Column doesn't exist, query without email_verified
                    cursor.execute(
                        """
                        SELECT id, email, password_hash, full_name, status
                        FROM users
                        WHERE email = %s
                        """,
                        (email,),
                    )
                user = cursor.fetchone()
                
                if not user:
                    return False, None, "Email hoặc mật khẩu không đúng"
                
                if user["status"] != "active":
                    return False, None, "Tài khoản đã bị khóa"
                
                # Verify password
                if not verify_password(password, user["password_hash"]):
                    return False, None, "Email hoặc mật khẩu không đúng"
                
                # Update last_login_at if column exists
                try:
                    cursor.execute(
                        """
                        UPDATE users
                        SET last_login_at = NOW()
                        WHERE id = %s
                        """,
                        (user["id"],),
                    )
                except Exception:
                    # Column doesn't exist, skip update
                    pass
                
                conn.commit()
                
                # Return user info (without password_hash)
                user_dict = {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "status": user["status"],
                }
                if "email_verified" in user:
                    user_dict["email_verified"] = user["email_verified"]
                
                return True, user_dict, None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}", exc_info=True)
        return False, None, f"Lỗi hệ thống: {str(e)}"


def get_users_list(page: int = 1, per_page: int = 20, search: Optional[str] = None) -> tuple[list[dict], int]:
    """
    Lấy danh sách users với pagination (cho admin)
    Returns: (users_list, total_count)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Build WHERE clause for search
                where_clause = ""
                params = []
                if search:
                    where_clause = "WHERE email LIKE %s OR full_name LIKE %s"
                    search_pattern = f"%{search}%"
                    params = [search_pattern, search_pattern]
                
                # Get total count
                count_query = f"SELECT COUNT(*) as total FROM users {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()["total"]
                
                # Get users with pagination
                offset = (page - 1) * per_page
                users_query = f"""
                    SELECT id, email, full_name, status, created_at, last_login_at
                    FROM users
                    {where_clause}
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(users_query, params + [per_page, offset])
                users = cursor.fetchall()
                
                # Get subscriptions for each user
                user_ids = [user["id"] for user in users]
                if user_ids:
                    placeholders = ",".join(["%s"] * len(user_ids))
                    try:
                        cursor.execute(
                            f"""
                            SELECT user_id, tier, status, expires_at
                            FROM subscriptions
                            WHERE user_id IN ({placeholders}) AND status = 'active'
                            ORDER BY created_at DESC
                            """,
                            user_ids,
                        )
                    except Exception:
                        # Column created_at doesn't exist
                        cursor.execute(
                            f"""
                            SELECT user_id, tier, status, expires_at
                            FROM subscriptions
                            WHERE user_id IN ({placeholders}) AND status = 'active'
                            """,
                            user_ids,
                        )
                    subscriptions = {sub["user_id"]: sub for sub in cursor.fetchall()}
                else:
                    subscriptions = {}
                
                # Combine user data with subscription
                result = []
                for user in users:
                    user_id = user["id"]
                    subscription = subscriptions.get(user_id)
                    result.append({
                        "id": user["id"],
                        "email": user["email"],
                        "full_name": user.get("full_name"),
                        "status": user["status"],
                        "created_at": user.get("created_at"),
                        "last_login_at": user.get("last_login_at"),
                        "current_tier": subscription["tier"] if subscription else None,
                        "subscription_status": subscription["status"] if subscription else None,
                        "expires_at": subscription["expires_at"] if subscription else None,
                    })
                
                return result, total_count
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}", exc_info=True)
        return [], 0


def get_user_by_email(email: str) -> Optional[dict]:
    """Lấy thông tin user theo email (cho admin)"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Try with email_verified first, fallback if column doesn't exist
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
                    # Column doesn't exist, query without email_verified
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
                
                # Get current subscription (try with created_at, fallback without)
                try:
                    cursor.execute(
                        """
                        SELECT tier, status, expires_at
                        FROM subscriptions
                        WHERE user_id = %s AND status = 'active'
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (user["id"],),
                    )
                except Exception:
                    # Column created_at doesn't exist, query without ORDER BY
                    cursor.execute(
                        """
                        SELECT tier, status, expires_at
                        FROM subscriptions
                        WHERE user_id = %s AND status = 'active'
                        LIMIT 1
                        """,
                        (user["id"],),
                    )
                subscription = cursor.fetchone()
                
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "status": user["status"],
                    "created_at": user["created_at"],
                    "last_login_at": user.get("last_login_at"),
                    "current_tier": subscription["tier"] if subscription else None,
                    "subscription_status": subscription["status"] if subscription else None,
                    "expires_at": subscription["expires_at"] if subscription else None,
                }
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting user by email: {str(e)}", exc_info=True)
        return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Lấy thông tin user theo ID"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if email_verified column exists first
                # If not, query without it (backward compatibility)
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
                    # Column doesn't exist, query without email_verified
                    cursor.execute(
                        """
                        SELECT id, email, full_name, status, created_at, last_login_at
                        FROM users
                        WHERE id = %s
                        """,
                        (user_id,),
                    )
                    user = cursor.fetchone()
                    if user:
                        user["email_verified"] = False  # Default to False if column doesn't exist
                    return user
                return cursor.fetchone()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting user by id: {str(e)}", exc_info=True)
        return None


def delete_user(user_id: int) -> tuple[bool, Optional[str]]:
    """
    Xóa user (hard delete) - chỉ dùng cho admin
    Returns: (success, error_message)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check user exists
                cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user:
                    return False, "User không tồn tại"
                
                # Delete user (CASCADE will handle related records)
                # Note: Foreign keys should be set to CASCADE or SET NULL
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                
            conn.commit()
            return True, f"Đã xóa user {user['email']} thành công"
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        return False, f"Lỗi khi xóa user: {str(e)}"


def generate_password_reset_token() -> str:
    """Generate secure password reset token"""
    return secrets.token_urlsafe(32)


def request_password_reset(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Request password reset cho user
    
    Returns:
        (success, error_message, reset_token)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user:
                    return False, "Email không tồn tại", None
                
                # Check if password_reset columns exist
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users'
                    AND COLUMN_NAME = 'password_reset_token'
                    """
                )
                has_reset_columns = cursor.fetchone() is not None
                
                if not has_reset_columns:
                    return False, "Password reset feature chưa được kích hoạt. Vui lòng liên hệ hỗ trợ", None
                
                # Generate reset token
                reset_token = generate_password_reset_token()
                reset_expires = datetime.now() + timedelta(hours=1)
                
                # Update user with reset token
                cursor.execute(
                    """
                    UPDATE users
                    SET password_reset_token = %s,
                        password_reset_token_expires = %s
                    WHERE id = %s
                    """,
                    (reset_token, reset_expires, user["id"]),
                )
            conn.commit()
            return True, None, reset_token
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}", None


def reset_password(token: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Reset password với token
    
    Returns:
        (success, error_message)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if password_reset columns exist
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users'
                    AND COLUMN_NAME = 'password_reset_token'
                    """
                )
                has_reset_columns = cursor.fetchone() is not None
                
                if not has_reset_columns:
                    return False, "Password reset feature chưa được kích hoạt. Vui lòng liên hệ hỗ trợ"
                
                # Find user with valid token
                cursor.execute(
                    """
                    SELECT id, email
                    FROM users
                    WHERE password_reset_token = %s
                    AND password_reset_token_expires > NOW()
                    """,
                    (token,),
                )
                user = cursor.fetchone()
                
                if not user:
                    return False, "Token không hợp lệ hoặc đã hết hạn"
                
                # Hash new password
                password_hash = hash_password(new_password)
                
                # Update password and clear reset token
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = %s,
                        password_reset_token = NULL,
                        password_reset_token_expires = NULL
                    WHERE id = %s
                    """,
                    (password_hash, user["id"]),
                )
            conn.commit()
            return True, None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}"


def verify_email(token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify email với token
    
    Returns:
        (success, error_message)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if email_verified columns exist
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users'
                    AND COLUMN_NAME = 'email_verified'
                    """
                )
                has_email_columns = cursor.fetchone() is not None
                
                if not has_email_columns:
                    return False, "Email verification feature chưa được kích hoạt"
                
                # Find user with valid token
                cursor.execute(
                    """
                    SELECT id, email
                    FROM users
                    WHERE verification_token = %s
                    AND verification_token_expires > NOW()
                    """,
                    (token,),
                )
                user = cursor.fetchone()
                
                if not user:
                    return False, "Token không hợp lệ hoặc đã hết hạn"
                
                # Update email_verified
                cursor.execute(
                    """
                    UPDATE users
                    SET email_verified = TRUE,
                        verification_token = NULL,
                        verification_token_expires = NULL
                    WHERE id = %s
                    """,
                    (user["id"],),
                )
            conn.commit()
            return True, None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}"


def resend_verification_email(user_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Resend verification email cho user
    
    Returns:
        (success, error_message, verification_token)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if email_verified columns exist
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users'
                    AND COLUMN_NAME = 'email_verified'
                    """
                )
                has_email_columns = cursor.fetchone() is not None
                
                if not has_email_columns:
                    return False, "Email verification feature chưa được kích hoạt", None
                
                # Get user info
                cursor.execute(
                    """
                    SELECT id, email, email_verified
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                user = cursor.fetchone()
                
                if not user:
                    return False, "User không tồn tại", None
                
                if user["email_verified"]:
                    return False, "Email đã được verify rồi", None
                
                # Generate new token
                verification_token = generate_verification_token()
                verification_expires = datetime.now() + timedelta(hours=24)
                
                # Update user with new token
                cursor.execute(
                    """
                    UPDATE users
                    SET verification_token = %s,
                        verification_token_expires = %s
                    WHERE id = %s
                    """,
                    (verification_token, verification_expires, user["id"]),
                )
            conn.commit()
            return True, None, verification_token
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}", None


def get_user_subscription(user_id: int) -> Optional[dict]:
    """Lấy subscription hiện tại của user"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(
                        """
                        SELECT tier, status, expires_at, created_at
                        FROM subscriptions
                        WHERE user_id = %s AND status = 'active'
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (user_id,),
                    )
                except Exception:
                    # Column created_at doesn't exist
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
    except Exception as e:
        logger.error(f"Error getting user subscription: {str(e)}", exc_info=True)
        return None
