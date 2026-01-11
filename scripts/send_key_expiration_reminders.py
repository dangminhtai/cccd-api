"""
Script to send key expiration reminders
Run this periodically (e.g., daily via cron) to check and send email reminders
for API keys expiring in 7, 3, and 1 days.
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import logging
import pymysql

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def send_key_expiration_reminders():
    """Check for keys expiring soon and send email reminders"""
    try:
        # Initialize Flask app context for template rendering
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from services.email_service import send_key_expiration_warning_email
            from services.user_service import get_user_by_id
            
            conn = _get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # Check if expires_at column exists
                    cursor.execute(
                        """
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                        AND TABLE_NAME = 'api_keys'
                        AND COLUMN_NAME = 'expires_at'
                        """
                    )
                    if cursor.fetchone() is None:
                        logger.warning("expires_at column not found, skipping expiration reminders")
                        return
                    
                    # Get keys expiring in 7, 3, and 1 days
                    reminder_days = [7, 3, 1]
                    base_url = os.getenv("BASE_URL", "http://localhost:8000")
                    keys_url = f"{base_url}/portal/keys"
                    
                    for days in reminder_days:
                        target_date = (datetime.now() + timedelta(days=days)).date()
                        target_date_end = target_date + timedelta(days=1)
                        
                        # Query keys expiring on target_date
                        cursor.execute(
                            """
                            SELECT 
                                ak.id,
                                ak.key_prefix,
                                ak.tier,
                                ak.owner_email,
                                ak.expires_at,
                                ak.user_id,
                                u.full_name,
                                u.email_verified
                            FROM api_keys ak
                            LEFT JOIN users u ON ak.user_id = u.id
                            WHERE ak.expires_at IS NOT NULL
                            AND ak.expires_at >= %s
                            AND ak.expires_at < %s
                            AND ak.active = TRUE
                            AND (u.email_verified IS NULL OR u.email_verified = TRUE)
                            """,
                            (target_date, target_date_end),
                        )
                        
                        keys = cursor.fetchall()
                        logger.info(f"Found {len(keys)} keys expiring in {days} days (on {target_date})")
                        
                        for key in keys:
                            try:
                                # Get user info
                                user = get_user_by_id(key["user_id"]) if key["user_id"] else None
                                if not user:
                                    logger.warning(f"User not found for key {key['id']}, skipping")
                                    continue
                                
                                user_name = user.get("full_name") or key.get("owner_email", "User")
                                user_email = user.get("email") or key.get("owner_email")
                                
                                if not user_email:
                                    logger.warning(f"No email found for key {key['id']}, skipping")
                                    continue
                                
                                # Format expiration date
                                expires_at = key["expires_at"]
                                if isinstance(expires_at, str):
                                    expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                                expiration_date_str = expires_at.strftime("%d/%m/%Y")
                                
                                # Send email
                                success = send_key_expiration_warning_email(
                                    to_email=user_email,
                                    to_name=user_name,
                                    key_prefix=key["key_prefix"],
                                    tier=key["tier"],
                                    days_remaining=days,
                                    expiration_date=expiration_date_str,
                                    keys_url=keys_url,
                                )
                                
                                if success:
                                    logger.info(f"Sent {days}-day reminder for key {key['id']} ({key['key_prefix']}...) to {user_email}")
                                else:
                                    logger.error(f"Failed to send {days}-day reminder for key {key['id']} to {user_email}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing key {key['id']}: {str(e)}", exc_info=True)
                                continue
                    
            finally:
                conn.close()
                
    except Exception as e:
        logger.error(f"Error in send_key_expiration_reminders: {str(e)}", exc_info=True)


if __name__ == "__main__":
    logger.info("Starting key expiration reminder check...")
    send_key_expiration_reminders()
    logger.info("Key expiration reminder check completed")
