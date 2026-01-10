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

