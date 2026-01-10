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


def approve_payment_admin(payment_id: int) -> tuple[bool, Optional[str]]:
    """
    Approve payment từ admin (không cần user_id check)
    Returns: (success, error_message)
    """
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get payment info với user info
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
                return False, "Payment không tồn tại hoặc đã được xử lý"
            
            user_id = payment["user_id"]
            amount = float(payment["amount"])
            
            # Determine tier from amount
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
            
            # Create new subscription (1 month default)
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(days=30)
            
            cursor.execute(
                """
                INSERT INTO subscriptions (user_id, tier, status, payment_method, amount, currency, expires_at)
                VALUES (%s, %s, 'active', %s, %s, %s, %s)
                """,
                (user_id, tier, payment["payment_gateway"], amount, payment["currency"], expires_at),
            )
            subscription_id = cursor.lastrowid
            
            if not subscription_id:
                conn.rollback()
                return False, "Không thể tạo subscription"
            
            # Update payment status - QUAN TRỌNG: Phải update status = 'success'
            cursor.execute(
                """
                UPDATE payments
                SET status = 'success', paid_at = NOW(), subscription_id = %s
                WHERE id = %s AND status = 'pending'
                """,
                (subscription_id, payment_id),
            )
            
            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Không thể update payment status (có thể đã được xử lý)"
            
            # Extend API keys expiration cho user này
            # Lấy subscription duration từ amount (1 month = 30 days)
            # Premium/Ultra: extend 30 days từ ngày hết hạn hiện tại hoặc từ bây giờ
            cursor.execute(
                """
                UPDATE api_keys
                SET expires_at = DATE_ADD(
                    COALESCE(expires_at, NOW()),
                    INTERVAL 30 DAY
                )
                WHERE user_id = %s 
                AND status = 'active'
                AND (expires_at IS NULL OR expires_at > NOW())
                """,
                (user_id,),
            )
            keys_extended = cursor.rowcount
            
            # Commit transaction - QUAN TRỌNG: Phải commit để lưu thay đổi
            # Tất cả operations đã thành công, commit để lưu vào database
            conn.commit()
            
            return True, f"Đã approve payment và extend {keys_extended} API key(s)"
            
        except Exception as e:
            # Rollback nếu có lỗi
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise e
        finally:
            if cursor:
                cursor.close()
            
    except Exception as e:
        import traceback
        error_msg = f"Lỗi khi approve payment: {str(e)}\n{traceback.format_exc()}"
        return False, error_msg
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


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
