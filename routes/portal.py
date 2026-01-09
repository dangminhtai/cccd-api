"""
Portal routes - Customer-facing web portal
"""
from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from services.user_service import authenticate_user, get_user_by_id, get_user_subscription, register_user

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
    """Landing page"""
    return render_template("portal/index.html")


@portal_bp.route("/register", methods=["GET", "POST"])
def register():
    """Đăng ký tài khoản"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        
        # Validation
        if not email or not password or not full_name:
            flash("Vui lòng điền đầy đủ thông tin", "error")
            return render_template("portal/register.html")
        
        if len(password) < 8:
            flash("Mật khẩu phải có ít nhất 8 ký tự", "error")
            return render_template("portal/register.html")
        
        # Register user
        success, error_msg, user_id = register_user(email, password, full_name)
        
        if success:
            flash("Đăng ký thành công! Vui lòng đăng nhập", "success")
            return redirect(url_for("portal.login"))
        else:
            flash(error_msg or "Đăng ký thất bại", "error")
            return render_template("portal/register.html")
    
    return render_template("portal/register.html")


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
            session.permanent = remember_me
            
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
            
            # Parse days_valid
            days_valid = None
            if days_valid_str:
                try:
                    days_valid_int = int(days_valid_str)
                    if days_valid_int < 1:
                        flash("Số ngày hợp lệ phải lớn hơn 0", "error")
                        return redirect(url_for("portal.keys"))
                    days_valid = days_valid_int
                except ValueError:
                    flash("Số ngày hợp lệ phải là số nguyên", "error")
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
            key_id = request.form.get("key_id")
            if key_id:
                try:
                    key_id_int = int(key_id)
                    from services.api_key_service import deactivate_key_by_id
                    if deactivate_key_by_id(key_id_int, user_id):
                        flash("Đã xóa API key thành công", "success")
                    else:
                        flash("Không tìm thấy API key hoặc bạn không có quyền xóa", "error")
                except (ValueError, Exception) as e:
                    flash(f"Lỗi khi xóa API key: {str(e)}", "error")
            
            return redirect(url_for("portal.keys"))
    
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
    )
