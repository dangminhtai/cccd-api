-- Script để update password cho admin user
-- Usage: mysql -u root -p cccd_api < scripts/update_admin_password.sql
-- Hoặc chạy trực tiếp trong MySQL client

USE cccd_api;

-- Update password hash cho admin user
-- Password: admin123
-- Hash được generate bằng: python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt(rounds=12)).decode())"
UPDATE admin_users 
SET password_hash = '$2b$12$CENlNM5pFX8lY5doiUP8dOpbKS0oXdQ0hYc7IimzZQx4hHlOfRmLO'
WHERE username = 'admin';

-- Verify update
SELECT id, username, email, is_active, 
       CASE 
           WHEN password_hash = '$2b$12$CENlNM5pFX8lY5doiUP8dOpbKS0oXdQ0hYc7IimzZQx4hHlOfRmLO' 
           THEN 'Password updated successfully' 
           ELSE 'Password NOT updated' 
       END as status
FROM admin_users 
WHERE username = 'admin';
