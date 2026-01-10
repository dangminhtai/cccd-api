"""
User Service - Quản lý users, authentication, registration
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

import bcrypt
import pymysql


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
                
                # Insert user
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, full_name, status, 
                                    email_verified, verification_token, verification_token_expires)
                    VALUES (%s, %s, %s, 'active', FALSE, %s, %s)
                    """,
                    (email, password_hash, full_name, verification_token, verification_expires),
                )
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
                cursor.execute(
                    """
                    SELECT id, email, password_hash, full_name, status, email_verified
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


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Lấy thông tin user theo ID"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, full_name, status, email_verified, created_at, last_login_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                return cursor.fetchone()
        finally:
            conn.close()
    except Exception:
        return None


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
