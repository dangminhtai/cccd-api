"""
Billing Service - Quản lý subscription và payments
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Optional

import pymysql

TierType = Literal["free", "premium", "ultra"]


def _get_db_connection():
    """Tạo connection MySQL từ environment variables"""
    import os
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def has_pending_payment(user_id: int) -> bool:
    """Kiểm tra xem user đã có payment pending chưa"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM payments
                    WHERE user_id = %s AND status = 'pending'
                    LIMIT 1
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
                return result is not None
        finally:
            conn.close()
    except Exception:
        return False


def get_user_payments(user_id: int, limit: int = 50) -> list[dict]:
    """Lấy lịch sử thanh toán của user"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, amount, currency, status, payment_gateway, 
                           transaction_id, notes, created_at, paid_at
                    FROM payments
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
                rows = cursor.fetchall()
        finally:
            conn.close()
        
        return [
            {
                "id": row["id"],
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "status": row["status"],
                "payment_gateway": row["payment_gateway"],
                "transaction_id": row["transaction_id"],
                "notes": row["notes"],
                "created_at": row["created_at"],
                "paid_at": row["paid_at"],
            }
            for row in rows
        ]
    except Exception:
        return []


def get_pending_payments(limit: int = 100) -> list[dict]:
    """Lấy danh sách payments đang pending (cho admin)"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        p.id,
                        p.user_id,
                        u.email,
                        u.full_name,
                        p.amount,
                        p.currency,
                        p.payment_gateway,
                        p.transaction_id,
                        p.notes,
                        p.created_at
                    FROM payments p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.status = 'pending'
                    ORDER BY p.created_at ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
        finally:
            conn.close()
        
        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "user_email": row["email"],
                "user_name": row["full_name"],
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "payment_gateway": row["payment_gateway"],
                "transaction_id": row["transaction_id"],
                "notes": row["notes"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    except Exception:
        return []


def create_payment(
    user_id: int,
    amount: float,
    currency: str = "VND",
    payment_gateway: str = "manual",
    transaction_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """
    Tạo payment record (pending)
    Returns: payment_id
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO payments (user_id, amount, currency, status, 
                                        payment_gateway, transaction_id, notes)
                    VALUES (%s, %s, %s, 'pending', %s, %s, %s)
                    """,
                    (user_id, amount, currency, payment_gateway, transaction_id, notes),
                )
                payment_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        
        return payment_id
    except Exception:
        return 0


def approve_payment(payment_id: int, user_id: int) -> bool:
    """
    Approve payment và update subscription
    Returns: True nếu thành công
    """
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Get payment info
                cursor.execute(
                    """
                    SELECT amount, currency, payment_gateway, transaction_id
                    FROM payments
                    WHERE id = %s AND user_id = %s AND status = 'pending'
                    """,
                    (payment_id, user_id),
                )
                payment = cursor.fetchone()
                
                if not payment:
                    return False
                
                # Determine tier from amount (simplified - có thể config riêng)
                # Free = 0 VND, Premium = 500,000 VND, Ultra = 2,000,000 VND
                amount = float(payment["amount"])
                if amount == 0:
                    tier = "free"
                elif amount < 1000000:  # < 1,000,000 VND = Premium
                    tier = "premium"
                else:  # >= 1,000,000 VND = Ultra
                    tier = "ultra"
                
                # Deactivate old subscription
                cursor.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'expired'
                    WHERE user_id = %s AND status = 'active'
                    """,
                    (user_id,),
                )
                
                # Create new subscription
                cursor.execute(
                    """
                    INSERT INTO subscriptions (user_id, tier, status, payment_method, amount, currency)
                    VALUES (%s, %s, 'active', %s, %s, %s)
                    """,
                    (user_id, tier, payment["payment_gateway"], amount, payment["currency"]),
                )
                subscription_id = cursor.lastrowid
                
                # Update payment status - QUAN TRỌNG: Phải check status = 'pending' để tránh double approve
                cursor.execute(
                    """
                    UPDATE payments
                    SET status = 'success', paid_at = NOW(), subscription_id = %s
                    WHERE id = %s AND status = 'pending'
                    """,
                    (subscription_id, payment_id),
                )
                
                # Verify update succeeded
                if cursor.rowcount == 0:
                    conn.rollback()
                    return False, "Không thể update payment status (có thể đã được approve rồi)"
                
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def _log_debug(msg: str):
    """Helper để log debug messages - dùng Flask logger nếu có context, nếu không thì print"""
    try:
        from flask import current_app
        current_app.logger.info(msg)
        print(msg)  # In luôn ra console để dễ debug
    except RuntimeError:
        # Không có Flask context, dùng print
        print(f"[DEBUG] {msg}")


def approve_payment_admin(payment_id: int) -> tuple[bool, Optional[str]]:
    """
    Approve payment từ admin (không cần user_id check)
    Returns: (success, error_message)
    """
    conn = None
    try:
        _log_debug(f"[APPROVE PAYMENT] Bắt đầu approve payment_id={payment_id}")
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get payment info với user info
            _log_debug(f"[APPROVE PAYMENT] Query payment với id={payment_id}, status='pending'")
            cursor.execute(
                """
                SELECT 
                    p.id,
                    p.user_id,
                    p.amount,
                    p.currency,
                    p.payment_gateway,
                    p.transaction_id,
                    p.notes,
                    p.status,
                    u.email,
                    u.full_name
                FROM payments p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = %s AND p.status = 'pending'
                """,
                (payment_id,),
            )
            payment = cursor.fetchone()
            
            if not payment:
                _log_debug(f"[APPROVE PAYMENT] Payment {payment_id} không tồn tại hoặc không phải pending")
                # Check xem payment có tồn tại không (có thể đã được approve)
                cursor.execute("SELECT id, status FROM payments WHERE id = %s", (payment_id,))
                existing = cursor.fetchone()
                if existing:
                    _log_debug(f"[APPROVE PAYMENT] Payment đã có status='{existing['status']}'")
                    return False, f"Payment đã có status='{existing['status']}', không thể approve lại"
                return False, "Payment không tồn tại"
            
            _log_debug(f"[APPROVE PAYMENT] ✅ Tìm thấy payment: id={payment['id']}, user_id={payment['user_id']}, amount={payment['amount']}, status={payment['status']}")
            
            user_id = payment["user_id"]
            amount = float(payment["amount"])
            
            # Determine tier from amount
            if amount == 0:
                tier = "free"
            elif amount < 1000000:  # < 1,000,000 VND = Premium
                tier = "premium"
            else:  # >= 1,000,000 VND = Ultra
                tier = "ultra"
            
            _log_debug(f"[APPROVE PAYMENT] Tier được xác định: {tier} (amount={amount})")
            
            # Deactivate old subscription
            _log_debug(f"[APPROVE PAYMENT] Deactivate old subscriptions cho user_id={user_id}")
            cursor.execute(
                """
                UPDATE subscriptions
                SET status = 'expired'
                WHERE user_id = %s AND status = 'active'
                """,
                (user_id,),
            )
            expired_count = cursor.rowcount
            _log_debug(f"[APPROVE PAYMENT] Đã expire {expired_count} subscription(s)")
            
            # Create new subscription (1 month default)
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(days=30)
            
            _log_debug(f"[APPROVE PAYMENT] Tạo subscription mới: tier={tier}, expires_at={expires_at}")
            cursor.execute(
                """
                INSERT INTO subscriptions (user_id, tier, status, payment_method, amount, currency, expires_at)
                VALUES (%s, %s, 'active', %s, %s, %s, %s)
                """,
                (user_id, tier, payment["payment_gateway"], amount, payment["currency"], expires_at),
            )
            subscription_id = cursor.lastrowid
            
            if not subscription_id:
                _log_debug(f"[APPROVE PAYMENT] ❌ Không thể tạo subscription (lastrowid={cursor.lastrowid})")
                conn.rollback()
                return False, "Không thể tạo subscription"
            
            _log_debug(f"[APPROVE PAYMENT] ✅ Subscription created: id={subscription_id}")
            
            # Update payment status - QUAN TRỌNG: Phải update status = 'success'
            _log_debug(f"[APPROVE PAYMENT] 🔄 UPDATE payment: id={payment_id}, set status='success', subscription_id={subscription_id}")
            cursor.execute(
                """
                UPDATE payments
                SET status = 'success', paid_at = NOW(), subscription_id = %s
                WHERE id = %s AND status = 'pending'
                """,
                (subscription_id, payment_id),
            )
            update_count = cursor.rowcount
            _log_debug(f"[APPROVE PAYMENT] UPDATE payment rowcount={update_count}")
            
            if update_count == 0:
                _log_debug(f"[APPROVE PAYMENT] ❌ UPDATE payment KHÔNG thành công (rowcount=0)")
                # Check payment status hiện tại
                cursor.execute("SELECT id, status FROM payments WHERE id = %s", (payment_id,))
                current_payment = cursor.fetchone()
                if current_payment:
                    _log_debug(f"[APPROVE PAYMENT] Payment hiện tại có status='{current_payment['status']}'")
                conn.rollback()
                return False, f"Không thể update payment status (rowcount=0, có thể status không phải 'pending')"
            
            # Verify payment đã được update trong cùng transaction
            cursor.execute("SELECT id, status, subscription_id FROM payments WHERE id = %s", (payment_id,))
            verify_payment = cursor.fetchone()
            _log_debug(f"[APPROVE PAYMENT] Verify payment sau UPDATE: id={verify_payment['id']}, status={verify_payment['status']}, subscription_id={verify_payment['subscription_id']}")
            
            if verify_payment['status'] != 'success':
                _log_debug(f"[APPROVE PAYMENT] ❌ Payment status vẫn là '{verify_payment['status']}' sau UPDATE!")
                conn.rollback()
                return False, f"Payment status không được update (vẫn là '{verify_payment['status']}')"
            
            # Đồng bộ API keys expiration với subscription expiration
            # API keys sẽ có expires_at = subscription.expires_at (đồng bộ với subscription)
            # NOTE: api_keys table có cột 'active' (BOOLEAN), không phải 'status'
            _log_debug(f"[APPROVE PAYMENT] Đồng bộ API keys expiration với subscription expires_at={expires_at}")
            cursor.execute(
                """
                UPDATE api_keys
                SET expires_at = %s
                WHERE user_id = %s 
                AND active = TRUE
                """,
                (expires_at, user_id),
            )
            keys_updated = cursor.rowcount
            _log_debug(f"[APPROVE PAYMENT] Đã đồng bộ {keys_updated} API key(s) với subscription expiration")
            
            # Commit transaction - QUAN TRỌNG: Phải commit để lưu thay đổi
            _log_debug(f"[APPROVE PAYMENT] 🔄 COMMIT transaction...")
            conn.commit()
            _log_debug(f"[APPROVE PAYMENT] ✅ COMMIT thành công!")
            
            # Verify sau commit (trong connection mới để đảm bảo thấy được data đã commit)
            verify_conn = _get_db_connection()
            try:
                verify_cursor = verify_conn.cursor()
                verify_cursor.execute("SELECT id, status, subscription_id, paid_at FROM payments WHERE id = %s", (payment_id,))
                final_payment = verify_cursor.fetchone()
                verify_cursor.close()
                
                _log_debug(f"[APPROVE PAYMENT] Verify sau COMMIT: id={final_payment['id']}, status={final_payment['status']}, subscription_id={final_payment['subscription_id']}, paid_at={final_payment['paid_at']}")
                
                if final_payment['status'] != 'success':
                    _log_debug(f"[APPROVE PAYMENT] ❌ LỖI: Payment status vẫn là '{final_payment['status']}' sau COMMIT!")
                    return False, f"Payment status không được lưu (sau commit vẫn là '{final_payment['status']}')"
                else:
                    _log_debug(f"[APPROVE PAYMENT] ✅✅✅ THÀNH CÔNG: Payment đã được approve (status='success')")
            finally:
                verify_conn.close()
            
            return True, f"Đã approve payment và đồng bộ {keys_updated} API key(s) với subscription (hết hạn: {expires_at.strftime('%Y-%m-%d')})"
            
        except Exception as e:
            # Rollback nếu có lỗi
            import traceback
            _log_debug(f"[APPROVE PAYMENT] ❌ Exception trong transaction: {e}")
            _log_debug(f"[APPROVE PAYMENT] Traceback: {traceback.format_exc()}")
            if conn:
                try:
                    _log_debug(f"[APPROVE PAYMENT] 🔄 ROLLBACK transaction...")
                    conn.rollback()
                    _log_debug(f"[APPROVE PAYMENT] ✅ ROLLBACK thành công")
                except Exception as rollback_err:
                    _log_debug(f"[APPROVE PAYMENT] ❌ Lỗi khi rollback: {rollback_err}")
            raise e
        finally:
            if cursor:
                cursor.close()
                _log_debug(f"[APPROVE PAYMENT] Cursor closed")
            
    except Exception as e:
        import traceback
        _log_debug(f"[APPROVE PAYMENT] ❌ Exception ngoài transaction: {e}")
        _log_debug(f"[APPROVE PAYMENT] Traceback: {traceback.format_exc()}")
        error_msg = f"Lỗi khi approve payment: {str(e)}\n{traceback.format_exc()}"
        return False, error_msg
    finally:
        if conn:
            try:
                conn.close()
                _log_debug(f"[APPROVE PAYMENT] Connection closed")
            except Exception as close_err:
                _log_debug(f"[APPROVE PAYMENT] ❌ Lỗi khi đóng connection: {close_err}")


def reject_payment(payment_id: int) -> tuple[bool, Optional[str]]:
    """Reject/cancel payment (chuyển status thành 'failed')"""
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE payments
                    SET status = 'failed'
                    WHERE id = %s AND status = 'pending'
                    """,
                    (payment_id,),
                )
                if cursor.rowcount == 0:
                    return False, "Payment không tồn tại hoặc không phải pending"
            conn.commit()
            return True, "Đã reject payment"
        finally:
            conn.close()
    except Exception as e:
        return False, f"Lỗi khi reject payment: {str(e)}"


