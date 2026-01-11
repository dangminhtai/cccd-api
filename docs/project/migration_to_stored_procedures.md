# Kế Hoạch Migration: Chuyển từ SQL Queries Cứng sang Stored Procedures & Functions

## 📋 Tổng Quan

Hiện tại, dự án đang sử dụng **SQL queries cứng** (hardcoded) trong Python code. Kế hoạch này đề xuất chuyển sang sử dụng **Stored Procedures** và **Functions** trong MySQL để:

- **Tối ưu hiệu suất**: Database engine có thể cache và optimize execution plans
- **Bảo mật tốt hơn**: Tránh SQL injection, centralized security
- **Dễ bảo trì**: Logic database tập trung, dễ thay đổi schema
- **Tái sử dụng**: Có thể gọi từ nhiều nơi (Python, admin tools, reports)
- **Transaction management**: Dễ quản lý transactions phức tạp

---

## 🔍 Phân Tích Hiện Trạng

### Thống Kê SQL Queries Hiện Tại

Dựa trên codebase hiện tại:

- **`services/user_service.py`**: ~33 SQL queries
- **`services/billing_service.py`**: ~21 SQL queries  
- **`services/api_key_service.py`**: ~22 SQL queries
- **Tổng cộng**: ~76 SQL queries cứng

### Các Loại Operations Hiện Tại

1. **User Management** (`user_service.py`):
   - User registration, login, authentication
   - Email verification
   - Password reset
   - User profile management
   - User search và pagination

2. **Billing & Subscriptions** (`billing_service.py`):
   - Payment creation và approval
   - Subscription management
   - Tier changes
   - Payment history

3. **API Key Management** (`api_key_service.py`):
   - API key generation và validation
   - Key rotation và history
   - Usage tracking
   - Key expiration

4. **Logging** (`logging_service.py`):
   - Request logging
   - Audit trails

---

## 🎯 Mục Tiêu Migration

### Phase 1: Critical Operations (Ưu tiên cao)
- User authentication (login, registration)
- Payment approval (transaction-critical)
- API key validation (high-frequency)

### Phase 2: Core Operations (Ưu tiên trung bình)
- User management (CRUD)
- Subscription management
- API key management

### Phase 3: Supporting Operations (Ưu tiên thấp)
- Logging operations
- Reporting queries
- Admin operations

---

## 📐 Kiến Trúc Đề Xuất

### 1. Naming Convention

**Stored Procedures:**
- Prefix: `sp_` cho stored procedures
- Format: `sp_{module}_{operation}`
- Ví dụ: `sp_user_create`, `sp_payment_approve`, `sp_api_key_validate`

**Functions:**
- Prefix: `fn_` cho functions
- Format: `fn_{module}_{operation}`
- Ví dụ: `fn_user_exists`, `fn_get_tier_rate_limit`, `fn_calculate_expiry`

### 2. Module Organization

Tổ chức theo modules:

```
sp_user_*          - User operations
sp_payment_*       - Payment operations
sp_subscription_*  - Subscription operations
sp_api_key_*       - API key operations
sp_log_*           - Logging operations
fn_user_*          - User helper functions
fn_billing_*       - Billing helper functions
```

### 3. Error Handling

- Stored procedures trả về `OUT` parameters cho success/error
- Hoặc dùng `SIGNAL SQLSTATE` để raise errors
- Python code catch và handle errors appropriately

---

## 🔄 Migration Strategy

### Bước 1: Tạo Stored Procedures (Database Layer)

**Cách làm:**
1. Tạo file SQL migration mới: `scripts/db_schema_stored_procedures.sql`
2. Định nghĩa stored procedures cho từng operation
3. Test stored procedures trực tiếp trong MySQL
4. Verify với sample data

**Lưu ý:**
- Giữ nguyên logic business hiện tại
- Đảm bảo backward compatibility
- Test kỹ với edge cases

