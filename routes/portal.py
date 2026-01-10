"""
Portal routes - Customer-facing web portal
"""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

import os
import pymysql

from app import limiter
from services.email_service import send_password_reset_email
from services.user_service import (
    authenticate_user,
    get_user_by_id,
    get_user_subscription,
    invalidate_user_sessions,
    register_user,
    request_password_reset,
    reset_password as reset_password_service,
)

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


def require_login(f):
    """Decorator để yêu cầu login"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập để tiếp tục", "warning")
            return redirect(url_for("portal.login"))
        return f(*args, **kwargs)
    return decorated_function


@portal_bp.route("/")
def index():
    """Landing page - redirect to login or dashboard"""
    # Nếu đã đăng nhập, redirect đến dashboard
    if "user_id" in session:
        return redirect(url_for("portal.dashboard"))
    # Nếu chưa đăng nhập, redirect đến login
    return redirect(url_for("portal.login"))


@portal_bp.route("/register", methods=["GET", "POST"])
def register():
    """Đăng ký tài khoản"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        
        # Validation - ĐỪNG TIN USER INPUT (Lesson #20)
        # Check required fields
        if not email or not password or not full_name:
            flash("Vui lòng điền đầy đủ thông tin", "error")
            return render_template("portal/register.html")
        
        # Check length limits (prevent DoS)
        if len(email) > 255:
            flash("Email quá dài (tối đa 255 ký tự)", "error")
            return render_template("portal/register.html")
        
        if len(password) > 100:
            flash("Mật khẩu quá dài (tối đa 100 ký tự)", "error")
            return render_template("portal/register.html")
        
        if len(full_name) > 255:
            flash("Họ tên quá dài (tối đa 255 ký tự)", "error")
            return render_template("portal/register.html")
        
        # Check password minimum length
        if len(password) < 8:
            flash("Mật khẩu phải có ít nhất 8 ký tự", "error")
            return render_template("portal/register.html")
        
        # Basic email format validation
        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Email không hợp lệ", "error")
            return render_template("portal/register.html")
        
        # Register user
        success, error_msg, user_id, verification_token = register_user(email, password, full_name)
        
        if success and user_id:
            # Send verification email only if verification_token was generated
            if verification_token:
                from services.email_service import send_verification_email
                import os
                
                base_url = os.getenv("BASE_URL", "http://localhost:8000")
                verification_url = f"{base_url}/portal/verify-email/{verification_token}"
                
                email_sent = send_verification_email(
                    to_email=email,
                    to_name=full_name,
                    verification_url=verification_url
                )
                
                if email_sent:
                    flash("Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản", "success")
                else:
                    flash("Đăng ký thành công! Nhưng không thể gửi email xác thực. Vui lòng liên hệ hỗ trợ", "warning")
            else:
                # Email verification columns don't exist, user can use immediately
                flash("Đăng ký thành công! Vui lòng đăng nhập", "success")
            
            return redirect(url_for("portal.login"))
        else:
            flash(error_msg or "Đăng ký thất bại", "error")
            return render_template("portal/register.html")
    
    return render_template("portal/register.html")


def _get_password_reset_rate_limit_key():
    """Get rate limit key for password reset - based on email"""
    # Only rate limit POST requests
    if request.method != "POST":
        from flask_limiter.util import get_remote_address
        # Exempt GET requests from rate limiting by using a unique key that won't conflict
        return f"pwd_reset_get:{get_remote_address()}:{id(request)}"
    
    email = request.form.get("email", "").strip()
    if email:
        return f"pwd_reset:{email}"
    # Fallback to IP if no email (shouldn't happen, but safety)
    from flask_limiter.util import get_remote_address
    return f"pwd_reset_ip:{get_remote_address()}"


