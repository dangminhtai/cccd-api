-- Migration SQL: Convert USD payments to VND
-- Tỷ giá: 1 USD = 25,000 VND (có thể điều chỉnh)

-- Bước 1: Backup trước khi migrate (khuyến nghị)
-- CREATE TABLE payments_backup AS SELECT * FROM payments;
-- CREATE TABLE subscriptions_backup AS SELECT * FROM subscriptions;

-- Bước 2: Update payments table
UPDATE payments
SET 
    amount = amount * 25000,  -- Convert USD to VND
    currency = 'VND'
WHERE currency = 'USD';

-- Bước 3: Update subscriptions table (nếu có currency column)
-- Kiểm tra xem có column currency không trước:
-- SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
-- WHERE TABLE_SCHEMA = 'cccd_api' AND TABLE_NAME = 'subscriptions' AND COLUMN_NAME = 'currency';

-- Nếu có thì chạy:
-- UPDATE subscriptions
-- SET 
--     amount = amount * 25000,
--     currency = 'VND'
-- WHERE currency = 'USD';

-- Bước 4: Verify
-- SELECT currency, COUNT(*) as count FROM payments GROUP BY currency;
-- SELECT currency, COUNT(*) as count FROM subscriptions GROUP BY currency;
