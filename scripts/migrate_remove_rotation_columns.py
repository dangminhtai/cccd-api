"""
Migration script to remove unused rotation/suspend columns from api_keys table
Drops: rotated_from, suspended_at, idx_rotated_from index
"""
import os
import sys
import pymysql
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

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

def column_exists(cursor, db_name, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (db_name, table_name, column_name)
    )
    return cursor.fetchone()["COUNT(*)"] > 0

def index_exists(cursor, db_name, table_name, index_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME = %s
        """
        , (db_name, table_name, index_name)
    )
    return cursor.fetchone()["COUNT(*)"] > 0

def foreign_key_exists(cursor, db_name, table_name, column_name):
    """Check if foreign key constraint exists for a column"""
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
        AND REFERENCED_TABLE_NAME IS NOT NULL
        """,
        (db_name, table_name, column_name)
    )
    return cursor.fetchone()["COUNT(*)"] > 0

def get_foreign_key_name(cursor, db_name, table_name, column_name):
    """Get foreign key constraint name"""
    cursor.execute(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
        AND REFERENCED_TABLE_NAME IS NOT NULL
        LIMIT 1
        """,
        (db_name, table_name, column_name)
    )
    result = cursor.fetchone()
    return result["CONSTRAINT_NAME"] if result else None

def main():
    db_name = os.getenv("MYSQL_DATABASE", "cccd_api")
    table_name = "api_keys"

    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Drop foreign key for rotated_from first (if exists)
                if foreign_key_exists(cursor, db_name, table_name, "rotated_from"):
                    fk_name = get_foreign_key_name(cursor, db_name, table_name, "rotated_from")
                    if fk_name:
                        logger.info(f"Dropping foreign key {fk_name}...")
                        try:
                            cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {fk_name}")
                            logger.info(f"[OK] Dropped foreign key {fk_name}")
                        except pymysql.Error as e:
                            logger.warning(f"Could not drop foreign key: {e}")
                
                # Drop index idx_rotated_from
                index_name = "idx_rotated_from"
                if index_exists(cursor, db_name, table_name, index_name):
                    logger.info(f"Dropping index {index_name}...")
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP INDEX {index_name}")
                        logger.info(f"[OK] Dropped index {index_name}")
                    except pymysql.Error as e:
                        logger.warning(f"Could not drop index: {e}")
                else:
                    logger.info(f"[OK] Index {index_name} does not exist")
                
                # Drop rotated_from column
                column_name = "rotated_from"
                if column_exists(cursor, db_name, table_name, column_name):
                    logger.info(f"Dropping column {column_name}...")
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                        logger.info(f"[OK] Dropped column {column_name}")
                    except pymysql.Error as e:
                        logger.error(f"Could not drop column {column_name}: {e}")
                else:
                    logger.info(f"[OK] Column {column_name} does not exist")
                
                # Drop suspended_at column
                column_name = "suspended_at"
                if column_exists(cursor, db_name, table_name, column_name):
                    logger.info(f"Dropping column {column_name}...")
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                        logger.info(f"[OK] Dropped column {column_name}")
                    except pymysql.Error as e:
                        logger.error(f"Could not drop column {column_name}: {e}")
                else:
                    logger.info(f"[OK] Column {column_name} does not exist")

            conn.commit()
            logger.info("\n[SUCCESS] Migration completed successfully!")
            logger.info("Removed: rotated_from column, suspended_at column, idx_rotated_from index")
            logger.info("Note: api_key_history table is kept as it's still used for delete/label update logging")
        finally:
            conn.close()
    except pymysql.Error as e:
        logger.error(f"\n[ERROR] Database error: {e}")
    except Exception as e:
        logger.error(f"\n[ERROR] An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
