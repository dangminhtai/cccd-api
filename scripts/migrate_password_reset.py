#!/usr/bin/env python3
"""
Migration script để thêm password reset columns vào users table
Chạy: python scripts/migrate_password_reset.py
"""
import os
import sys

# Add parent directory to path để import được modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

import pymysql


def check_column_exists(cursor, table_name, column_name):
    """Check if column exists in table"""
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
        """,
        (table_name, column_name),
    )
    result = cursor.fetchone()
    return result["count"] > 0


def check_index_exists(cursor, table_name, index_name):
    """Check if index exists"""
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND INDEX_NAME = %s
        """,
        (table_name, index_name),
    )
    result = cursor.fetchone()
    return result["count"] > 0


def main():
    """Run migration"""
    # Connect to database
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "cccd_api"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    
    try:
        with conn.cursor() as cursor:
            # Check and add password_reset_token column
            if not check_column_exists(cursor, "users", "password_reset_token"):
                print("Adding password_reset_token column...")
                cursor.execute(
                    """
                    ALTER TABLE users 
                    ADD COLUMN password_reset_token VARCHAR(255) NULL
                    """
                )
                print("[OK] Added password_reset_token column")
            else:
                print("[OK] password_reset_token column already exists")
            
            # Check and add password_reset_expires column
            if not check_column_exists(cursor, "users", "password_reset_expires"):
                print("Adding password_reset_expires column...")
                cursor.execute(
                    """
                    ALTER TABLE users 
                    ADD COLUMN password_reset_expires DATETIME NULL
                    """
                )
                print("[OK] Added password_reset_expires column")
            else:
                print("[OK] password_reset_expires column already exists")
            
            # Check and add index
            if not check_index_exists(cursor, "users", "idx_password_reset_token"):
                print("Creating index idx_password_reset_token...")
                cursor.execute(
                    """
                    CREATE INDEX idx_password_reset_token 
                    ON users(password_reset_token)
                    """
                )
                print("[OK] Created index idx_password_reset_token")
            else:
                print("[OK] Index idx_password_reset_token already exists")
            
            # Commit changes
            conn.commit()
            print("\n[SUCCESS] Migration completed successfully!")
            
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
