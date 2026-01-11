"""
Admin API routes - Quản lý API keys
Yêu cầu header: X-Admin-Key
"""
from __future__ import annotations

import os

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
def admin_dashboard():
    """Trang admin dashboard - chỉ hiển thị form, không load data nhạy cảm"""
    from flask import current_app
    
    # KHÔNG load pending_payments ở đây vì chưa verify admin key
    # Pending payments sẽ được load qua JavaScript khi user nhập key và gọi API
    # Bảo mật: Không expose sensitive data trong initial render
    
    # Lấy thông tin API settings để hiển thị trong demo section
    settings = current_app.config.get("SETTINGS")
    api_key_mode = getattr(settings, "api_key_mode", "simple")
    api_key_required = (
        api_key_mode == "tiered" or 
        bool(getattr(settings, "api_key", None))
    )
    configured_key = getattr(settings, "api_key", "") or ""
    
    return render_template(
        "admin.html", 
        pending_payments=None,
        api_key_required=api_key_required,
        configured_key=configured_key,
        api_key_mode=api_key_mode,
    )


def _get_request_id() -> str:
    return g.get("request_id", "-")


@admin_bp.before_request
def check_admin_auth():
    """Kiểm tra Admin key trước mọi request"""
    admin_secret = os.getenv("ADMIN_SECRET")
    if not admin_secret:
        # Nếu chưa config ADMIN_SECRET, vẫn cho phép GET /admin/ để hiển thị form nhập key
        # Nhưng không cho phép các action khác (API endpoints)
        if request.method == "GET" and request.endpoint == "admin.admin_dashboard":
            return None
        return jsonify({"error": "Admin API chưa được cấu hình (ADMIN_SECRET)"}), 503
    
    # Cho GET /admin/, KHÔNG yêu cầu admin key (template sẽ yêu cầu user nhập)
    # Template sẽ chỉ hiển thị form, không load data nhạy cảm
    # Data sẽ được load qua API khi user nhập key
    # Demo section cũng được tích hợp trong admin dashboard
    if request.method == "GET" and request.endpoint == "admin.admin_dashboard":
        return None
    
    # Cho TẤT CẢ routes khác (API endpoints), yêu cầu admin key trong header
    provided_key = request.headers.get("X-Admin-Key")
    if provided_key != admin_secret:
        return jsonify({"error": "Unauthorized - Admin key không hợp lệ"}), 403


@admin_bp.post("/keys/create")
def create_key():
    """
    Tạo API key mới
    Body: { "tier": "free|premium|ultra", "email": "...", "days": 30 }
    """
    from services.api_key_service import create_api_key
    
    data = request.get_json(silent=True) or {}
    tier = data.get("tier", "free")
    email = data.get("email")
    days = data.get("days")
    
    if tier not in ("free", "premium", "ultra"):
        return jsonify({"error": "tier phải là free, premium hoặc ultra"}), 400
    
    if not email:
        return jsonify({"error": "email là bắt buộc"}), 400
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"error": "Email không hợp lệ"}), 400
    
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
        api_key = create_api_key(tier=tier, owner_email=email, days_valid=days_valid)
        return jsonify({
            "success": True,
            "api_key": api_key,  # Chỉ hiển thị 1 lần
            "tier": tier,
            "email": email,
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


@admin_bp.get("/stats")
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
    from services.user import get_users_list
    
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
        from services.user import delete_user
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



