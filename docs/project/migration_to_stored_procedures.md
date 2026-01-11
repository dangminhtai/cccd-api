# Kế Hoạch Migration: Chuyển SQL Queries Sang Stored Procedures & Functions

## Tổng Quan

Hiện tại, dự án đang sử dụng **hardcoded SQL queries** trong Python code (services layer). Kế hoạch này đề xuất chuyển đổi sang **MySQL Stored Procedures và Functions** để:
- Tăng hiệu suất (queries được compile và cache)
- Tăng bảo mật (giảm SQL injection risks)
- Dễ bảo trì (logic tập trung ở database layer)
- Tái sử dụng code (có thể gọi từ nhiều nơi)

## Phân Tích Hiện Trạng

### 1. Services Layer Hiện Tại

#### `services/user_service.py`
- **Số lượng queries**: ~15-20 queries
- **Các operations chính**:
  - User registration (`register_user`)
  - User authentication (`authenticate_user`)
  - Get user by ID/email (`get_user_by_id`, `get_user_by_email`)
  - Get users list với pagination (`get_users_list`)
  - Password reset (`request_password_reset`, `reset_password`)
  - Email verification (`verify_email`, `resend_verification_email`)
  - Delete user (`delete_user`)

#### `services/billing_service.py`
- **Số lượng queries**: ~10-15 queries
- **Các operations chính**:
  - Create payment (`create_payment`)
  - Approve payment (`approve_payment`)
  - Get pending payments (`get_pending_payments`)
  - Get user payments (`get_user_payments`)
  - Manually change tier (`manually_change_user_tier`)
  - Get tier pricing (`get_tier_pricing`)

#### `services/api_key_service.py`
- **Số lượng queries**: ~8-12 queries
- **Các operations chính**:
  - Create API key (`create_api_key`)
  - Get user API keys (`get_user_api_keys`)
  - Validate API key (`validate_api_key`)
  - Update key label (`update_key_label`)
  - Delete key (`delete_key_by_id`)
  - Get key usage stats (`get_key_usage_stats`)

#### `services/logging_service.py`
- **Số lượng queries**: ~3-5 queries
- **Các operations chính**:
  - Log request to database (`log_request_to_database`)
  - Get usage statistics

### 2. Vấn Đề Hiện Tại

#### Performance Issues
- Mỗi query phải được parse và compile mỗi lần execute
- Không có query plan caching
- Network overhead cho mỗi query statement

#### Security Concerns
- SQL injection risks (dù đã dùng parameterized queries)
- Business logic exposed trong application code
- Khó audit và track database changes

#### Maintenance Challenges
- SQL queries rải rác trong nhiều files
- Khó thay đổi schema mà không sửa code
- Khó optimize queries mà không touch application code
- Backward compatibility issues (try/except cho optional columns)

#### Code Duplication
- Similar queries ở nhiều nơi (ví dụ: get user subscription)
- Logic phức tạp lặp lại (ví dụ: pagination, search)

## Kế Hoạch Migration

### Phase 1: Thiết Kế Database Layer (1-2 tuần)

#### 1.1 Phân Loại Queries

**Stored Procedures** (cho operations có side effects):
- `sp_user_register` - Đăng ký user mới
- `sp_user_authenticate` - Xác thực login
- `sp_user_change_tier` - Admin đổi tier user
- `sp_user_delete` - Xóa user
- `sp_payment_create` - Tạo payment request
- `sp_payment_approve` - Admin approve payment
- `sp_payment_reject` - Admin reject payment
- `sp_api_key_create` - Tạo API key mới
- `sp_api_key_delete` - Xóa API key
- `sp_api_key_update_label` - Update label
- `sp_request_log` - Log API request

**Stored Functions** (cho read-only operations):
- `fn_get_user_by_id` - Lấy user theo ID
- `fn_get_user_by_email` - Lấy user theo email
- `fn_get_users_list` - Lấy danh sách users (pagination)
- `fn_get_user_subscription` - Lấy subscription hiện tại
- `fn_get_pending_payments` - Lấy pending payments
- `fn_get_user_payments` - Lấy payments của user
- `fn_validate_api_key` - Validate API key
- `fn_get_key_usage_stats` - Lấy usage statistics

**Views** (cho complex queries):
- `vw_user_subscriptions` - User với subscription info
- `vw_api_key_stats` - API key statistics
- `vw_payment_summary` - Payment summary

#### 1.2 Thiết Kế Parameters & Return Values

**Ví dụ cho Stored Procedure:**
```sql
-- Input: email, password_hash, full_name
-- Output: user_id, verification_token, success_flag, error_message
```

**Ví dụ cho Stored Function:**
```sql
-- Input: user_id
-- Output: JSON object với user info + subscription
```

### Phase 2: Tạo Stored Procedures & Functions (2-3 tuần)

#### 2.1 Priority Order

**High Priority** (dùng nhiều, performance critical):
1. `sp_user_authenticate` - Login được gọi mỗi request
2. `fn_validate_api_key` - Validate key được gọi mỗi API request
3. `sp_request_log` - Logging được gọi mỗi API call
4. `fn_get_user_subscription` - Get tier cho rate limiting

**Medium Priority** (dùng thường xuyên):
5. `sp_user_register` - Registration flow
6. `sp_payment_approve` - Admin operations
7. `fn_get_users_list` - Admin dashboard
8. `fn_get_pending_payments` - Admin dashboard

**Low Priority** (dùng ít):
9. `sp_user_change_tier` - Admin operations
10. `sp_user_delete` - Admin operations
11. Các functions khác

#### 2.2 Migration Strategy

**Approach 1: Big Bang** (không khuyến nghị)
- Tạo tất cả procedures/functions cùng lúc
- Thay đổi toàn bộ application code
- Risk cao, khó rollback