### Bước 2: Tạo Wrapper Functions (Python Layer)

**Cách làm:**
1. Tạo module mới: `services/db_procedures.py`
2. Mỗi stored procedure có 1 Python wrapper function
3. Wrapper function:
   - Kết nối database
   - Gọi stored procedure với `CALL sp_name(...)`
   - Parse kết quả
   - Handle errors
   - Return Python objects

**Lưu ý:**
- Giữ nguyên function signatures hiện tại (nếu có thể)
- Đảm bảo type safety
- Proper error handling và logging

### Bước 3: Refactor Service Layer

**Cách làm:**
1. Thay thế từng `cursor.execute()` bằng wrapper function
2. Test từng function sau khi refactor
3. Giữ nguyên unit tests (nếu có)
4. Verify integration tests

**Lưu ý:**
- Refactor từng module một (user → billing → api_key)
- Không refactor tất cả cùng lúc
- Có rollback plan nếu cần

### Bước 4: Cleanup & Optimization

**Cách làm:**
1. Xóa SQL queries cứng không còn dùng
2. Optimize stored procedures (indexes, query plans)
3. Update documentation
4. Performance testing

---

## 📝 Chi Tiết Migration Plan

### Module 1: User Management

**Stored Procedures cần tạo:**
- `sp_user_create` - Tạo user mới
- `sp_user_authenticate` - Xác thực login
- `sp_user_get_by_email` - Lấy user theo email
- `sp_user_get_by_id` - Lấy user theo ID
- `sp_user_update_password` - Đổi password
- `sp_user_list` - Danh sách users (pagination)
- `sp_user_delete` - Xóa user

**Functions cần tạo:**
- `fn_user_exists` - Kiểm tra user tồn tại
- `fn_user_email_verified` - Kiểm tra email đã verify chưa

**Migration order:**
1. Authentication (critical)
2. User CRUD
3. Email verification
4. Password reset

### Module 2: Billing & Payments

**Stored Procedures cần tạo:**
- `sp_payment_create` - Tạo payment request
- `sp_payment_approve` - Approve payment (transaction-critical)
- `sp_payment_reject` - Reject payment
- `sp_payment_get_by_id` - Lấy payment details
- `sp_payment_list_by_user` - Lịch sử payments
- `sp_subscription_create` - Tạo subscription
- `sp_subscription_update_tier` - Đổi tier
- `sp_subscription_expire_old` - Expire subscriptions cũ

**Functions cần tạo:**
- `fn_has_pending_payment` - Kiểm tra pending payment
- `fn_get_tier_pricing` - Lấy giá tier
- `fn_calculate_subscription_expiry` - Tính ngày hết hạn

**Migration order:**
1. Payment approval (critical transaction)
2. Payment CRUD
3. Subscription management
4. Tier changes

### Module 3: API Key Management

**Stored Procedures cần tạo:**
- `sp_api_key_create` - Tạo API key mới
- `sp_api_key_validate` - Validate API key (high-frequency)
- `sp_api_key_get_by_hash` - Lấy key theo hash
- `sp_api_key_list_by_user` - Danh sách keys của user
- `sp_api_key_update_label` - Update label
- `sp_api_key_delete` - Xóa key
- `sp_api_key_extend_expiry` - Gia hạn key
- `sp_api_key_log_history` - Log key history

**Functions cần tạo:**
- `fn_api_key_is_valid` - Kiểm tra key hợp lệ
- `fn_get_key_tier` - Lấy tier của key
- `fn_get_rate_limit` - Lấy rate limit theo tier

**Migration order:**
1. API key validation (high-frequency, critical)
2. API key CRUD
3. Key history logging
4. Expiration management

### Module 4: Logging

**Stored Procedures cần tạo:**
- `sp_log_request` - Log API request
- `sp_log_get_usage_stats` - Lấy usage statistics
- `sp_log_get_by_key` - Lấy logs theo API key

**Migration order:**
1. Request logging
2. Usage statistics
3. Audit trails

