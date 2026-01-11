"""
Admin API routes - Quản lý API keys
Yêu cầu header: X-Admin-Key
"""
from __future__ import annotations

import os
import time

from flask import Blueprint, current_app, flash, g, jsonify, redirect, render_template, request, url_for
from flask_limiter.util import get_remote_address

from app import limiter
from services.admin_security import (
    get_failed_attempts_count,
    get_security_stats,
    is_ip_blocked,
    record_failed_attempt,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    """Trang đăng nhập admin"""
    from flask import session
    
    # Nếu đã đăng nhập, redirect đến dashboard
    if "admin_id" in session and session.get("is_admin") is True:
        return redirect(url_for("admin.admin_dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Vui lòng điền đầy đủ thông tin", "error")
            return render_template("admin/login.html")
        
        # Authenticate
        from services.admin_auth_service import authenticate_admin
        success, admin_data, error_msg = authenticate_admin(username, password)
        
        if success and admin_data:
            # Tạo session
            session["admin_id"] = admin_data["id"]
            session["admin_username"] = admin_data["username"]
            session["admin_email"] = admin_data["email"]
            session["admin_full_name"] = admin_data["full_name"]
            session["is_admin"] = True
            session.permanent = True  # Remember me
            
            current_app.logger.info(
                f"admin_login_success | admin_id={admin_data['id']} | "
                f"username={admin_data['username']} | ip={get_remote_address()}"
            )
            
            flash(f"Chào mừng, {admin_data['full_name']}!", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            # Log failed attempt
            current_app.logger.warning(
                f"admin_login_failed | username={username} | "
                f"ip={get_remote_address()} | error={error_msg}"
            )
            flash(error_msg or "Username hoặc password không đúng", "error")
            return render_template("admin/login.html")
    
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def admin_logout():
    """Đăng xuất admin"""
    from flask import session
    
    if "admin_id" in session:
        admin_id = session.get("admin_id")
        current_app.logger.info(
            f"admin_logout | admin_id={admin_id} | ip={get_remote_address()}"
        )
        session.clear()
        flash("Đã đăng xuất thành công", "success")
    
    return redirect(url_for("admin.admin_login"))


@admin_bp.get("/")
def admin_dashboard():
    """Trang admin dashboard - chỉ hiển thị sau khi đăng nhập"""
    from flask import session
    
    # Lấy thông tin admin từ session
    admin_id = session.get("admin_id")
    admin_username = session.get("admin_username", "Admin")
    admin_full_name = session.get("admin_full_name", "Administrator")
    
    # Lấy thông tin API settings
    settings = current_app.config.get("SETTINGS")
    api_key_mode = getattr(settings, "api_key_mode", "simple")
    api_key_required = (
        api_key_mode == "tiered" or 
        bool(getattr(settings, "api_key", None))
    )
    configured_key = getattr(settings, "api_key", "") or ""
    
    return render_template(
        "admin.html", 
        admin_username=admin_username,
        admin_full_name=admin_full_name,
        pending_payments=None,
        api_key_required=api_key_required,
        configured_key=configured_key,
        api_key_mode=api_key_mode,
    )


def _get_request_id() -> str:
    return g.get("request_id", "-")


@admin_bp.before_request
def check_admin_auth():
    """
    Kiểm tra Admin authentication trước mọi request
    Hỗ trợ 2 cách:
    1. Session-based (cho web interface) - Ưu tiên
    2. Header-based (cho API calls) - Fallback
    
    Bao gồm chống brute force: IP blocking, rate limiting, logging
    """
    from flask import session
    
    # Cho phép login page và static files
    if request.endpoint in ("admin.admin_login", "admin.admin_logout", "static"):
        return None
    
    # ===== KIỂM TRA SESSION (Ưu tiên cho web interface) =====
    if "admin_id" in session and session.get("is_admin") is True:
        # Đã đăng nhập qua session → cho phép
        return None
    
    # ===== FALLBACK: HEADER-BASED AUTH (cho API calls) =====
    admin_secret = os.getenv("ADMIN_SECRET")
    if admin_secret:
        provided_key = request.headers.get("X-Admin-Key")
        if provided_key == admin_secret:
            # Key đúng → cho phép (cho API calls)
            return None
    
    # ===== CHỐNG BRUTE FORCE =====
    # Lấy IP address của request
    ip_address = get_remote_address()
    
    # Kiểm tra xem IP có bị block không
    is_blocked, unblock_time = is_ip_blocked(ip_address)
    if is_blocked:
        remaining_seconds = int(unblock_time - time.time())
        current_app.logger.warning(
            f"admin_blocked_ip | request_id={_get_request_id()} | "
            f"ip={ip_address} | endpoint={request.endpoint} | "
            f"unblock_in={remaining_seconds}s"
        )
        # Nếu là web request, redirect đến login
        if request.endpoint and "admin" in request.endpoint:
            flash(f"IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau {remaining_seconds} giây.", "error")
            return redirect(url_for("admin.admin_login"))
        return jsonify({
            "error": f"IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau {remaining_seconds} giây.",
            "blocked_until": int(unblock_time),
            "remaining_seconds": remaining_seconds,
        }), 429
    
    # Nếu không có session và không có valid header key
    if admin_secret:
        provided_key = request.headers.get("X-Admin-Key", "")
        if provided_key and provided_key != admin_secret:
            # Có key nhưng sai → ghi lại failed attempt
            endpoint = request.endpoint or request.path
            record_failed_attempt(ip_address, endpoint)
            
            failed_count = get_failed_attempts_count(ip_address)
            
            # Log failed attempt
            current_app.logger.warning(
                f"admin_auth_failed | request_id={_get_request_id()} | "
                f"ip={ip_address} | endpoint={endpoint} | "
                f"failed_count={failed_count}"
            )
            
            # Delay để làm chậm brute force (exponential backoff)
            delay_seconds = min(0.1 * (2 ** (failed_count - 1)), 2.0)
            time.sleep(delay_seconds)
            
            # Kiểm tra lại xem có bị block sau khi record attempt không
            is_blocked, unblock_time = is_ip_blocked(ip_address)
            if is_blocked:
                remaining_seconds = int(unblock_time - time.time())
                # Web request → redirect đến login
                if request.endpoint and "admin" in request.endpoint:
                    flash(f"IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau {remaining_seconds} giây.", "error")
                    return redirect(url_for("admin.admin_login"))
                return jsonify({
                    "error": f"IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau {remaining_seconds} giây.",
                    "blocked_until": int(unblock_time),
                    "remaining_seconds": remaining_seconds,
                }), 429
    
    # Không có session và không có valid key → redirect đến login (web) hoặc 403 (API)
    if request.endpoint and "admin" in str(request.endpoint):
        # Web request → redirect đến login
        flash("Vui lòng đăng nhập để truy cập trang admin", "warning")
        return redirect(url_for("admin.admin_login"))
    
    # API request → 403
    return jsonify({"error": "Unauthorized - Vui lòng đăng nhập hoặc cung cấp admin key hợp lệ"}), 403
    
    # ===== CHỐNG BRUTE FORCE =====
    # Lấy IP address của request
    ip_address = get_remote_address()
    
    # Kiểm tra xem IP có bị block không
    is_blocked, unblock_time = is_ip_blocked(ip_address)
    if is_blocked:
        remaining_seconds = int(unblock_time - time.time())
        current_app.logger.warning(
            f"admin_blocked_ip | request_id={_get_request_id()} | "
            f"ip={ip_address} | endpoint={request.endpoint} | "
            f"unblock_in={remaining_seconds}s"
        )
        return jsonify({
            "error": f"IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau {remaining_seconds} giây.",
            "blocked_until": int(unblock_time),
            "remaining_seconds": remaining_seconds,
        }), 429  # 429 Too Many Requests
    
    # Cho TẤT CẢ routes khác (API endpoints), yêu cầu admin key trong header
    provided_key = request.headers.get("X-Admin-Key")
    
    if provided_key != admin_secret:
        # Key sai → ghi lại failed attempt và block nếu cần
        endpoint = request.endpoint or request.path
        record_failed_attempt(ip_address, endpoint)
        
        failed_count = get_failed_attempts_count(ip_address)
        
        # Log failed attempt
        current_app.logger.warning(
            f"admin_auth_failed | request_id={_get_request_id()} | "
            f"ip={ip_address} | endpoint={endpoint} | "
            f"failed_count={failed_count}"
        )
        
        # Delay để làm chậm brute force (exponential backoff)
        # Delay tăng dần theo số lần failed: 0.1s, 0.2s, 0.4s, 0.8s, 1.6s
        delay_seconds = min(0.1 * (2 ** (failed_count - 1)), 2.0)  # Max 2 seconds
        time.sleep(delay_seconds)
        
        # Kiểm tra lại xem có bị block sau khi record attempt không
        is_blocked, unblock_time = is_ip_blocked(ip_address)
        if is_blocked:
            remaining_seconds = int(unblock_time - time.time())
            return jsonify({
                "error": f"IP bị tạm khóa do quá nhiều lần thử sai. Vui lòng thử lại sau {remaining_seconds} giây.",
                "blocked_until": int(unblock_time),
                "remaining_seconds": remaining_seconds,
            }), 429
        
        # Trả về error message (không tiết lộ thông tin về key)
        return jsonify({"error": "Unauthorized - Admin key không hợp lệ"}), 403
    
    # Key đúng → reset failed attempts cho IP này (nếu có)
    # (Có thể implement reset logic nếu cần)


@admin_bp.post("/keys/create")
@limiter.limit("10 per minute")  # Rate limit cho create key
def create_key():
    """
    Tạo API key mới (admin test key - không cần email)
    Body: { "tier": "free|premium|ultra", "days": 30 }
    """
    from services.api_key_service import create_api_key
    
    data = request.get_json(silent=True) or {}
    tier = data.get("tier", "free")
    days = data.get("days")
    
    if tier not in ("free", "premium", "ultra"):
        return jsonify({"error": "tier phải là free, premium hoặc ultra"}), 400
    
    # Validate days if provided
    days_valid = None
    if days is not None and days != "":
        try:
            days_int = int(days)
            if days_int < 1:
                return jsonify({"error": "Số ngày phải >= 1"}), 400
            days_valid = days_int
        except (ValueError, TypeError):
            return jsonify({"error": "Số ngày phải là số nguyên"}), 400
    
    try:
        # Admin test key - không cần email, set owner_email = None hoặc "admin_test"
        api_key = create_api_key(tier=tier, owner_email=None, days_valid=days_valid)
        return jsonify({
            "success": True,
            "api_key": api_key,  # Chỉ hiển thị 1 lần
            "tier": tier,
            "expires_in_days": days,
            "message": "⚠️ Lưu API key ngay! Key chỉ hiển thị 1 lần.",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.get("/keys/<key_prefix>/info")
def get_key_info(key_prefix: str):
    """
    Xem thông tin key theo prefix
    Lưu ý: Chỉ tìm theo prefix, không cần full key
    """
    import pymysql
    
    conn = None
    try:
        from services.api_key_service import _get_db_connection
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT key_prefix, tier, owner_email, active, created_at, expires_at
                FROM api_keys
                WHERE key_prefix LIKE %s
                LIMIT 10
                """,
                (f"{key_prefix}%",),
            )
            rows = cursor.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
    
    if not rows:
        return jsonify({"error": "Không tìm thấy key"}), 404
    
    return jsonify({
        "count": len(rows),
        "keys": [
            {
                "key_prefix": r["key_prefix"],
                "tier": r["tier"],
                "owner_email": r["owner_email"],
                "active": r["active"],
                "created_at": str(r["created_at"]),
                "expires_at": str(r["expires_at"]) if r["expires_at"] else None,
            }
            for r in rows
        ],
    })


@admin_bp.post("/keys/<key_prefix>/deactivate")
def deactivate_key(key_prefix: str):
    """Vô hiệu hóa key theo prefix"""
    import pymysql
    
    conn = None
    try:
        from services.api_key_service import _get_db_connection
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE api_keys SET active = FALSE WHERE key_prefix = %s",
                (key_prefix,),
            )
            affected = cursor.rowcount
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
    
    if affected == 0:
        return jsonify({"error": "Không tìm thấy key"}), 404
    
    return jsonify({
        "success": True,
        "message": f"Đã vô hiệu hóa key {key_prefix}",
    })


@admin_bp.get("/keys/<key_prefix>/usage")
def get_key_usage(key_prefix: str):
    """Xem usage của key"""
    import pymysql
    
    conn = None
    try:
        from services.api_key_service import _get_db_connection
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            # Get key id
            cursor.execute(
                "SELECT id, tier FROM api_keys WHERE key_prefix = %s",
                (key_prefix,),
            )
            key_row = cursor.fetchone()
            
            if not key_row:
                return jsonify({"error": "Không tìm thấy key"}), 404
            
            # Get usage stats
            cursor.execute(
                """
                SELECT request_date, request_count
                FROM api_usage
                WHERE key_id = %s
                ORDER BY request_date DESC
                LIMIT 30
                """,
                (key_row["id"],),
            )
            usage_rows = cursor.fetchall()
            
            cursor.execute(
                "SELECT SUM(request_count) as total FROM api_usage WHERE key_id = %s",
                (key_row["id"],),
            )
            total_row = cursor.fetchone()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
    
    return jsonify({
        "key_prefix": key_prefix,
        "tier": key_row["tier"],
        "total_requests": total_row["total"] or 0,
        "daily": [
            {"date": str(r["request_date"]), "count": r["request_count"]}
            for r in usage_rows
        ],
    })


@admin_bp.get("/security-stats")
@limiter.limit("10 per minute")  # Rate limit cho security stats
def get_security_stats_endpoint():
    """Xem thống kê bảo mật (blocked IPs, failed attempts)"""
    stats = get_security_stats()
    return jsonify({
        "success": True,
        "security": stats,
    })


@admin_bp.get("/stats")
@limiter.limit("30 per minute")  # Rate limit cho admin stats
def get_stats():
    """Thống kê tổng quan"""
    import pymysql
    
    conn = None
    try:
        from services.api_key_service import _get_db_connection
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    tier,
                    COUNT(*) as total_keys,
                    SUM(active) as active_keys
                FROM api_keys
                GROUP BY tier
                """
            )
            tier_stats = cursor.fetchall()
            
            cursor.execute(
                """
                SELECT SUM(request_count) as total
                FROM api_usage
                WHERE request_date = CURDATE()
                """
            )
            today_row = cursor.fetchone()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
    
    return jsonify({
        "tiers": {
            r["tier"]: {"total": r["total_keys"], "active": r["active_keys"]}
            for r in tier_stats
        },
        "requests_today": today_row["total"] or 0,
    })


@admin_bp.get("/payments")
def admin_payments():
    """Admin API: Lấy danh sách pending payments (JSON)"""
    from services.billing_service import get_pending_payments
    
    pending_payments = get_pending_payments(limit=100)
    
    return jsonify({"payments": pending_payments})


@admin_bp.post("/payments/<int:payment_id>/approve")
def admin_approve_payment(payment_id: int):
    """Admin: Approve payment và extend API keys"""
    from services.billing_service import approve_payment_admin
    from flask import current_app
    
    current_app.logger.info(f"Admin approve payment_id={payment_id}")
    
    success, message = approve_payment_admin(payment_id)
    
    current_app.logger.info(f"Approve payment result: success={success}, message={message}")
    
    if success:
        flash(f"✅ {message}", "success")
    else:
        flash(f"❌ {message}", "error")
        current_app.logger.error(f"Failed to approve payment {payment_id}: {message}")
    
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.post("/payments/<int:payment_id>/reject")
def admin_reject_payment(payment_id: int):
    """Admin: Reject/cancel payment"""
    from services.billing_service import reject_payment
    from flask import current_app
    
    current_app.logger.info(f"Admin reject payment_id={payment_id}")
    
    success, message = reject_payment(payment_id)
    
    if success:
        flash(f"✅ {message}", "success")
    else:
        flash(f"❌ {message}", "error")
        current_app.logger.error(f"Failed to reject payment {payment_id}: {message}")
    
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.post("/users/change-tier")
def admin_change_user_tier():
    """Admin: Manually change user tier"""
    from services.billing_service import manually_change_user_tier
    from services.user_service import get_user_by_email
    from flask import current_app
    
    # Check if AJAX request
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    
    user_email = request.form.get("user_email", "").strip()
    user_id = request.form.get("user_id", "").strip()
    target_tier = request.form.get("tier")
    notes = request.form.get("notes", "").strip()
    
    if not target_tier:
        if is_ajax:
            return jsonify({"error": "Tier không được để trống"}), 400
        flash("❌ Tier không được để trống", "error")
        return redirect(url_for("admin.admin_dashboard"))
    
    # Get user_id from email if provided
    if user_email and not user_id:
        user = get_user_by_email(user_email)
        if not user:
            if is_ajax:
                return jsonify({"error": "Không tìm thấy user với email này"}), 404
            flash("❌ Không tìm thấy user với email này", "error")
            return redirect(url_for("admin.admin_dashboard"))
        user_id = user["id"]
    elif not user_id:
        if is_ajax:
            return jsonify({"error": "Vui lòng nhập email hoặc user ID"}), 400
        flash("❌ Vui lòng nhập email hoặc user ID", "error")
        return redirect(url_for("admin.admin_dashboard"))
    
    try:
        user_id = int(user_id)
    except ValueError:
        if is_ajax:
            return jsonify({"error": "User ID không hợp lệ"}), 400
        flash("❌ User ID không hợp lệ", "error")
        return redirect(url_for("admin.admin_dashboard"))
    
    current_app.logger.info(f"Admin change user_id={user_id} tier to {target_tier}")
    
    success, message = manually_change_user_tier(user_id, target_tier, notes if notes else None)
    
    if success:
        if is_ajax:
            return jsonify({"success": True, "message": message}), 200
        flash(f"✅ {message}", "success")
    else:
        if is_ajax:
            return jsonify({"error": message}), 400
        flash(f"❌ {message}", "error")
        current_app.logger.error(f"Failed to change tier: {message}")
    
    if is_ajax:
        return jsonify({"success": True, "message": message}), 200
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.get("/users/search")
def admin_search_user():
    """Admin API: Search user by email (JSON)"""
    from services.user_service import get_user_by_email
    
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"error": "Email không được để trống"}), 400
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Không tìm thấy user"}), 404
    
    return jsonify({"user": user})


@admin_bp.get("/users")
def admin_list_users():
    """Admin API: List users with pagination (JSON)"""
    from services.user_service import get_users_list
    
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip() or None
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    users, total_count = get_users_list(page=page, per_page=per_page, search=search)
    
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    
    return jsonify({
        "users": users,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
        }
    })


@admin_bp.post("/users/<int:user_id>/delete")
def admin_delete_user(user_id: int):
    """Admin: Delete user (hard delete)"""
    from services.user_service import delete_user
    from flask import current_app
    
    # Check if AJAX request
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    
    current_app.logger.info(f"Admin delete user_id={user_id}")
    
    success, message = delete_user(user_id)
    
    if success:
        if is_ajax:
            return jsonify({"success": True, "message": message}), 200
        flash(f"✅ {message}", "success")
    else:
        if is_ajax:
            return jsonify({"error": message}), 400
        flash(f"❌ {message}", "error")
        current_app.logger.error(f"Failed to delete user {user_id}: {message}")
    
    if is_ajax:
        return jsonify({"success": True, "message": message}), 200
    return redirect(url_for("admin.admin_dashboard"))



