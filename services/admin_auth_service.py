"""
Admin Authentication Service - Quản lý đăng nhập admin
"""
from __future__ import annotations

import bcrypt
import pymysql
from typing import Dict, Optional, Tuple


def _get_db_connection():
    """Lấy MySQL connection"""
    import os
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def hash_password(password: str) -> str:
    """Hash password bằng bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password với hash"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def authenticate_admin(username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Xác thực admin login
    
    Args:
        username: Username hoặc email
        password: Plain text password
        
    Returns:
        Tuple (success, admin_data, error_message)
        - success: True nếu đăng nhập thành công
        - admin_data: Dict với thông tin admin nếu success
        - error_message: Error message nếu failed
    """
    if not username or not password:
        return False, None, "Username và password không được để trống"
    
    conn = None
    try:
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            # Tìm admin theo username hoặc email
            cursor.execute(
                """
                SELECT id, username, password_hash, email, full_name, is_active
                FROM admin_users
                WHERE (username = %s OR email = %s) AND is_active = TRUE
                LIMIT 1
                """,
                (username, username),
            )
            admin = cursor.fetchone()
            
            if not admin:
                return False, None, "Username hoặc password không đúng"
            
            # Verify password
            if not verify_password(password, admin["password_hash"]):
                return False, None, "Username hoặc password không đúng"
            
            # Update last_login
            cursor.execute(
                "UPDATE admin_users SET last_login = NOW() WHERE id = %s",
                (admin["id"],),
            )
            conn.commit()
            
            # Return admin data (không bao gồm password_hash)
            admin_data = {
                "id": admin["id"],
                "username": admin["username"],
                "email": admin["email"],
                "full_name": admin["full_name"],
            }
            
            return True, admin_data, None
            
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        return False, None, f"Database error: {str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, None, f"Unexpected error: {str(e)}"
    finally:
        if conn:
            conn.close()


def get_admin_by_id(admin_id: int) -> Optional[Dict]:
    """
    Lấy thông tin admin theo ID
    
    Args:
        admin_id: Admin ID
        
    Returns:
        Dict với thông tin admin hoặc None
    """
    conn = None
    try:
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, full_name, is_active, last_login, created_at
                FROM admin_users
                WHERE id = %s AND is_active = TRUE
                LIMIT 1
                """,
                (admin_id,),
            )
            admin = cursor.fetchone()
            return admin
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()


def change_admin_password(admin_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Đổi mật khẩu admin
    
    Args:
        admin_id: Admin ID
        old_password: Mật khẩu cũ
        new_password: Mật khẩu mới
        
    Returns:
        Tuple (success, error_message)
    """
    if not new_password or len(new_password) < 8:
        return False, "Mật khẩu mới phải có ít nhất 8 ký tự"
    
    conn = None
    try:
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            # Lấy password hash hiện tại
            cursor.execute(
                "SELECT password_hash FROM admin_users WHERE id = %s AND is_active = TRUE",
                (admin_id,),
            )
            admin = cursor.fetchone()
            
            if not admin:
                return False, "Admin không tồn tại"
            
            # Verify old password
            if not verify_password(old_password, admin["password_hash"]):
                return False, "Mật khẩu cũ không đúng"
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            cursor.execute(
                "UPDATE admin_users SET password_hash = %s WHERE id = %s",
                (new_password_hash, admin_id),
            )
            conn.commit()
            
            return True, None
            
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error: {str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Unexpected error: {str(e)}"
    finally:
        if conn:
            conn.close()