def manually_change_user_tier(user_id: int, target_tier: str, notes: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Admin: Manually change user tier (không qua payment)
    Returns: (success, error_message)
    """
    if target_tier not in ("free", "premium", "ultra"):
        return False, "Tier không hợp lệ (phải là free, premium, hoặc ultra)"
    
    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check user exists
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return False, "User không tồn tại"
                
                # Deactivate old subscription
                cursor.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'expired'
                    WHERE user_id = %s AND status = 'active'
                    """,
                    (user_id,),
                )
                
                # Create new subscription
                cursor.execute(
                    """
                    INSERT INTO subscriptions (user_id, tier, status, payment_method, notes)
                    VALUES (%s, %s, 'active', 'manual', %s)
                    """,
                    (user_id, target_tier, notes or f"Admin manually changed to {target_tier}"),
                )
            conn.commit()
            return True, f"Đã đổi tier user sang {target_tier}"
        finally:
            conn.close()
    except Exception as e:
        return False, f"Lỗi khi đổi tier: {str(e)}"


def get_tier_pricing() -> dict:
    """Lấy bảng giá các tier (có thể config từ database hoặc hardcode)"""
    return {
        "free": {
            "name": "Free",
            "price": 0,
            "currency": "VND",
            "rate_limit_per_min": 10,
            "rate_limit_per_day": 1000,
            "features": ["10 requests/phút", "1000 requests/ngày", "Hỗ trợ cơ bản"],
        },
        "premium": {
            "name": "Premium",
            "price": 500000,  # VND/tháng (~$20 USD)
            "currency": "VND",
            "rate_limit_per_min": 100,
            "rate_limit_per_day": None,  # Unlimited
            "features": ["100 requests/phút", "Không giới hạn/ngày", "Hỗ trợ ưu tiên"],
        },
        "ultra": {
            "name": "Ultra",
            "price": 2000000,  # VND/tháng (~$80 USD)
            "currency": "VND",
            "rate_limit_per_min": 1000,
            "rate_limit_per_day": None,  # Unlimited
            "features": ["1000 requests/phút", "Không giới hạn/ngày", "Hỗ trợ 24/7"],
        },
    }
