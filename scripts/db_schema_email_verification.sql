-- Add email verification columns to users table
-- Run this on your MySQL database: mysql -u root -p cccd_api < scripts/db_schema_email_verification.sql

USE cccd_api;

-- Add email verification columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS verification_token_expires DATETIME NULL;

-- Create index for faster verification token lookup
CREATE INDEX IF NOT EXISTS idx_verification_token ON users(verification_token);

-- Note: verification_token_expires will be set to 24 hours from creation
