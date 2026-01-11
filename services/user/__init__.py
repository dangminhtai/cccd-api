"""
User Module - Public API exports
"""
from __future__ import annotations

from services.user.models import Subscription, User
from services.user.service import (
    authenticate_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_subscription,
    get_users_list,
    invalidate_user_sessions,
    register_user,
    request_password_reset,
    reset_password,
    resend_verification_email,
    verify_email,
)

# Backward compatibility alias
generate_new_verification_token = resend_verification_email

__all__ = [
    # Service functions
    "register_user",
    "authenticate_user",
    "get_user_by_id",
    "get_user_by_email",
    "get_users_list",
    "delete_user",
    "request_password_reset",
    "reset_password",
    "verify_email",
    "resend_verification_email",
    "get_user_subscription",
    "invalidate_user_sessions",
    # Models
    "User",
    "Subscription",
]
