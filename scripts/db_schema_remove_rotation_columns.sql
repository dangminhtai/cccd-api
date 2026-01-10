-- Migration script to remove unused rotation/suspend columns
-- Run this on your MySQL database

USE cccd_api;

-- Drop foreign key for rotated_from first (if exists)
SET @dbname = DATABASE();
SET @tablename = "api_keys";
SET @columnname = "rotated_from";

SET @fk_name = (
    SELECT CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = @dbname
    AND TABLE_NAME = @tablename
    AND COLUMN_NAME = @columnname
    AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);

SET @preparedStatement = (SELECT IF(
    @fk_name IS NOT NULL,
    CONCAT("ALTER TABLE ", @tablename, " DROP FOREIGN KEY ", @fk_name),
    "SELECT 1"
));
PREPARE dropFK FROM @preparedStatement;
EXECUTE dropFK;
DEALLOCATE PREPARE dropFK;

-- Drop index idx_rotated_from
SET @indexname = "idx_rotated_from";
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE
            (TABLE_SCHEMA = @dbname)
            AND (TABLE_NAME = @tablename)
            AND (INDEX_NAME = @indexname)
    ) > 0,
    CONCAT("ALTER TABLE ", @tablename, " DROP INDEX ", @indexname),
    "SELECT 1"
));
PREPARE dropIndex FROM @preparedStatement;
EXECUTE dropIndex;
DEALLOCATE PREPARE dropIndex;

-- Drop rotated_from column
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE
            (TABLE_SCHEMA = @dbname)
            AND (TABLE_NAME = @tablename)
            AND (COLUMN_NAME = @columnname)
    ) > 0,
    CONCAT("ALTER TABLE ", @tablename, " DROP COLUMN ", @columnname),
    "SELECT 1"
));
PREPARE dropColumn FROM @preparedStatement;
EXECUTE dropColumn;
DEALLOCATE PREPARE dropColumn;

-- Drop suspended_at column
SET @columnname = "suspended_at";
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE
            (TABLE_SCHEMA = @dbname)
            AND (TABLE_NAME = @tablename)
            AND (COLUMN_NAME = @columnname)
    ) > 0,
    CONCAT("ALTER TABLE ", @tablename, " DROP COLUMN ", @columnname),
    "SELECT 1"
));
PREPARE dropColumn FROM @preparedStatement;
EXECUTE dropColumn;
DEALLOCATE PREPARE dropColumn;

-- Note: api_key_history table is kept as it's still used for delete/label update logging