@portal_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per hour", key_func=_get_password_reset_rate_limit_key, per_method=True)
def forgot_password():
    """Quên mật khẩu - Request password reset"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        
        if not email:
            flash("Vui lòng nhập email", "error")
            return render_template("portal/forgot_password.html")
        
        # Basic email validation
        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Email không hợp lệ", "error")
            return render_template("portal/forgot_password.html")
        
        # Request password reset
        success, error_msg, reset_token = request_password_reset(email)
        
        if success and reset_token:
            # Get user info for email
            conn = pymysql.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                port=int(os.getenv("MYSQL_PORT", "3306")),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", ""),
                database=os.getenv("MYSQL_DATABASE", "cccd_api"),
                cursorclass=pymysql.cursors.DictCursor,
            )
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, email, full_name FROM users WHERE email = %s", (email,))
                    user = cursor.fetchone()
                    
                    if user:
                        # Send reset email
                        base_url = os.getenv("BASE_URL", "http://localhost:8000")
                        reset_url = f"{base_url}/portal/reset-password/{reset_token}"
                        
                        email_sent = send_password_reset_email(
                            to_email=user["email"],
                            to_name=user["full_name"],
                            reset_url=reset_url
                        )
                        
                        if email_sent:
                            flash("Đã gửi email đặt lại mật khẩu. Vui lòng kiểm tra hộp thư (có thể trong Spam)", "success")
                        else:
                            flash("Không thể gửi email. Vui lòng thử lại sau hoặc liên hệ hỗ trợ", "error")
            except Exception:
                pass  # Don't reveal if email exists
            finally:
                conn.close()
        elif error_msg:
            flash(error_msg, "error")
        else:
            # Don't reveal if email exists (security)
            flash("Nếu email tồn tại, bạn sẽ nhận được link đặt lại mật khẩu", "success")
        
        return redirect(url_for("portal.login"))
    
    return render_template("portal/forgot_password.html")


@portal_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    """Đặt lại mật khẩu với token"""
    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not new_password or not confirm_password:
            flash("Vui lòng điền đầy đủ thông tin", "error")
            return render_template("portal/reset_password.html", token=token)
        
        if new_password != confirm_password:
            flash("Mật khẩu xác nhận không khớp", "error")
            return render_template("portal/reset_password.html", token=token)
        
        # Validate password length
        if len(new_password) < 8:
            flash("Mật khẩu phải có ít nhất 8 ký tự", "error")
            return render_template("portal/reset_password.html", token=token)
        
        if len(new_password) > 100:
            flash("Mật khẩu quá dài (tối đa 100 ký tự)", "error")
            return render_template("portal/reset_password.html", token=token)
        
        # Reset password
        success, error_msg, user_id = reset_password_service(token, new_password)
        
        if success and user_id:
            # Invalidate all sessions
            invalidate_user_sessions(user_id)
            
            flash("Đặt lại mật khẩu thành công! Vui lòng đăng nhập với mật khẩu mới", "success")
            return redirect(url_for("portal.login"))
        else:
            flash(error_msg or "Đặt lại mật khẩu thất bại", "error")
            return render_template("portal/reset_password.html", token=token)
    
    # GET: Show reset form - Validate token first
    try:
        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "cccd_api"),
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(
                        """
                        SELECT id, password_reset_expires, status
                        FROM users
                        WHERE password_reset_token = %s
                        """,
                        (token,),
                    )
                except Exception:
                    # Columns don't exist
                    flash("Password reset feature chưa được kích hoạt", "error")
                    return redirect(url_for("portal.login"))
                
                user = cursor.fetchone()
                
                if not user:
                    flash("Token không hợp lệ hoặc đã hết hạn", "error")
                    return redirect(url_for("portal.login"))
                
                if user["status"] != "active":
                    flash("Tài khoản đã bị khóa", "error")
                    return redirect(url_for("portal.login"))
                
                if user["password_reset_expires"] and user["password_reset_expires"] < datetime.now():
                    flash("Token đã hết hạn. Vui lòng yêu cầu lại", "error")
                    return redirect(url_for("portal.forgot_password"))
        finally:
            conn.close()
    except Exception:
        flash("Có lỗi xảy ra. Vui lòng thử lại", "error")
        return redirect(url_for("portal.login"))
    
    return render_template("portal/reset_password.html", token=token)


@portal_bp.route("/login", methods=["GET", "POST"])
def login():
    """Đăng nhập"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember_me = request.form.get("remember_me") == "on"
        
        if not email or not password:
            flash("Vui lòng điền email và mật khẩu", "error")
            return render_template("portal/login.html")
        
        # Authenticate
        success, error_msg, user_data = authenticate_user(email, password)
        
        if success and user_data:
            # Set session
            session["user_id"] = user_data["id"]
            session["user_email"] = user_data["email"]
            session["user_name"] = user_data["full_name"]
            
            # Remember me: set permanent session (24h) if checked
            if remember_me:
                session.permanent = True
                # Flask will use PERMANENT_SESSION_LIFETIME from app config (24h)
                # Cookie will have max_age set and persist after browser closes
            else:
                session.permanent = False
                # Regular session cookie (expires when browser closes)
            
            # Force session to be saved (mark as modified)
            session.modified = True
            
            flash(f"Chào mừng, {user_data['full_name']}!", "success")
            return redirect(url_for("portal.dashboard"))
        else:
            flash(error_msg or "Đăng nhập thất bại", "error")
            return render_template("portal/login.html")
    
    return render_template("portal/login.html")


