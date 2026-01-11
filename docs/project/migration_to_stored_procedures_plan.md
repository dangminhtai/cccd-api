# Kế hoạch Migration sang Stored Procedures & Functions

## 1. Tổng quan

### 1.1 Mục tiêu
- Chuyển từ SQL queries cứng trong Python code sang Stored Procedures & Functions trong MySQL
- Giảm SQL queries trong application code, tăng performance và maintainability
- Tập trung business logic vào database layer
- Dễ dàng optimize queries mà không cần deploy lại application

### 1.2 Lợi ích
- **Performance**: Stored procedures được compile và cache trong MySQL
- **Security**: Giảm SQL injection risks, parameterized queries
- **Maintainability**: SQL logic tập trung ở database, dễ maintain
- **Consistency**: Đảm bảo business logic được thực thi nhất quán
- **Testing**: Có thể test stored procedures độc lập

### 1.3 Nhược điểm
- **Portability**: Khó migrate sang database khác (MySQL → PostgreSQL)
- **Version Control**: SQL code trong database khó track changes
- **Debugging**: Khó debug stored procedures hơn Python code
- **Deployment**: Cần deploy SQL scripts cùng với application code

## 2. Phân tích hiện trạng

### 2.1 Services hiện tại

#### 2.1.1 `user_service.py`
**Các operations chính:**
- `register_user()` - Tạo user mới + subscription
- `authenticate_user()` - Login, verify password
- `get_user_by_id()` - Lấy user theo ID
- `get_user_by_email()` - Lấy user theo email
- `get_users_list()` - List users với pagination và search
- `delete_user()` - Xóa user
- `request_password_reset()` - Tạo password reset token
- `reset_password()` - Reset password với token
- `verify_email()` - Verify email với token
- `resend_verification_email()` - Resend verification token
- `get_user_subscription()` - Lấy subscription của user

**SQL patterns:**
- SELECT users (với backward compatibility cho email_verified, last_login_at)
- INSERT users (với email verification columns)
- UPDATE users (password hash, last_login_at, email_verified)
- SELECT subscriptions (với backward compatibility cho created_at)
- DELETE users (cascade)

#### 2.1.2 `billing_service.py`
**Các operations chính:**
- `create_payment()` - Tạo payment request
- `approve_payment()` - Admin approve payment, tạo subscription
- `get_pending_payments()` - List pending payments
- `get_user_payments()` - Lấy payment history của user
- `get_user_subscription()` - Lấy subscription hiện tại
- `extend_api_keys()` - Extend API keys khi approve payment
- `manually_change_user_tier()` - Admin change tier trực tiếp
- `has_pending_payment()` - Check pending payment

**SQL patterns:**
- SELECT payments (với filters: pending, user_id)
- INSERT payments
- UPDATE payments (status, subscription_id)
- SELECT subscriptions (với filters: active, user_id)
- INSERT subscriptions (với backward compatibility cho created_at)
- UPDATE subscriptions (status, expires_at)
- UPDATE api_keys (expires_at, active)

#### 2.1.3 `api_key_service.py`
**Các operations chính:**
- `create_api_key()` - Tạo API key mới
- `validate_api_key()` - Verify API key
- `get_user_api_keys()` - List API keys của user
- `update_key_label()` - Update label của key
- `delete_key_by_id()` - Xóa API key
- `get_api_key_by_id()` - Lấy API key theo ID
- `log_key_history()` - Log history khi update/delete

**SQL patterns:**
- SELECT api_keys (với filters: user_id, active, key_hash)
- INSERT api_keys
- UPDATE api_keys (label, active, expires_at)
- DELETE api_keys
- INSERT api_key_history
- SELECT api_key_history

#### 2.1.4 `usage_service.py`
**SQL patterns:**
- SELECT request_logs (với filters: api_key_id, date range)
- Aggregation queries (COUNT, GROUP BY)
- Date range filtering

#### 2.1.5 `logging_service.py`
**SQL patterns:**
- INSERT request_logs
- SELECT request_logs (với filters)

### 2.2 Vấn đề hiện tại

#### 2.2.1 Backward Compatibility
- Nhiều queries phải handle backward compatibility (email_verified, created_at, last_login_at)
- Code phức tạp với try/except cho optional columns
- Khó maintain khi thêm columns mới

#### 2.2.2 SQL Injection Risks
- Mặc dù dùng parameterized queries, nhưng vẫn có risks nếu không cẩn thận
- String concatenation trong WHERE clauses (search queries)

#### 2.2.3 Performance
- Queries được parse mỗi lần execute
- Không có query plan caching cho dynamic queries
- Multiple queries trong loops (N+1 problem)

#### 2.2.4 Business Logic Scattered
- Business logic nằm ở Python code và database
- Khó đảm bảo consistency khi có nhiều services gọi cùng logic
- Transaction management phức tạp

## 3. Kế hoạch Migration

### 3.1 Phase 1: Preparation (Chuẩn bị)

#### 3.1.1 Database Schema Review
- **Mục tiêu**: Đảm bảo database schema đầy đủ và consistent
- **Tasks**:
  - Review tất cả SQL scripts trong `scripts/`
  - Đảm bảo tất cả columns đã được migrate (email_verified, password_reset_token, etc.)
  - Standardize column names và types
  - Add missing indexes cho performance