---

## ⚠️ Rủi Ro & Giảm Thiểu

### Rủi Ro 1: Performance Degradation
**Nguyên nhân:** Stored procedures có thể chậm hơn nếu không optimize
**Giảm thiểu:**
- Test performance trước khi deploy
- Sử dụng EXPLAIN để analyze query plans
- Tối ưu indexes
- Có rollback plan

### Rủi Ro 2: Breaking Changes
**Nguyên nhân:** Thay đổi behavior không mong muốn
**Giảm thiểu:**
- Test kỹ với sample data
- Giữ nguyên business logic
- Integration tests
- Staged rollout (test → staging → production)

### Rủi Ro 3: Migration Complexity
**Nguyên nhân:** Quá nhiều thay đổi cùng lúc
**Giảm thiểu:**
- Migration từng module một
- Có thể chạy song song (old + new code)
- Feature flags để toggle

### Rủi Ro 4: Database Lock
**Nguyên nhân:** Stored procedures có thể lock tables
**Giảm thiểu:**
- Sử dụng appropriate isolation levels
- Tránh long-running transactions
- Monitor lock waits

---

## ✅ Definition of Done

### Phase 1 (Critical Operations)
- [ ] Tất cả stored procedures cho authentication được tạo và test
- [ ] Payment approval stored procedure hoạt động đúng
- [ ] API key validation stored procedure hoạt động đúng
- [ ] Python wrappers được implement
- [ ] Service layer đã refactor
- [ ] Integration tests pass
- [ ] Performance không giảm > 10%

### Phase 2 (Core Operations)
- [ ] Tất cả stored procedures cho user management được tạo
- [ ] Tất cả stored procedures cho billing được tạo
- [ ] Tất cả stored procedures cho API key management được tạo
- [ ] Service layer đã refactor hoàn toàn
- [ ] Unit tests pass
- [ ] Documentation updated

### Phase 3 (Supporting Operations)
- [ ] Logging stored procedures được tạo
- [ ] Tất cả SQL queries cứng đã được thay thế
- [ ] Code cleanup hoàn tất
- [ ] Performance optimization
- [ ] Final testing và verification

---

## 📚 Tài Liệu Tham Khảo

### MySQL Stored Procedures
- Syntax: `CREATE PROCEDURE sp_name(...) BEGIN ... END`
- Parameters: `IN`, `OUT`, `INOUT`
- Error handling: `SIGNAL SQLSTATE`
- Transactions: `START TRANSACTION`, `COMMIT`, `ROLLBACK`

### Best Practices
- Sử dụng prepared statements trong stored procedures
- Validate inputs
- Proper error handling
- Logging important operations
- Document parameters và return values

### Testing Strategy
- Unit test stored procedures với sample data
- Integration test với Python wrappers
- Performance test với realistic load
- Security test (SQL injection, privilege escalation)

---

## 🚀 Timeline Ước Tính

- **Phase 1 (Critical)**: 1-2 tuần
- **Phase 2 (Core)**: 2-3 tuần
- **Phase 3 (Supporting)**: 1 tuần
- **Total**: 4-6 tuần

**Lưu ý:** Timeline có thể thay đổi tùy vào complexity và testing requirements.

---

## 📌 Next Steps

1. **Review và approve** kế hoạch này
2. **Tạo database migration script** cho Phase 1
3. **Implement Python wrappers** cho Phase 1
4. **Test và verify** Phase 1
5. **Tiếp tục** với Phase 2 và 3

---

## 💡 Lưu Ý Quan Trọng

- **KHÔNG viết code SQL trong file markdown này** - chỉ hướng dẫn và kế hoạch
- **Migration từng bước một** - không rush
- **Test kỹ trước khi deploy** - đặc biệt là critical operations
- **Giữ backward compatibility** - có thể rollback nếu cần
- **Document mọi thay đổi** - để dễ maintain sau này