**Approach 2: Incremental** (khuyến nghị)
- Tạo procedure/function cho 1 operation
- Update application code để dùng procedure
- Test kỹ trước khi tiếp tục
- Repeat cho từng operation

**Approach 3: Parallel** (an toàn nhất)
- Tạo procedure/function mới
- Giữ code cũ hoạt động
- Thêm feature flag để switch
- Test với procedure mới
- Khi stable, remove code cũ

### Phase 3: Update Application Code (2-3 tuần)

#### 3.1 Tạo Database Service Layer

**File mới: `services/db_procedures.py`**
- Wrapper functions để gọi stored procedures
- Error handling và logging
- Type hints và documentation
- Backward compatibility layer

**Ví dụ structure:**
```python
# services/db_procedures.py
def call_user_register(email, password_hash, full_name):
    """Wrapper để gọi sp_user_register"""
    # Call procedure
    # Handle errors
    # Return formatted result
```

#### 3.2 Migration Path cho Mỗi Service

**Step 1**: Tạo procedure/function trong database
**Step 2**: Tạo wrapper function trong `db_procedures.py`
**Step 3**: Update service function để dùng wrapper
**Step 4**: Test thoroughly
**Step 5**: Remove old SQL code

#### 3.3 Backward Compatibility

- Giữ old functions hoạt động trong transition period
- Feature flag để switch giữa old/new implementation
- Gradual migration (migrate 1 service at a time)

### Phase 4: Testing & Optimization (1-2 tuần)

#### 4.1 Testing Strategy

**Unit Tests:**
- Test từng stored procedure/function
- Test error cases
- Test edge cases

**Integration Tests:**
- Test application code với procedures
- Test transaction handling
- Test concurrent access

**Performance Tests:**
- Benchmark old vs new implementation
- Test với high load
- Monitor query execution time

#### 4.2 Optimization

- Analyze query execution plans
- Add indexes nếu cần
- Optimize procedure logic
- Cache results nếu phù hợp

### Phase 5: Documentation & Rollout (1 tuần)

#### 5.1 Documentation

- Document tất cả stored procedures/functions
- Parameter descriptions
- Return value formats
- Error codes và meanings
- Usage examples

#### 5.2 Rollout Plan

- Deploy procedures/functions to staging
- Test với production-like data
- Gradual rollout to production
- Monitor performance và errors
- Rollback plan nếu có issues

## Lợi Ích Dự Kiến

### Performance
- **Query caching**: Procedures được compile và cache
- **Reduced network traffic**: 1 call thay vì nhiều queries
- **Optimized execution plans**: Database optimizer có thể optimize tốt hơn

### Security
- **SQL injection protection**: Parameters được validate ở database level
- **Access control**: Có thể set permissions cho procedures
- **Audit trail**: Dễ track database operations

### Maintainability
- **Centralized logic**: Business logic ở database layer
- **Schema changes**: Dễ update mà không touch application code
- **Version control**: Procedures có thể version

### Reusability
- **Multiple applications**: Có thể dùng procedures từ nhiều apps
- **API consistency**: Đảm bảo logic nhất quán
- **Testing**: Dễ test procedures độc lập

## Rủi Ro & Giảm Thiểu

### Rủi Ro 1: Vendor Lock-in
- **Vấn đề**: Stored procedures là MySQL-specific, khó migrate sang database khác
- **Giảm thiểu**: 
  - Chỉ dùng procedures cho business logic
  - Giữ application code database-agnostic
  - Có migration plan nếu cần đổi database

### Rủi Ro 2: Debugging Khó Khăn
- **Vấn đề**: Debug stored procedures khó hơn application code
- **Giảm thiểu**:
  - Comprehensive logging trong procedures
  - Good error messages
  - Debug tools và techniques

### Rủi Ro 3: Version Control
- **Vấn đề**: Procedures không nằm trong Git (phải export/import)
- **Giảm thiểu**:
  - Tạo migration scripts cho procedures
  - Version control cho SQL files
  - Automated deployment

### Rủi Ro 4: Testing Complexity
- **Vấn đề**: Test procedures cần database setup
- **Giảm thiểu**:
  - Test database với sample data
  - Automated tests
  - Integration test suite

## Timeline Tổng Thể

- **Week 1-2**: Phase 1 - Thiết kế database layer
- **Week 3-5**: Phase 2 - Tạo stored procedures/functions (high priority)
- **Week 6-8**: Phase 3 - Update application code (incremental)
- **Week 9-10**: Phase 4 - Testing & optimization
- **Week 11**: Phase 5 - Documentation & rollout

**Tổng thời gian**: ~11 tuần (2.5-3 tháng)

## Success Metrics

- **Performance**: Giảm 20-30% query execution time
- **Code reduction**: Giảm 30-40% SQL code trong application
- **Maintainability**: Dễ update schema mà không sửa code
- **Security**: Zero SQL injection vulnerabilities
- **Test coverage**: 90%+ test coverage cho procedures

## Next Steps

1. **Review và approve** kế hoạch này
2. **Setup test database** để develop procedures
3. **Bắt đầu Phase 1**: Thiết kế procedures cho high-priority operations
4. **Create migration scripts** để version control procedures
5. **Implement first procedure** (ví dụ: `sp_user_authenticate`) như proof of concept

## Notes

- **Không bắt buộc migrate tất cả**: Có thể chỉ migrate các operations quan trọng
- **Hybrid approach**: Có thể giữ một số queries trong code, dùng procedures cho complex operations
- **Gradual migration**: Không cần migrate hết cùng lúc, có thể làm từng phần
- **Backward compatibility**: Đảm bảo không break existing functionality