#### 3.1.2 Documentation
- **Mục tiêu**: Document tất cả database operations hiện tại
- **Tasks**:
  - List tất cả SQL queries trong codebase
  - Document business logic cho mỗi operation
  - Identify queries có thể optimize
  - Identify queries có backward compatibility issues

#### 3.1.3 Testing Strategy
- **Mục tiêu**: Đảm bảo có test coverage trước khi migrate
- **Tasks**:
  - Review existing tests (nếu có)
  - Plan test strategy cho stored procedures
  - Setup test database cho stored procedures

### 3.2 Phase 2: Core Operations (Các operations cốt lõi)

#### 3.2.1 User Operations
**Priority: High**

**Stored Procedures/Functions cần tạo:**
- `sp_user_register()` - Register user + create subscription
- `sp_user_authenticate()` - Authenticate user, update last_login_at
- `fn_user_get_by_id()` - Get user by ID (với backward compatibility)
- `fn_user_get_by_email()` - Get user by email (với backward compatibility)
- `sp_users_list()` - List users với pagination và search
- `sp_user_delete()` - Delete user (cascade)
- `sp_user_password_reset_request()` - Create password reset token
- `sp_user_password_reset()` - Reset password với token
- `sp_user_email_verify()` - Verify email với token
- `sp_user_email_resend_verification()` - Resend verification token

**Migration steps:**
1. Tạo stored procedures cho user operations
2. Update `user_service.py` để gọi stored procedures thay vì raw SQL
3. Test với backward compatibility
4. Remove backward compatibility code sau khi verify

#### 3.2.2 Billing Operations
**Priority: High**

**Stored Procedures/Functions cần tạo:**
- `sp_payment_create()` - Create payment request
- `sp_payment_approve()` - Approve payment, create subscription, extend API keys
- `fn_payments_pending_list()` - List pending payments
- `fn_payments_user_list()` - List payments của user
- `fn_subscription_get_active()` - Get active subscription của user
- `sp_subscription_manually_change_tier()` - Admin change tier trực tiếp
- `fn_payment_has_pending()` - Check pending payment

**Migration steps:**
1. Tạo stored procedures cho billing operations
2. Update `billing_service.py` để gọi stored procedures
3. Handle transaction trong stored procedures
4. Test với multiple scenarios (approve, reject, extend keys)

#### 3.2.3 API Key Operations
**Priority: Medium**

**Stored Procedures/Functions cần tạo:**
- `sp_api_key_create()` - Create API key, hash key
- `fn_api_key_validate()` - Validate API key, return user_id và tier
- `fn_api_keys_user_list()` - List API keys của user
- `sp_api_key_update_label()` - Update label, log history
- `sp_api_key_delete()` - Delete key, log history
- `fn_api_key_get_by_id()` - Get API key by ID

**Migration steps:**
1. Tạo stored procedures cho API key operations
2. Move key hashing logic vào stored procedure (hoặc giữ ở Python)
3. Update `api_key_service.py` để gọi stored procedures
4. Test với key validation và history logging

### 3.3 Phase 3: Supporting Operations (Các operations hỗ trợ)

#### 3.3.1 Usage/Logging Operations
**Priority: Low**

**Stored Procedures/Functions cần tạo:**
- `sp_request_log_create()` - Log request
- `fn_request_logs_get()` - Get request logs với filters
- `fn_api_usage_stats()` - Get usage statistics

**Migration steps:**
1. Tạo stored procedures cho logging operations
2. Update `logging_service.py` và `usage_service.py`
3. Optimize aggregation queries

### 3.4 Phase 4: Optimization (Tối ưu)

#### 4.1 Query Optimization
- Add indexes cho stored procedures
- Optimize JOINs và WHERE clauses
- Use EXPLAIN để analyze query plans

#### 4.2 Caching Strategy
- Consider caching cho frequently called stored procedures
- Use MySQL query cache (nếu enabled)
- Application-level caching cho read-heavy operations

#### 4.3 Transaction Management
- Move transaction logic vào stored procedures
- Ensure ACID properties
- Handle deadlocks và timeouts

## 4. Implementation Strategy

### 4.1 Naming Conventions

**Stored Procedures:**
- Prefix: `sp_` (stored procedure)
- Format: `sp_{table}_{operation}()`
- Examples:
  - `sp_user_register()`
  - `sp_payment_approve()`
  - `sp_api_key_create()`

**Functions:**
- Prefix: `fn_` (function)
- Format: `fn_{table}_{operation}()`
- Examples:
  - `fn_user_get_by_id()`
  - `fn_payments_pending_list()`
  - `fn_api_key_validate()`

### 4.2 Parameter Naming
- Use descriptive names: `p_user_id`, `p_email`, `p_tier`
- Prefix input parameters: `p_` (parameter)
- Prefix output parameters: `o_` (output) nếu cần

### 4.3 Return Values
- Stored Procedures: Use OUT parameters hoặc SELECT result set
- Functions: Return scalar values (INT, VARCHAR, JSON)
- Consider returning JSON cho complex results

