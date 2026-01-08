-- Database schema for API Key Tiers
-- Run this on your MySQL database

CREATE DATABASE IF NOT EXISTS cccd_api;
USE cccd_api;

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash (64 chars hex)
    key_prefix VARCHAR(20) NOT NULL,        -- First 8 chars of key for identification
    tier ENUM('free', 'premium', 'ultra') NOT NULL DEFAULT 'free',
    owner_email VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NULL,               -- NULL = never expires
    active BOOLEAN NOT NULL DEFAULT TRUE,
    
    INDEX idx_key_hash (key_hash),
    INDEX idx_tier (tier),
    INDEX idx_owner_email (owner_email)
);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    key_id INT NOT NULL,
    request_date DATE NOT NULL,
    request_count INT NOT NULL DEFAULT 0,
    
    UNIQUE KEY uk_key_date (key_id, request_date),
    FOREIGN KEY (key_id) REFERENCES api_keys(id) ON DELETE CASCADE
);

-- Rate limit config per tier
CREATE TABLE IF NOT EXISTS tier_config (
    tier ENUM('free', 'premium', 'ultra') PRIMARY KEY,
    rate_limit_per_minute INT NOT NULL,
    rate_limit_per_day INT NULL,           -- NULL = unlimited
    description VARCHAR(255)
);

-- Insert default tier config
INSERT INTO tier_config (tier, rate_limit_per_minute, rate_limit_per_day, description) VALUES
    ('free', 10, 1000, 'Free tier - 10 req/min, 1000 req/day'),
    ('premium', 100, NULL, 'Premium tier - 100 req/min, unlimited/day'),
    ('ultra', 1000, NULL, 'Ultra tier - 1000 req/min, unlimited/day')
ON DUPLICATE KEY UPDATE tier=tier;

