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
        return False, f"Lỗi hệ thống: {str(e)}", None, None


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Xác thực user login
    
    Returns:
        (success, error_message, user_data)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Try to query with email_verified first (if column exists)
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
                    return False, "Email hoặc mật khẩu không đúng", None
                
                if user["status"] != "active":
                    return False, "Tài khoản đã bị khóa", None
                
                # Verify password
                if not verify_password(password, user["password_hash"]):
                    return False, "Email hoặc mật khẩu không đúng", None
                
                # Update last_login_at
                cursor.execute(
                    "UPDATE users SET last_login_at = NOW() WHERE id = %s",
                    (user["id"],),
                )
                conn.commit()
                
                return True, None, {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "email_verified": bool(user.get("email_verified", False)),
                }
        finally:
            conn.close()
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}", None


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
                cursor.execute(
                    """
                    SELECT id, email, email_verified, verification_token_expires
                    FROM users
                    WHERE verification_token = %s
                    """,
                    (token,),
                )
                user = cursor.fetchone()
                
                if not user:
                    return False, "Token không hợp lệ hoặc đã hết hạn"
                
                if user["email_verified"]:
                    return False, "Email đã được xác thực rồi"
                
                # Check token expiry
                if user["verification_token_expires"] and user["verification_token_expires"] < datetime.now():
                    return False, "Token đã hết hạn. Vui lòng yêu cầu gửi lại email xác thực"
                
                # Verify email
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
        return False, f"Lỗi hệ thống: {str(e)}"


def generate_new_verification_token(user_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Generate new verification token cho user
    
    Returns:
        (success, error_message, verification_token)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if user exists and not already verified
                cursor.execute(
                    "SELECT id, email_verified FROM users WHERE id = %s",
                    (user_id,),
                )
                user = cursor.fetchone()
                
                if not user:
                    return False, "User không tồn tại", None
                
                if user["email_verified"]:
                    return False, "Email đã được xác thực rồi", None
                
                # Generate new token
                verification_token = generate_verification_token()
                verification_expires = datetime.now() + timedelta(hours=24)
                
                cursor.execute(
                    """
                    UPDATE users 
                    SET verification_token = %s, 
                        verification_token_expires = %s
                    WHERE id = %s
                    """,
                    (verification_token, verification_expires, user_id),
                )
                conn.commit()
                
                return True, None, verification_token
        finally:
            conn.close()
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}", None


def get_user_by_email(email: str) -> Optional[dict]:
    """Lấy thông tin user theo email (cho admin)"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
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
                
                # Get current subscription
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
                subscription = cursor.fetchone()
                
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "status": user["status"],
                    "created_at": user["created_at"],
                    "last_login_at": user["last_login_at"],
                    "current_tier": subscription["tier"] if subscription else None,
                    "subscription_status": subscription["status"] if subscription else None,
                    "expires_at": subscription["expires_at"] if subscription else None,
                }
        finally:
            conn.close()
    except Exception:
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
                try:
                    cursor.execute(
                        """
                        SELECT id, email, full_name, status
                        FROM users
                        WHERE email = %s
                        """,
                        (email,),
                    )
                except Exception:
                    return False, "Lỗi hệ thống", None
                
                user = cursor.fetchone()
                
                # Always return success (security: don't reveal if email exists)
                if not user:
                    return True, None, None
                
                if user["status"] != "active":
                    return True, None, None  # Don't reveal account status
                
                # Generate reset token
                reset_token = generate_password_reset_token()
                reset_expires = datetime.now() + timedelta(hours=1)  # 1 hour expiry
                
                # Update user with reset token
                try:
                    cursor.execute(
                        """
                        UPDATE users 
                        SET password_reset_token = %s, 
                            password_reset_expires = %s
                        WHERE id = %s
                        """,
                        (reset_token, reset_expires, user["id"]),
                    )
                except Exception:
                    # Columns might not exist, return False
                    return False, "Password reset feature chưa được kích hoạt. Vui lòng liên hệ hỗ trợ", None
                
                conn.commit()
                return True, None, reset_token
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}", None


def reset_password(token: str, new_password: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Reset password với token
    
    Returns:
        (success, error_message, user_id)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if token exists and not expired
                try:
                    cursor.execute(
                        """
                        SELECT id, email, password_reset_expires, status
                        FROM users
                        WHERE password_reset_token = %s
                        """,
                        (token,),
                    )
                except Exception:
                    # Columns might not exist
                    return False, "Password reset feature chưa được kích hoạt. Vui lòng liên hệ hỗ trợ", None
                
                user = cursor.fetchone()
                
                if not user:
                    return False, "Token không hợp lệ hoặc đã hết hạn", None
                
                if user["status"] != "active":
                    return False, "Tài khoản đã bị khóa", None
                
                # Check token expiry
                if user["password_reset_expires"] and user["password_reset_expires"] < datetime.now():
                    return False, "Token đã hết hạn. Vui lòng yêu cầu lại", None
                
                # Hash new password
                password_hash = hash_password(new_password)
                
                # Update password and clear reset token
                cursor.execute(
                    """
                    UPDATE users 
                    SET password_hash = %s, 
                        password_reset_token = NULL,
                        password_reset_expires = NULL
                    WHERE id = %s
                    """,
                    (password_hash, user["id"]),
                )
                conn.commit()
                
                return True, None, user["id"]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống: {str(e)}", None


def invalidate_user_sessions(user_id: int) -> bool:
    """
    Invalidate all sessions cho user (sau khi reset password)
    Note: Flask sessions are stored client-side, so we can't directly invalidate them
    This function is a placeholder for future implementation (e.g., storing session IDs in DB)
    
    Returns:
        success
    """
    # TODO: Implement session management if needed
    # For now, sessions will be invalidated when user tries to use them (password check fails)
    logger.info(f"Password reset for user {user_id} - sessions should be invalidated on next login attempt")
    return True


def get_user_subscription(user_id: int) -> Optional[dict]:
    """Lấy subscription hiện tại của user"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, tier, status, started_at, expires_at, payment_method, amount, currency
                    FROM subscriptions
                    WHERE user_id = %s AND status = 'active'
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (user_id,),
                )
                return cursor.fetchone()
        finally:
            conn.close()
    except Exception:
        return None