### 4.4 Error Handling
- Use MySQL error handling (DECLARE HANDLER)
- Return error codes và messages
- Log errors trong database
- Python code handle errors từ stored procedures

### 4.5 Backward Compatibility
- Phase 1: Support cả raw SQL và stored procedures
- Phase 2: Migrate từng service một
- Phase 3: Remove raw SQL code sau khi verify

## 5. Migration Steps

### 5.1 Cho mỗi Service

#### Step 1: Tạo Stored Procedures
1. Viết stored procedure trong SQL file
2. Test stored procedure trực tiếp trong MySQL
3. Verify với các edge cases
4. Document parameters và return values

#### Step 2: Update Python Code
1. Create helper function để call stored procedure
2. Replace raw SQL với stored procedure call
3. Handle errors và return values
4. Keep backward compatibility nếu cần

#### Step 3: Testing
1. Unit tests cho stored procedures (nếu có)
2. Integration tests cho Python code
3. Test với real data
4. Performance testing

#### Step 4: Deployment
1. Deploy SQL scripts trước
2. Deploy Python code sau
3. Monitor for errors
4. Rollback plan nếu cần

### 5.2 Migration Order

**Priority 1 (High Impact):**
1. User operations (register, authenticate, get_user)
2. Billing operations (approve_payment, create_payment)

**Priority 2 (Medium Impact):**
3. API key operations (create, validate, list)
4. Subscription operations (get, change_tier)

**Priority 3 (Low Impact):**
5. Logging operations (log_request, get_logs)
6. Usage statistics (aggregation queries)

## 6. Risks & Mitigation

### 6.1 Risks

#### 6.1.1 Breaking Changes
- **Risk**: Stored procedures có thể break existing functionality
- **Mitigation**: 
  - Test thoroughly trước khi deploy
  - Phase migration (support cả old và new)
  - Rollback plan

#### 6.1.2 Performance Issues
- **Risk**: Stored procedures có thể slower nếu không optimize
- **Mitigation**:
  - Benchmark trước và sau migration
  - Optimize queries trong stored procedures
  - Use EXPLAIN để analyze

#### 6.1.3 Database Lock
- **Risk**: Deploy stored procedures có thể lock database
- **Mitigation**:
  - Deploy trong maintenance window
  - Use online DDL nếu MySQL version hỗ trợ
  - Test trên staging environment trước

#### 6.1.4 Debugging Difficulty
- **Risk**: Khó debug stored procedures hơn Python code
- **Mitigation**:
  - Comprehensive logging trong stored procedures
  - Good error messages
  - Documentation đầy đủ

### 6.2 Rollback Plan
- Keep old Python code trong git history
- Deploy SQL scripts có thể rollback
- Feature flag để switch giữa old và new implementation
- Database backup trước khi deploy

## 7. Success Criteria

### 7.1 Functional
- ✅ Tất cả functionality hoạt động như cũ
- ✅ No regression trong tests
- ✅ Backward compatibility maintained (nếu cần)

### 7.2 Performance
- ✅ Query performance >= current performance
- ✅ Reduced query execution time
- ✅ Better database connection usage

### 7.3 Code Quality
- ✅ Less SQL code trong Python
- ✅ Better separation of concerns
- ✅ Easier to maintain và update

### 7.4 Documentation
- ✅ Stored procedures documented
- ✅ Migration guide created
- ✅ API documentation updated

## 8. Timeline Estimate

### Phase 1: Preparation
- **Duration**: 1-2 tuần
- **Tasks**: Schema review, documentation, testing strategy

### Phase 2: Core Operations
- **Duration**: 3-4 tuần
- **Tasks**: User operations, billing operations

### Phase 3: Supporting Operations
- **Duration**: 2-3 tuần
- **Tasks**: API key operations, logging operations

### Phase 4: Optimization
- **Duration**: 1-2 tuần
- **Tasks**: Query optimization, performance tuning

**Total**: ~8-12 tuần

## 9. Tools & Resources

### 9.1 Tools
- MySQL Workbench - để viết và test stored procedures
- MySQL CLI - để execute SQL scripts
- Python MySQL connector - để call stored procedures
- Testing framework - để test stored procedures

### 9.2 Documentation
- MySQL Stored Procedures documentation
- Best practices cho stored procedures
- Performance tuning guides

### 9.3 Team Skills
- SQL stored procedures knowledge
- MySQL administration
- Testing strategies
- Performance optimization

## 10. Next Steps

1. **Review và Approve Plan**: Review kế hoạch này với team
2. **Setup Environment**: Setup test database cho stored procedures
3. **POC (Proof of Concept)**: Implement 1-2 stored procedures để validate approach
4. **Start Phase 1**: Begin với preparation phase
5. **Iterative Migration**: Migrate từng service một, test thoroughly

---

**Lưu ý**: 
- Đây là kế hoạch tổng quan, chi tiết implementation sẽ được update trong từng phase
- Priority có thể thay đổi dựa trên business needs
- Timeline là estimate, có thể điều chỉnh dựa trên complexity
