"""
Admin API routes - Quản lý API keys
Yêu cầu header: X-Admin-Key
"""
from __future__ import annotations

import os

from flask import Blueprint, g, jsonify, render_template, request

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
def admin_dashboard():
    """Trang admin dashboard"""
    return render_template("admin.html")


def _get_request_id() -> str:
    return g.get("request_id", "-")


@admin_bp.before_request
def check_admin_auth():
    """Kiểm tra Admin key trước mọi request (trừ GET /admin/ để hiển thị HTML)"""
    # Không check auth cho route GET /admin/ (hiển thị HTML)
    if request.method == "GET" and request.endpoint == "admin.admin_dashboard":
        return None
    
    admin_secret = os.getenv("ADMIN_SECRET")
    if not admin_secret:
        return jsonify({"error": "Admin API chưa được cấu hình (ADMIN_SECRET)"}), 503
    
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
    if days is not None:
        try:
            days_int = int(days)
            if days_int < 1:
                return jsonify({"error": "Số ngày phải >= 1"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Số ngày phải là số nguyên"}), 400
    
    try:
        api_key = create_api_key(tier=tier, owner_email=email, days_valid=days)
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

