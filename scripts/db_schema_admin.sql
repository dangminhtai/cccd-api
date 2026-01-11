-- Admin Users Table
-- Tài khoản admin riêng biệt, không liên quan đến users table

CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123 - CHANGE THIS IN PRODUCTION!)
-- Password hash for "admin123" (bcrypt, rounds=12)
-- IMPORTANT: Change this password immediately after first login!
-- To generate new hash: python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt(rounds=12)).decode())"
INSERT INTO admin_users (username, password_hash, email, full_name, is_active) 
VALUES (
    'admin',
    '$2b$12$IG8fmVh1MYHk92w488Ipr.GW6Coba2qcvzlT02vCdV5x/ULJ4dCcW',  -- admin123 - CHANGE THIS!
    'admin@cccd-api.local',
    'System Administrator',
    TRUE
) ON DUPLICATE KEY UPDATE username=username;
