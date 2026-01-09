-- Optional: Request Logs Table
-- Chỉ cần tạo bảng này nếu muốn lưu detailed logs vào database
-- (Hiện tại đang dùng Flask logger - terminal/file logs)

-- Bảng này dùng để:
-- 1. Audit trail (ai gọi API khi nào)
-- 2. Phân tích usage patterns
-- 3. Debug production issues
-- 4. Compliance/security monitoring

CREATE TABLE IF NOT EXISTS request_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(32) NOT NULL,           -- UUID hoặc short ID để trace
    api_key_id INT NULL,                        -- NULL nếu không có API key (simple mode)
    api_key_prefix VARCHAR(20) NULL,            -- Prefix của key (để identify mà không lộ full key)
    ip_address VARCHAR(45) NULL,                -- IPv4 hoặc IPv6
    method VARCHAR(10) NOT NULL,                 -- GET, POST, etc.
    endpoint VARCHAR(255) NOT NULL,             -- /v1/cccd/parse
    status_code INT NOT NULL,                  -- 200, 400, 401, 500, etc.
    response_time_ms INT NULL,                  -- Thời gian xử lý (milliseconds)
    cccd_masked VARCHAR(20) NULL,               -- CCCD đã mask (ví dụ: 079******345)
    province_code VARCHAR(10) NULL,              -- Mã tỉnh (nếu parse thành công)
    province_version VARCHAR(20) NULL,          -- legacy_63 hoặc current_34
    is_valid_format BOOLEAN NULL,               -- true/false/null
    is_plausible BOOLEAN NULL,                  -- true/false/null
    error_message TEXT NULL,                    -- Message lỗi (nếu có)
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_request_id (request_id),
    INDEX idx_api_key_id (api_key_id),
    INDEX idx_api_key_prefix (api_key_prefix),
    INDEX idx_status_code (status_code),
    INDEX idx_created_at (created_at),
    INDEX idx_endpoint (endpoint),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
);

-- Cleanup strategy: Xóa logs cũ hơn 90 ngày (tùy chỉnh)
-- Có thể chạy định kỳ bằng cron job:
-- DELETE FROM request_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
