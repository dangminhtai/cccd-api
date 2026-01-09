"""
User Service - Quản lý users, authentication, registration
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
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


def register_user(email: str, password: str, full_name: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Đăng ký user mới
    
    Returns:
        (success, error_message, user_id)
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, "Email đã được sử dụng", None
                
                # Hash password
                password_hash = hash_password(password)
                
                # Insert user
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, full_name, status)
                    VALUES (%s, %s, %s, 'active')
                    """,
                    (email, password_hash, full_name),
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
                return True, None, user_id
        finally:
            conn.close()
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}", None


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
                
                # Return user data (without password_hash)
                user_data = {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "status": user["status"],
                }
                
                return True, None, user_data
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
                    SELECT id, email, full_name, status, created_at, last_login_at
                    FROM users
                    WHERE id = %s AND status = 'active'
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
                    SELECT id, tier, status, started_at, expires_at
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