@portal_bp.route("/logout")
def logout():
    """Đăng xuất"""
    session.clear()
    flash("Đã đăng xuất thành công", "success")
    return redirect(url_for("portal.index"))


@portal_bp.route("/verify-email/<token>")
def verify_email(token: str):
    """Xác thực email với token"""
    from services.user_service import verify_email as verify_email_service
    
    success, error_msg = verify_email_service(token)
    
    if success:
        flash("Email đã được xác thực thành công! Bạn có thể tạo API key ngay bây giờ", "success")
        return redirect(url_for("portal.login"))
    else:
        flash(error_msg or "Xác thực email thất bại", "error")
        return redirect(url_for("portal.login"))


@portal_bp.route("/resend-verification", methods=["GET", "POST"])
@require_login
def resend_verification():
    """Gửi lại email xác thực"""
    from services.user_service import generate_new_verification_token, get_user_by_id
    from services.email_service import send_verification_email
    import os
    
    user_id = session.get("user_id")
    if not user_id:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for("portal.login"))
    
    user = get_user_by_id(user_id)
    if not user:
        flash("User không tồn tại", "error")
        return redirect(url_for("portal.login"))
    
    if user.get("email_verified"):
        flash("Email đã được xác thực rồi", "info")
        return redirect(url_for("portal.dashboard"))
    
    # Handle both GET and POST
    # Generate new token
    success, error_msg, verification_token = generate_new_verification_token(user_id)
    
    if success and verification_token:
        # Send verification email
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        verification_url = f"{base_url}/portal/verify-email/{verification_token}"
        
        email_sent = send_verification_email(
            to_email=user["email"],
            to_name=user["full_name"],
            verification_url=verification_url
        )
        
        if email_sent:
            flash("Đã gửi lại email xác thực. Vui lòng kiểm tra hộp thư", "success")
        else:
            flash("Không thể gửi email. Vui lòng thử lại sau", "error")
    else:
        flash(error_msg or "Không thể tạo token xác thực", "error")
    
    return redirect(url_for("portal.dashboard"))


@portal_bp.route("/dashboard")
@require_login
def dashboard():
    """Dashboard chính"""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    subscription = get_user_subscription(user_id)
    
    if not user:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn", "warning")
        return redirect(url_for("portal.login"))
    
    return render_template(
        "portal/dashboard.html",
        user=user,
        subscription=subscription,
    )


