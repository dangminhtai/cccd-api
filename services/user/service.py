"""
User Service - Business logic for user operations
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from services.user import repository, validators, utils

logger = logging.getLogger(__name__)


def register_user(email: str, password: str, full_name: str) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
    """
    Đăng ký user mới
    
    Returns:
        (success, error_message, user_id, verification_token)
    """
    try:
        # Validate inputs
        email_valid, email_error = validators.validate_email(email)
        if not email_valid:
            return False, email_error, None, None
        
        password_valid, password_error = validators.validate_password(password)
        if not password_valid:
            return False, password_error, None, None
        
        full_name_valid, full_name_error = validators.validate_full_name(full_name)
        if not full_name_valid:
            return False, full_name_error, None, None
        
        # Check if email already exists
        if repository.check_email_exists(email):
            return False, "Email đã được sử dụng", None, None
        
        # Hash password
        password_hash = utils.hash_password(password)
        
        # Generate verification token
        verification_token = utils.generate_verification_token()
        verification_expires = datetime.now() + timedelta(hours=24)
        
        # Create user
        user_id = repository.create_user(email, password_hash, full_name, verification_token, verification_expires)
        
        # Create default free subscription
        repository.create_subscription(user_id, "free")
        
        return True, None, user_id, verification_token
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        return False, "Lỗi hệ thống khi đăng ký", None, None


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Xác thực user (login)
    
    Returns:
        (success, user_data, error_message)
    """
    try:
        # Get user by email (with password_hash)
        user = repository.get_user_by_email(email, include_password=True)
        if not user:
            return False, None, "Email hoặc password không đúng"
        
        # Check if user is active
        if user.get("status") != "active":
            return False, None, "Tài khoản đã bị khóa"
        
        # Get password hash
        password_hash = user.get("password_hash")
        if not password_hash:
            return False, None, "Email hoặc password không đúng"
        
        # Verify password
        if not utils.verify_password(password, password_hash):
            return False, None, "Email hoặc password không đúng"
        
        # Update last_login_at
        repository.update_user_last_login(user["id"])
        
        # Return user data (without password_hash)
        user_data = {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "status": user["status"],
            "email_verified": user.get("email_verified", False),
        }
        
        return True, user_data, None
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}", exc_info=True)
        return False, None, "Lỗi hệ thống khi đăng nhập"


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Lấy user theo ID"""
    valid, error = validators.validate_user_id(user_id)
    if not valid:
        logger.warning(f"Invalid user_id: {error}")
        return None
    
    return repository.get_user_by_id(user_id)


def get_user_by_email(email: str) -> Optional[dict]:
    """Lấy user theo email (cho admin)"""
    email_valid, email_error = validators.validate_email(email)
    if not email_valid:
        logger.warning(f"Invalid email: {email_error}")
        return None
    
    user = repository.get_user_by_email(email)
    if not user:
        return None
    
    # Get current subscription
    subscription = repository.get_user_subscription(user["id"])
    
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


def get_users_list(page: int = 1, per_page: int = 20, search: Optional[str] = None) -> tuple[list[dict], int]:
    """
    Lấy danh sách users với pagination (cho admin)
    Returns: (users_list, total_count)
    """
    return repository.get_users_list(page=page, per_page=per_page, search=search)


def delete_user(user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Hard delete a user and all associated data
    """
    valid, error = validators.validate_user_id(user_id)
    if not valid:
        return False, error
    
    try:
        repository.delete_user(user_id)
        return True, f"Đã xóa user ID {user_id} và tất cả dữ liệu liên quan thành công."
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
        return False, f"Lỗi hệ thống khi xóa user: {str(e)}"


def request_password_reset(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Yêu cầu reset password (tạo token và gửi email)
    
    Returns:
        (success, error_message, reset_token)
    """
    try:
        # Get user by email
        user = repository.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists or not (security)
            return True, None, None
        
        # Generate reset token
        reset_token = utils.generate_password_reset_token()
        expires_at = datetime.now() + timedelta(hours=1)
        
        # Save token to database
        repository.create_password_reset_token(user["id"], reset_token, expires_at)
        
        return True, None, reset_token
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}", exc_info=True)
        return False, "Lỗi hệ thống khi yêu cầu reset password", None


def reset_password(token: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Reset password với token
    
    Returns:
        (success, error_message)
    """
    try:
        # Validate password
        password_valid, password_error = validators.validate_password(new_password)
        if not password_valid:
            return False, password_error
        
        # Get token from database
        token_data = repository.get_password_reset_token(token)
        if not token_data:
            return False, "Token không hợp lệ hoặc đã hết hạn"
        
        # Check if token expired
        if token_data["password_reset_expires"] < datetime.now():
            return False, "Token đã hết hạn. Vui lòng yêu cầu reset password mới."
        
        # Hash new password
        password_hash = utils.hash_password(new_password)
        
        # Update password
        repository.update_password(token_data["id"], password_hash)
        
        return True, None
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)
        return False, "Lỗi hệ thống khi reset password"


def verify_email(token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify email với token
    
    Returns:
        (success, error_message)
    """
    try:
        # Get token from database
        token_data = repository.get_email_verification_token(token)
        if not token_data:
            return False, "Token không hợp lệ hoặc đã hết hạn"
        
        # Check if token expired
        if token_data["verification_token_expires"] < datetime.now():
            return False, "Token đã hết hạn. Vui lòng yêu cầu gửi lại email verification."
        
        # Update email_verified
        repository.update_email_verified(token_data["id"])
        
        return True, None
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}", exc_info=True)
        return False, "Lỗi hệ thống khi verify email"


def resend_verification_email(user_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Resend verification email cho user
    
    Returns:
        (success, error_message, verification_token)
    """
    try:
        valid, error = validators.validate_user_id(user_id)
        if not valid:
            return False, error, None
        
        # Get user
        user = repository.get_user_by_id(user_id)
        if not user:
            return False, "Không tìm thấy user", None
        
        # Check if already verified
        if user.get("email_verified"):
            return False, "Email đã được verify rồi", None
        
        # Generate new token
        verification_token = utils.generate_verification_token()
        verification_expires = datetime.now() + timedelta(hours=24)
        
        # Update token in database
        repository.update_verification_token(user_id, verification_token, verification_expires)
        
        return True, None, verification_token
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}", exc_info=True)
        return False, "Lỗi hệ thống khi resend verification email", None


def get_user_subscription(user_id: int) -> Optional[dict]:
    """Lấy subscription hiện tại của user"""
    valid, error = validators.validate_user_id(user_id)
    if not valid:
        logger.warning(f"Invalid user_id: {error}")
        return None
    
    return repository.get_user_subscription(user_id)


def invalidate_user_sessions(user_id: int) -> None:
    """
    Invalidate all active sessions for a given user.
    Note: For Flask's default cookie-based sessions, this is a placeholder.
    Real session invalidation requires server-side session management.
    """
    logger.info(f"Invalidating sessions for user ID: {user_id} (placeholder)")
    # In a real application with server-side sessions, you would delete/mark sessions as invalid here.
    # For Flask's default client-side sessions, this action is limited.
