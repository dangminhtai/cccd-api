"""
Script để tạo dữ liệu giả cho usage statistics
Usage: python scripts/generate_fake_usage_data.py
"""
import os
import sys
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import pymysql


def _get_db_connection():
    """Tạo connection MySQL từ environment variables"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def list_all_keys():
    """Liệt kê tất cả API keys"""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, key_prefix, tier, user_id, active
                FROM api_keys
                ORDER BY created_at DESC
                LIMIT 20
                """
            )
            keys = cursor.fetchall()
            
            if not keys:
                print("Khong tim thay API key nao trong database")
                return []
            
            print(f"Tim thay {len(keys)} API keys:")
            print("-" * 80)
            for key in keys:
                print(f"ID: {key['id']} | Prefix: {key['key_prefix']} | Tier: {key['tier']} | Active: {key['active']}")
            print("-" * 80)
            return keys
    finally:
        conn.close()


def generate_fake_data_for_key(key_prefix: str = None, key_id: int = None, days: int = 30):
    """
    Tạo dữ liệu giả cho một API key
    
    Args:
        key_prefix: Key prefix (ví dụ: ultr_39ee5b2388015696ec818138c91e10a7)
        key_id: Key ID (nếu không có prefix)
        days: Số ngày để tạo data (mặc định 30 ngày)
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Tìm key_id
            if key_id:
                cursor.execute("SELECT id, key_prefix FROM api_keys WHERE id = %s", (key_id,))
            elif key_prefix:
                cursor.execute("SELECT id, key_prefix FROM api_keys WHERE key_prefix = %s", (key_prefix,))
            else:
                print("Can phai cung cap key_prefix hoac key_id")
                return False
            
            key_row = cursor.fetchone()
            
            if not key_row:
                print(f"Khong tim thay API key")
                print("Danh sach keys co san:")
                list_all_keys()
                return False
            
            key_id = key_row["id"]
            actual_prefix = key_row["key_prefix"]
            print(f"Tim thay key_id: {key_id} cho prefix: {actual_prefix}")
            
            # Xóa data cũ (optional - comment out nếu muốn giữ data cũ)
            # cursor.execute(
            #     "DELETE FROM request_logs WHERE api_key_id = %s",
            #     (key_id,)
            # )
            # print(f"🗑️  Đã xóa {cursor.rowcount} records cũ")
            
            # Tạo data cho từng ngày
            today = datetime.now().date()
            total_inserted = 0
            
            for day_offset in range(days):
                target_date = today - timedelta(days=day_offset)
                
                # Số lượng requests mỗi ngày (variation để biểu đồ đẹp)
                # Tạo pattern: cao vào giữa tuần, thấp vào cuối tuần
                day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday
                if day_of_week < 5:  # Weekday
                    base_requests = random.randint(800, 1200)
                else:  # Weekend
                    base_requests = random.randint(200, 500)
                
                # Thêm một chút random variation
                num_requests = base_requests + random.randint(-100, 100)
                num_requests = max(50, num_requests)  # Minimum 50 requests
                
                # Success rate: 95-99%
                success_rate = random.uniform(0.95, 0.99)
                num_success = int(num_requests * success_rate)
                num_errors = num_requests - num_success
                
                # Tạo requests cho ngày này
                for i in range(num_requests):
                    # Random time trong ngày
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    created_at = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
                    
                    # Determine status code
                    if i < num_success:
                        status_code = 200
                        response_time = random.randint(20, 80)  # 20-80ms for success
                        is_valid_format = True
                        is_plausible = True
                        error_message = None
                    else:
                        # Random error types
                        error_type = random.choice(['400', '500', '429'])
                        status_code = int(error_type)
                        response_time = random.randint(100, 500)  # 100-500ms for errors
                        is_valid_format = error_type != '400'
                        is_plausible = None
                        error_message = f"Error {error_type}" if error_type != '400' else "Invalid format"
                    
                    # Random CCCD (masked)
                    cccd = f"{random.randint(100, 999)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
                    cccd_masked = f"{cccd[:3]}******{cccd[-3:]}"
                    province_code = cccd[:3]
                    
                    # Insert vào database
                    cursor.execute(
                        """
                        INSERT INTO request_logs (
                            request_id, api_key_id, api_key_prefix, ip_address,
                            method, endpoint, status_code, response_time_ms,
                            cccd_masked, province_code, province_version,
                            is_valid_format, is_plausible, error_message,
                            created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            f"fake_{key_id}_{target_date}_{i}",
                            key_id,
                            key_prefix,
                            f"192.168.1.{random.randint(1, 255)}",
                            "POST",
                            "/v1/cccd/parse",
                            status_code,
                            response_time,
                            cccd_masked,
                            province_code,
                            "current",
                            is_valid_format,
                            is_plausible,
                            error_message,
                            created_at
                        )
                    )
                    total_inserted += 1
                
                if (day_offset + 1) % 5 == 0:
                    conn.commit()
                    print(f"Da tao data cho {day_offset + 1}/{days} ngay...")
            
            conn.commit()
            print(f"Hoan thanh! Da tao {total_inserted} requests cho {days} ngay")
            print(f"Data tu {today - timedelta(days=days-1)} den {today}")
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Loi: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    import sys
    
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description="Generate fake usage data for an API key")
    parser.add_argument("--key", type=str, default=None, 
                       help="API key prefix")
    parser.add_argument("--key-id", type=int, default=None,
                       help="API key ID")
    parser.add_argument("--days", type=int, default=30, 
                       help="Number of days to generate data for (default: 30)")
    parser.add_argument("--list", action="store_true",
                       help="List all available API keys")
    
    args = parser.parse_args()
    
    if args.list:
        list_all_keys()
        sys.exit(0)
    
    if not args.key and not args.key_id:
        print("Can phai cung cap --key hoac --key-id")
        print("Dung --list de xem danh sach keys")
        sys.exit(1)
    
    print(f"Bat dau tao du lieu gia")
    if args.key:
        print(f"Key prefix: {args.key}")
    if args.key_id:
        print(f"Key ID: {args.key_id}")
    print(f"So ngay: {args.days}")
    print("-" * 50)
    
    success = generate_fake_data_for_key(key_prefix=args.key, key_id=args.key_id, days=args.days)
    
    if success:
        print("-" * 50)
        print("Hoan thanh! Refresh trang Usage de xem bieu do.")
    else:
        print("-" * 50)
        print("Co loi xay ra. Vui long kiem tra lai.")