@portal_bp.route("/keys", methods=["GET", "POST"])
@require_login
def keys():
    """Quản lý API keys"""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    
    if not user:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn", "warning")
        return redirect(url_for("portal.login"))
    
    subscription = get_user_subscription(user_id)
    current_tier = subscription["tier"] if subscription else "free"
    
    # POST: Create new key
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "create":
            tier = request.form.get("tier", current_tier)
            days_valid_str = request.form.get("days_valid", "").strip()
            
            # Validate tier matches subscription
            if tier not in ("free", "premium", "ultra"):
                flash("Tier không hợp lệ", "error")
                return redirect(url_for("portal.keys"))
            
            # Check if user can create this tier (must match subscription)
            if tier != current_tier:
                flash(f"Bạn chỉ có thể tạo API key tier {current_tier}. Vui lòng nâng cấp để sử dụng tier {tier}.", "error")
                return redirect(url_for("portal.keys"))
            
            # Parse days_valid - ĐỪNG TIN USER INPUT (Lesson #20)
            days_valid = None
            if days_valid_str:
                # Check length first (prevent DoS)
                if len(days_valid_str) > 10:
                    flash("Số ngày hợp lệ quá dài", "error")
                    return redirect(url_for("portal.keys"))
                
                try:
                    days_valid_int = int(days_valid_str)
                    # Validate range
                    if days_valid_int < 1:
                        flash("Số ngày hợp lệ phải lớn hơn 0", "error")
                        return redirect(url_for("portal.keys"))
                    if days_valid_int > 3650:  # Max 10 years
                        flash("Số ngày hợp lệ không được vượt quá 3650 ngày (10 năm)", "error")
                        return redirect(url_for("portal.keys"))
                    days_valid = days_valid_int
                except ValueError:
                    flash("Số ngày hợp lệ phải là số nguyên", "error")
                    return redirect(url_for("portal.keys"))
            
            # Check email verification before creating key
            if not user.get("email_verified"):
                flash("Vui lòng xác thực email trước khi tạo API key. Kiểm tra email hoặc yêu cầu gửi lại", "error")
                return redirect(url_for("portal.keys"))
            
            # Create key
            from services.api_key_service import create_api_key
            try:
                api_key = create_api_key(
                    tier=tier,
                    owner_email=user["email"],
                    user_id=user_id,
                    days_valid=days_valid,
                )
                # Store in session to show once
                session["new_api_key"] = api_key
                if days_valid:
                    flash(f"Tạo API key thành công! Key sẽ hết hạn sau {days_valid} ngày. Vui lòng lưu lại ngay.", "success")
                else:
                    flash("Tạo API key thành công! Key vĩnh viễn. Vui lòng lưu lại ngay.", "success")
            except Exception as e:
                flash(f"Lỗi khi tạo API key: {str(e)}", "error")
            
            return redirect(url_for("portal.keys"))
        
        elif action == "delete":
            # AJAX endpoint - return JSON (hard delete)
            from flask import jsonify
            key_id = request.form.get("key_id")
            if not key_id:
                return jsonify({"success": False, "error": "Key ID không được để trống"}), 400
            
            try:
                key_id_int = int(key_id)
                from services.api_key_service import delete_key_by_id
                if delete_key_by_id(key_id_int, user_id):
                    return jsonify({"success": True, "message": "Đã xóa API key thành công (đã xóa khỏi database)"})
                else:
                    return jsonify({"success": False, "error": "Không tìm thấy API key hoặc bạn không có quyền xóa"}), 404
            except (ValueError, Exception) as e:
                return jsonify({"success": False, "error": f"Lỗi khi xóa API key: {str(e)}"}), 500
        
        elif action == "update_label":
            # AJAX endpoint - return JSON
            from flask import jsonify
            key_id = request.form.get("key_id")
            label = request.form.get("label", "").strip()
            if not key_id:
                return jsonify({"success": False, "error": "Key ID không được để trống"}), 400
            
            try:
                key_id_int = int(key_id)
                from services.api_key_service import update_key_label
                success, error_msg = update_key_label(key_id_int, user_id, label if label else None)
                if success:
                    return jsonify({"success": True, "message": "Đã cập nhật label thành công"})
                else:
                    return jsonify({"success": False, "error": error_msg or "Lỗi khi cập nhật label"}), 400
            except (ValueError, Exception) as e:
                return jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500
    
    # GET: List keys
    from services.api_key_service import get_user_api_keys
    api_keys = get_user_api_keys(user_id)
    
    # Get new key from session (show once)
    new_api_key = session.pop("new_api_key", None)
    
    return render_template(
        "portal/keys.html",
        user=user,
        subscription=subscription,
        api_keys=api_keys,
        new_api_key=new_api_key,
        current_tier=current_tier,
        email_verified=user.get("email_verified", False) if user else False,
    )


