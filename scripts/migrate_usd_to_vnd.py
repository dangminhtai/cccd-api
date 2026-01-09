"""
Migration script: Convert USD payments to VND
Chạy script này để convert tất cả payment records từ USD sang VND
"""
import os
import sys

# Add parent directory to path để import được modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Exchange rate: 1 USD = 25,000 VND (có thể điều chỉnh)
USD_TO_VND_RATE = 25000


def get_db_connection():
    """Tạo connection MySQL từ environment variables"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def migrate_payments():
    """Convert tất cả payments từ USD sang VND"""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # 1. Kiểm tra số lượng records cần migrate
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM payments
                WHERE currency = 'USD'
                """
            )
            result = cursor.fetchone()
            usd_count = result["count"] if result else 0
            
            if usd_count == 0:
                print("✅ Không có payment nào cần migrate (USD).")
                return
            
            print(f"📊 Tìm thấy {usd_count} payment(s) cần migrate từ USD sang VND")
            print(f"💱 Tỷ giá: 1 USD = {USD_TO_VND_RATE:,} VND")
            print()
            
            # 2. Xem preview các records sẽ bị thay đổi
            cursor.execute(
                """
                SELECT id, user_id, amount, currency, status, notes, created_at
                FROM payments
                WHERE currency = 'USD'
                ORDER BY created_at DESC
                LIMIT 10
                """
            )
            preview_records = cursor.fetchall()
            
            print("📋 Preview các records sẽ được migrate:")
            print("-" * 80)
            for record in preview_records:
                new_amount = float(record["amount"]) * USD_TO_VND_RATE
                print(
                    f"ID: {record['id']} | "
                    f"Amount: ${record['amount']:.2f} USD → {new_amount:,.0f} VND | "
                    f"Status: {record['status']} | "
                    f"Note: {record['notes'] or 'N/A'}"
                )
            print("-" * 80)
            print()
            
            # 3. Xác nhận từ user
            confirm = input("⚠️  Bạn có chắc chắn muốn migrate? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("❌ Migration đã bị hủy.")
                return
            
            # 4. Thực hiện migration
            print("\n🔄 Đang migrate...")
            
            # Update payments table
            cursor.execute(
                """
                UPDATE payments
                SET 
                    amount = amount * %s,
                    currency = 'VND'
                WHERE currency = 'USD'
                """,
                (USD_TO_VND_RATE,),
            )
            payments_updated = cursor.rowcount
            
            # Update subscriptions table (nếu có currency field)
            # Kiểm tra xem có column currency không
            cursor.execute(
                """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'subscriptions' 
                AND COLUMN_NAME = 'currency'
                """,
                (os.getenv("MYSQL_DATABASE", "cccd_api"),),
            )
            has_currency_column = cursor.fetchone() is not None
            
            subscriptions_updated = 0
            if has_currency_column:
                cursor.execute(
                    """
                    UPDATE subscriptions
                    SET 
                        amount = amount * %s,
                        currency = 'VND'
                    WHERE currency = 'USD'
                    """,
                    (USD_TO_VND_RATE,),
                )
                subscriptions_updated = cursor.rowcount
            
            # Commit transaction
            conn.commit()
            
            print(f"✅ Migration hoàn thành!")
            print(f"   - Payments updated: {payments_updated}")
            if has_currency_column:
                print(f"   - Subscriptions updated: {subscriptions_updated}")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Lỗi khi migrate: {e}")
        raise
    finally:
        conn.close()


def verify_migration():
    """Verify migration đã thành công"""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # Check remaining USD records
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM payments
                WHERE currency = 'USD'
                """
            )
            result = cursor.fetchone()
            usd_remaining = result["count"] if result else 0
            
            # Check VND records
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM payments
                WHERE currency = 'VND'
                """
            )
            result = cursor.fetchone()
            vnd_count = result["count"] if result else 0
            
            print("\n📊 Verification:")
            print(f"   - USD records còn lại: {usd_remaining}")
            print(f"   - VND records: {vnd_count}")
            
            if usd_remaining == 0:
                print("✅ Migration thành công! Không còn USD records.")
            else:
                print(f"⚠️  Vẫn còn {usd_remaining} USD record(s).")
                
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 80)
    print("Migration Script: USD → VND")
    print("=" * 80)
    print()
    
    try:
        migrate_payments()
        verify_migration()
    except KeyboardInterrupt:
        print("\n❌ Migration bị hủy bởi user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        sys.exit(1)
