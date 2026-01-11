"""
User Validators - Input validation for user operations
"""
from __future__ import annotations

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format và length
    Returns: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email không được để trống"
    
    email = email.strip()
    
    if len(email) > 255:
        return False, "Email không được vượt quá 255 ký tự"
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Email không hợp lệ"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength và length
    Returns: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password không được để trống"
    
    if len(password) < 8:
        return False, "Password phải có ít nhất 8 ký tự"
    
    if len(password) > 100:
        return False, "Password không được vượt quá 100 ký tự"
    
    return True, ""


def validate_full_name(full_name: str) -> Tuple[bool, str]:
    """
    Validate full name format và length
    Returns: (is_valid, error_message)
    """
    if not full_name or not isinstance(full_name, str):
        return False, "Tên không được để trống"
    
    full_name = full_name.strip()
    
    if len(full_name) < 1:
        return False, "Tên không được để trống"
    
    if len(full_name) > 255:
        return False, "Tên không được vượt quá 255 ký tự"
    
    return True, ""


def validate_user_id(user_id: int) -> Tuple[bool, str]:
    """
    Validate user ID format
    Returns: (is_valid, error_message)
    """
    if not isinstance(user_id, int):
        return False, "User ID phải là số nguyên"
    
    if user_id <= 0:
        return False, "User ID phải lớn hơn 0"
    
    return True, ""