@portal_bp.route("/keys/<int:key_id>/rotate", methods=["POST"])
@require_login
def rotate_key(key_id: int):
    """Rotate API key - AJAX endpoint"""
    from flask import jsonify
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Vui lòng đăng nhập"}), 401
    
    from services.api_key_service import rotate_key as rotate_key_service
    success, error_msg, new_key = rotate_key_service(key_id, user_id)
    
    if success and new_key:
        return jsonify({
            "success": True,
            "message": "Rotate key thành công! Key mới đã được tạo. Key cũ sẽ hết hạn sau 7 ngày.",
            "new_key": new_key  # Trả về key mới để show trong modal
        })
    else:
        return jsonify({"success": False, "error": error_msg or "Lỗi khi rotate key"}), 400


@portal_bp.route("/keys/<int:key_id>/suspend", methods=["POST"])
@require_login
def suspend_key(key_id: int):
    """Suspend API key - AJAX endpoint"""
    from flask import jsonify
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Vui lòng đăng nhập"}), 401
    
    from services.api_key_service import suspend_key as suspend_key_service
    success, error_msg = suspend_key_service(key_id, user_id)
    
    if success:
        return jsonify({"success": True, "message": "Đã suspend key thành công"})
    else:
        return jsonify({"success": False, "error": error_msg or "Lỗi khi suspend key"}), 400


@portal_bp.route("/keys/<int:key_id>/resume", methods=["POST"])
@require_login
def resume_key(key_id: int):
    """Resume API key - AJAX endpoint"""
    from flask import jsonify
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Vui lòng đăng nhập"}), 401
    
    from services.api_key_service import resume_key as resume_key_service
    success, error_msg = resume_key_service(key_id, user_id)
    
    if success:
        return jsonify({"success": True, "message": "Đã resume key thành công"})
    else:
        return jsonify({"success": False, "error": error_msg or "Lỗi khi resume key"}), 400


@portal_bp.route("/keys/<int:key_id>/usage")
@require_login
def key_usage(key_id: int):
    """Get usage stats for a specific key (JSON API)"""
    user_id = session.get("user_id")
    if not user_id:
        from flask import jsonify
        return jsonify({"error": "Unauthorized"}), 401
    
    days = request.args.get("days", "30", type=int)
    if days not in (7, 30, 90, 365):
        days = 30
    
    from services.api_key_service import get_key_usage_per_key
    from flask import jsonify
    
    usage = get_key_usage_per_key(key_id, user_id, days=days)
    if usage is None:
        return jsonify({"error": "Key not found or access denied"}), 404
    
    return jsonify(usage)


@portal_bp.route("/usage")
@require_login
def usage():
    """Usage statistics dashboard"""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    
    if not user:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn", "warning")
        return redirect(url_for("portal.login"))
    
    # Get days parameter (default 30)
    days = request.args.get("days", "30", type=int)
    if days not in (7, 30, 90, 365):
        days = 30
    
    # Get usage stats
    from services.usage_service import get_user_usage_stats
    stats = get_user_usage_stats(user_id, days=days)
    
    return render_template(
        "portal/usage.html",
        user=user,
        stats=stats,
        days=days,
    )


