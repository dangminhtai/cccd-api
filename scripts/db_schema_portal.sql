-- Database schema for Customer Portal (Step 12)
-- Run this on your MySQL database: mysql -u root -p cccd_api < scripts/db_schema_portal.sql

USE cccd_api;

-- Users table (khách hàng)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    full_name VARCHAR(255) NOT NULL,
    status ENUM('active', 'suspended', 'deleted') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL,
    
    INDEX idx_email (email),
    INDEX idx_status (status)
);

-- Subscriptions table (đăng ký tier)
CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    tier ENUM('free', 'premium', 'ultra') NOT NULL DEFAULT 'free',
    status ENUM('active', 'expired', 'cancelled') NOT NULL DEFAULT 'active',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NULL,  -- NULL = never expires (for lifetime subscriptions)
    payment_method VARCHAR(50) NULL,  -- 'manual', 'stripe', 'paypal', etc.
    amount DECIMAL(10, 2) NULL,  -- Amount paid
    currency VARCHAR(3) DEFAULT 'USD',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_tier (tier)
);

-- Payments table (lịch sử thanh toán)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subscription_id INT NULL,  -- Link to subscription if applicable
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status ENUM('pending', 'success', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    payment_gateway VARCHAR(50) NULL,  -- 'manual', 'stripe', 'paypal', etc.
    transaction_id VARCHAR(255) NULL,  -- Gateway transaction ID
    notes TEXT NULL,  -- Admin notes for manual payments
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Link API keys to users (update existing api_keys table)
-- Note: This assumes api_keys table already exists from Step 10
-- MySQL doesn't support IF NOT EXISTS in ALTER TABLE, so we check first
-- Run this manually if needed:
-- ALTER TABLE api_keys ADD COLUMN user_id INT NULL;
-- ALTER TABLE api_keys ADD FOREIGN KEY fk_api_keys_user_id (user_id) REFERENCES users(id) ON DELETE SET NULL;
-- CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Default subscription for new users (free tier)
-- This will be created automatically when user registers
