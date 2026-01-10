"""
Migration script to add API Key Rotation & Management columns
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
        """,
        (db_name, table_name, index_name)
    )
    return cursor.fetchone()["COUNT(*)"] > 0

def table_exists(cursor, db_name, table_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """,
        (db_name, table_name)
    )
    return cursor.fetchone()["COUNT(*)"] > 0

def main():
    db_name = os.getenv("MYSQL_DATABASE", "cccd_api")
    table_name = "api_keys"

    try:
        conn = _get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Add label column
                column_name = "label"
                if not column_exists(cursor, db_name, table_name, column_name):
                    logger.info(f"Adding {column_name} column...")
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(100) NULL")
                    logger.info(f"[OK] Added {column_name} column")
                else:
                    logger.info(f"[OK] {column_name} column already exists")

                # Add rotated_from column (without foreign key first, then add FK separately)
                column_name = "rotated_from"
                if not column_exists(cursor, db_name, table_name, column_name):
                    logger.info(f"Adding {column_name} column...")
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} INT NULL")
                    logger.info(f"[OK] Added {column_name} column")
                else:
                    logger.info(f"[OK] {column_name} column already exists")

                # Add foreign key for rotated_from (if not exists)
                # Check if FK exists by checking constraints
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s
                    AND TABLE_NAME = %s
                    AND COLUMN_NAME = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                    """,
                    (db_name, table_name, "rotated_from")
                )
                fk_exists = cursor.fetchone()["COUNT(*)"] > 0
                
                if not fk_exists:
                    logger.info("Adding foreign key for rotated_from...")
                    try:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD FOREIGN KEY (rotated_from) REFERENCES {table_name}(id) ON DELETE SET NULL"
                        )
                        logger.info("[OK] Added foreign key for rotated_from")
                    except pymysql.Error as e:
                        logger.warning(f"Could not add foreign key (may already exist or data issue): {e}")
                else:
                    logger.info("[OK] Foreign key for rotated_from already exists")

                # Add suspended_at column
                column_name = "suspended_at"
                if not column_exists(cursor, db_name, table_name, column_name):
                    logger.info(f"Adding {column_name} column...")
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} DATETIME NULL")
                    logger.info(f"[OK] Added {column_name} column")
                else:
                    logger.info(f"[OK] {column_name} column already exists")

                # Create index for rotated_from
                index_name = "idx_rotated_from"
                if not index_exists(cursor, db_name, table_name, index_name):
                    logger.info(f"Creating index {index_name}...")
                    cursor.execute(f"CREATE INDEX {index_name} ON {table_name}(rotated_from)")
                    logger.info(f"[OK] Created index {index_name}")
                else:
                    logger.info(f"[OK] Index {index_name} already exists")

                # Create api_key_history table
                history_table = "api_key_history"
                if not table_exists(cursor, db_name, history_table):
                    logger.info(f"Creating {history_table} table...")
                    cursor.execute(f"""
                        CREATE TABLE {history_table} (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            key_id INT NOT NULL,
                            action VARCHAR(50) NOT NULL,
                            old_value TEXT NULL,
                            new_value TEXT NULL,
                            performed_by INT NULL,
                            performed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            
                            INDEX idx_key_id (key_id),
                            INDEX idx_performed_at (performed_at),
                            FOREIGN KEY (key_id) REFERENCES {table_name}(id) ON DELETE CASCADE
                        )
                    """)
                    logger.info(f"[OK] Created {history_table} table")
                else:
                    logger.info(f"[OK] {history_table} table already exists")

            conn.commit()
            logger.info("\n[SUCCESS] Migration completed successfully!")
        finally:
            conn.close()
    except pymysql.Error as e:
        logger.error(f"\n[ERROR] Database error: {e}")
    except Exception as e:
        logger.error(f"\n[ERROR] An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