@portal_bp.route("/usage/api")
@require_login
def usage_api():
    """API endpoint để lấy usage stats (JSON) - dùng cho AJAX/Chart.js"""
    user_id = session.get("user_id")
    
    if not user_id:
        from flask import jsonify
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get days parameter (default 30)
    days = request.args.get("days", "30", type=int)
    if days not in (7, 30, 90, 365):
        days = 30
    
    # Get usage stats
    from services.usage_service import get_user_usage_stats
    stats = get_user_usage_stats(user_id, days=days)
    
    from flask import jsonify
    return jsonify(stats)


@portal_bp.route("/billing")
@require_login
def billing():
    """Billing history và subscription management"""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    
    if not user:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn", "warning")
        return redirect(url_for("portal.login"))
    
    subscription = get_user_subscription(user_id)
    from services.billing_service import get_user_payments, get_tier_pricing
    
    payments = get_user_payments(user_id)
    pricing = get_tier_pricing()
    
    return render_template(
        "portal/billing.html",
        user=user,
        subscription=subscription,
        payments=payments,
        pricing=pricing,
    )


@portal_bp.route("/upgrade", methods=["GET", "POST"])
@require_login
def upgrade():
    """Upgrade tier - Manual payment flow"""
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)
    
    if not user:
        session.clear()
        flash("Phiên đăng nhập đã hết hạn", "warning")
        return redirect(url_for("portal.login"))
    
    subscription = get_user_subscription(user_id)
    current_tier = subscription["tier"] if subscription else "free"
    
    from services.billing_service import get_tier_pricing, create_payment, approve_payment
    
    pricing = get_tier_pricing()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "request_upgrade":
            target_tier = request.form.get("tier")
            
            if target_tier not in pricing:
                flash("Tier không hợp lệ", "error")
                return redirect(url_for("portal.upgrade"))
            
            if target_tier == current_tier:
                flash("Bạn đã ở tier này rồi", "warning")
                return redirect(url_for("portal.upgrade"))
            
            # Check if downgrade
            tier_order = {"free": 0, "premium": 1, "ultra": 2}
            if tier_order.get(target_tier, 0) < tier_order.get(current_tier, 0):
                flash("Không thể downgrade. Vui lòng liên hệ admin.", "error")
                return redirect(url_for("portal.upgrade"))
            
            # Create payment request
            amount = pricing[target_tier]["price"]
            currency = pricing[target_tier].get("currency", "VND")
            payment_id = create_payment(
                user_id=user_id,
                amount=amount,
                currency=currency,
                payment_gateway="manual",
                notes=f"Upgrade from {current_tier} to {target_tier}",
            )
            
            if payment_id:
                # Format amount with VND
                if currency == "VND":
                    amount_formatted = f"{amount:,.0f}".replace(",", ".")
                else:
                    amount_formatted = f"${amount:.2f}"
                
                flash(
                    f"Đã tạo yêu cầu nâng cấp lên {pricing[target_tier]['name']}. "
                    f"Admin sẽ xử lý thanh toán {amount_formatted} {currency} và kích hoạt tier mới.",
                    "success"
                )
            else:
                flash("Lỗi khi tạo yêu cầu thanh toán", "error")
            
            return redirect(url_for("portal.billing"))
        
        elif action == "approve_payment":
            # Admin only - nhưng để đây cho MVP (manual approval)
            payment_id = request.form.get("payment_id")
            if payment_id:
                try:
                    payment_id_int = int(payment_id)
                    if approve_payment(payment_id_int, user_id):
                        flash("Thanh toán đã được approve và subscription đã được update", "success")
                    else:
                        flash("Không thể approve payment", "error")
                except (ValueError, Exception) as e:
                    flash(f"Lỗi: {str(e)}", "error")
            
            return redirect(url_for("portal.billing"))
    
    # GET: Show upgrade page
    return render_template(
        "portal/upgrade.html",
        user=user,
        subscription=subscription,
        current_tier=current_tier,
        pricing=pricing,
    )

