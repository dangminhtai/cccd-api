# Kế Hoạch Clean Code & Module Organization

## 📋 Tổng Quan

Hiện tại, một số file trong dự án có >500-1000 dòng code, gây khó khăn cho việc đọc, maintain và test. Kế hoạch này đề xuất refactor codebase để đạt được:
- **Readability**: Code dễ đọc, dễ hiểu
- **Maintainability**: Dễ bảo trì, dễ sửa lỗi
- **Testability**: Dễ viết unit tests
- **Scalability**: Dễ mở rộng, thêm features mới

---

## 🔍 Phân Tích Hiện Trạng

### File Size Analysis

| File | Lines | Status | Priority |
|------|-------|--------|----------|
| `services/user_service.py` | 712 | ❌ Too Long | High |
| `services/billing_service.py` | 556 | ❌ Too Long | High |
| `services/api_key_service.py` | ~589 | ❌ Too Long | High |
| `app/templates/admin.html` | 990 | ❌ Too Long | Medium |
| `services/logging_service.py` | ~200 | ✅ OK | Low |
| `services/usage_service.py` | ~200 | ✅ OK | Low |

### Best Practices

- **Python file**: Nên <= 300-500 dòng
- **Function**: Nên <= 50-100 dòng
- **Class**: Nên <= 200-300 dòng
- **Template**: Nên <= 300-400 dòng

---

## 🎯 Mục Tiêu Refactor

### 1. Code Organization

**Current Structure:**
```
services/
  ├── user_service.py (712 lines) ❌
  ├── billing_service.py (556 lines) ❌
  ├── api_key_service.py (589 lines) ❌
  └── ...
```

**Target Structure:**
```
services/
  ├── user/
  │   ├── __init__.py
  │   ├── models.py          # Data models (dataclasses)
  │   ├── repository.py      # Database queries (raw SQL)
  │   ├── service.py         # Business logic
  │   ├── validators.py      # Input validation
  │   └── utils.py           # Helper functions
  ├── billing/
  │   ├── __init__.py
  │   ├── models.py
  │   ├── repository.py
  │   ├── service.py
  │   └── validators.py
  ├── api_key/
  │   ├── __init__.py
  │   ├── models.py
  │   ├── repository.py
  │   ├── service.py
  │   └── utils.py
  └── ...
```

### 2. Separation of Concerns

**Repository Layer** (`repository.py`):
- Raw SQL queries
- Database connections
- Data mapping (dict → model)
- Error handling cho database operations

**Service Layer** (`service.py`):
- Business logic
- Validation (gọi validators)
- Transaction management
- Orchestration (gọi repository)

**Model Layer** (`models.py`):
- Data models (dataclasses/Pydantic)
- Type hints
- Data validation

**Utils Layer** (`utils.py`):
- Helper functions (hash_password, generate_token, etc.)
- Pure functions (no side effects)
- Reusable utilities

**Validators Layer** (`validators.py`):
- Input validation
- Business rules validation
- Error messages

---

## 📐 Module Organization Strategy

### Strategy 1: Domain-Based (Recommended)

Chia theo domain (user, billing, api_key):

**Pros:**
- Dễ tìm code liên quan
- Clear ownership
- Dễ scale khi domain lớn lên

**Cons:**
- Có thể có duplicate code giữa domains
- Cần shared utilities

### Strategy 2: Layer-Based

Chia theo layers (models, repositories, services):

**Pros:**
- Clear separation of concerns
- Dễ test từng layer

**Cons:**
- Khó tìm code liên quan đến 1 domain
- File structure phức tạp hơn

**Recommendation**: Dùng **Domain-Based** vì phù hợp với Flask app structure.

---

## 🔄 Refactoring Plan

### Phase 1: User Service Refactoring (Priority: High)

**Current:** `services/user_service.py` (712 lines)

**Target Structure:**
```
services/user/
  ├── __init__.py           # Public API exports
  ├── models.py             # User, Subscription models (~100 lines)
  ├── repository.py         # Database queries (~200 lines)
  ├── service.py            # Business logic (~200 lines)
  ├── validators.py         # Input validation (~100 lines)
  └── utils.py              # Helper functions (~100 lines)
```

**Functions Mapping:**

**`models.py`** (Data Models):
- `User` dataclass
- `Subscription` dataclass
- `PasswordResetToken` dataclass
- `EmailVerificationToken` dataclass

**`repository.py`** (Database Queries):
- `create_user()` - INSERT user
- `get_user_by_id()` - SELECT user by ID
- `get_user_by_email()` - SELECT user by email
- `get_users_list()` - SELECT users with pagination
- `update_user()` - UPDATE user
- `delete_user()` - DELETE user
- `create_subscription()` - INSERT subscription
- `get_user_subscription()` - SELECT subscription
- `update_subscription()` - UPDATE subscription
- `create_password_reset_token()` - INSERT token
- `get_password_reset_token()` - SELECT token
- `delete_password_reset_token()` - DELETE token
- `create_email_verification_token()` - INSERT token
- `get_email_verification_token()` - SELECT token
- `update_email_verified()` - UPDATE email_verified

**`service.py`** (Business Logic):
- `register_user()` - Registration flow (gọi repository + validation)
- `authenticate_user()` - Login flow (gọi repository + password verify)
- `get_user()` - Get user (wrapper)
- `update_user()` - Update user (wrapper + validation)
- `delete_user()` - Delete user (wrapper + cascade logic)
- `request_password_reset()` - Password reset request (gọi repository + email)
- `reset_password()` - Reset password (gọi repository + validation)
- `verify_email()` - Email verification (gọi repository + update)
- `resend_verification_email()` - Resend verification (gọi repository + email)

**`validators.py`** (Input Validation):
- `validate_email()` - Email format + length
- `validate_password()` - Password strength + length
- `validate_full_name()` - Name format + length
- `validate_user_id()` - User ID format

**`utils.py`** (Helper Functions):
- `hash_password()` - Bcrypt hash
- `verify_password()` - Bcrypt verify
- `generate_verification_token()` - Generate token
- `generate_password_reset_token()` - Generate token

**`__init__.py`** (Public API):
```python
from .service import (
    register_user,
    authenticate_user,
    get_user_by_id,
    get_user_by_email,
    get_users_list,
    delete_user,
    request_password_reset,
    reset_password,
    verify_email,
    resend_verification_email,
)
from .models import User, Subscription

__all__ = [
    # Service functions
    "register_user",
    "authenticate_user",
    # ... other functions
    # Models
    "User",
    "Subscription",
]
```

**Migration Steps:**
1. Tạo folder `services/user/`
2. Tạo `models.py` với dataclasses
3. Tạo `repository.py` với database queries
4. Tạo `utils.py` với helper functions
5. Tạo `validators.py` với validation logic
6. Tạo `service.py` với business logic (gọi repository + validators)
7. Tạo `__init__.py` với public API exports
8. Update imports trong routes (từ `services.user_service` → `services.user`)
9. Test thoroughly
10. Delete old `user_service.py`

### Phase 2: Billing Service Refactoring (Priority: High)

**Current:** `services/billing_service.py` (556 lines)

**Target Structure:**
```
services/billing/
  ├── __init__.py
  ├── models.py             # Payment, Subscription models
  ├── repository.py         # Database queries
  ├── service.py            # Business logic
  └── validators.py         # Input validation
```

**Functions Mapping:**

**`models.py`**:
- `Payment` dataclass
- `Subscription` dataclass (hoặc reuse từ user models)
- `TierPricing` dataclass

**`repository.py`**:
- `create_payment()` - INSERT payment
- `get_payment_by_id()` - SELECT payment
- `get_pending_payments()` - SELECT pending payments
- `get_user_payments()` - SELECT user payments
- `update_payment_status()` - UPDATE payment status
- `create_subscription()` - INSERT subscription
- `get_user_subscription()` - SELECT subscription
- `update_subscription()` - UPDATE subscription
- `expire_old_subscriptions()` - UPDATE subscriptions

**`service.py`**:
- `create_payment()` - Create payment (gọi repository + validation)
- `approve_payment()` - Approve payment (transaction logic)
- `reject_payment()` - Reject payment (wrapper)
- `get_pending_payments()` - Get pending payments (wrapper)
- `get_user_payments()` - Get user payments (wrapper)
- `manually_change_user_tier()` - Change tier (transaction logic)
- `get_tier_pricing()` - Get pricing (config data)
- `has_pending_payment()` - Check pending (wrapper)

**`validators.py`**:
- `validate_tier()` - Tier validation
- `validate_payment_amount()` - Amount validation
- `validate_currency()` - Currency validation

**Migration Steps:**
1. Tương tự Phase 1
2. Note: `Subscription` model có thể reuse từ `user.models` hoặc tách riêng

### Phase 3: API Key Service Refactoring (Priority: High)

**Current:** `services/api_key_service.py` (~589 lines)

**Target Structure:**
```
services/api_key/
  ├── __init__.py
  ├── models.py             # APIKey, APIKeyHistory models
  ├── repository.py         # Database queries
  ├── service.py            # Business logic
  └── utils.py              # Key generation, hashing
```

**Functions Mapping:**

**`models.py`**:
- `APIKey` dataclass
- `APIKeyInfo` dataclass (hoặc reuse APIKey)
- `APIKeyHistory` dataclass
- `UsageStats` dataclass

**`repository.py`**:
- `create_api_key()` - INSERT api_key
- `get_api_key_by_hash()` - SELECT by hash
- `get_api_key_by_id()` - SELECT by ID
- `get_user_api_keys()` - SELECT user keys
- `update_api_key()` - UPDATE key (label, active, expires_at)
- `delete_api_key()` - DELETE key
- `create_key_history()` - INSERT history
- `get_key_history()` - SELECT history
- `get_key_usage_stats()` - SELECT usage stats

**`service.py`**:
- `create_api_key()` - Create key (gọi repository + generation)
- `validate_api_key()` - Validate key (gọi repository + hash)
- `get_user_api_keys()` - Get keys (wrapper)
- `update_key_label()` - Update label (gọi repository + history)
- `delete_key_by_id()` - Delete key (gọi repository + history)
- `get_usage_stats()` - Get stats (wrapper)

**`utils.py`**:
- `generate_api_key()` - Generate key with prefix
- `hash_key()` - SHA256 hash
- `get_rate_limit_for_tier()` - Rate limit config

**Migration Steps:**
1. Tương tự Phase 1 và 2

### Phase 4: Template Refactoring (Priority: Medium)

**Current:** `app/templates/admin.html` (990 lines)

**Target Structure:**
```
app/templates/admin/
  ├── base.html             # Admin base template
  ├── dashboard.html        # Main dashboard content
  ├── components/
  │   ├── admin_key_input.html
  │   ├── pending_payments.html
  │   ├── user_list.html
  │   └── stats.html
  └── scripts/
      └── admin.js          # JavaScript code
```

**Refactoring Strategy:**
- Extract components: Pending Payments, User List, Stats sections
- Move JavaScript to separate file
- Use template includes: `{% include "admin/components/pending_payments.html" %}`

**Migration Steps:**
1. Tạo folder `app/templates/admin/`
2. Extract components thành separate files
3. Move JavaScript to `static/js/admin.js`
4. Update main template để dùng includes
5. Test thoroughly

### Phase 5: Shared Utilities (Priority: Low)

**Current:** Duplicate code giữa services (database connection, etc.)

**Target Structure:**
```
services/
  ├── shared/
  │   ├── __init__.py
  │   ├── database.py       # Database connection pool
  │   └── exceptions.py     # Custom exceptions
  └── ...
```

**Functions:**
- `get_db_connection()` - Centralized database connection
- `CustomException` classes - Custom exceptions

---

## ✅ Best Practices

### 1. File Size Guidelines

- **Python file**: <= 300-500 dòng
- **Function**: <= 50-100 dòng
- **Class**: <= 200-300 dòng
- **Template**: <= 300-400 dòng

### 2. Module Organization

- **Domain-based**: Chia theo domain (user, billing, api_key)
- **Single Responsibility**: Mỗi module chỉ làm 1 việc
- **Clear naming**: File names rõ ràng, dễ hiểu

### 3. Code Structure

- **Repository**: Raw SQL queries, database operations
- **Service**: Business logic, orchestration
- **Models**: Data models, type hints
- **Validators**: Input validation
- **Utils**: Helper functions, pure functions

### 4. Import Organization

- **Public API**: Export qua `__init__.py`
- **Internal imports**: Dùng relative imports trong module
- **External imports**: Standard library → Third-party → Local

### 5. Testing Strategy

- **Unit tests**: Test từng function riêng lẻ
- **Integration tests**: Test service + repository
- **Test organization**: Mirror source structure

---

## 📊 Success Metrics

### Code Quality
- ✅ All files <= 500 lines
- ✅ Functions <= 100 lines
- ✅ No duplicate code (DRY)
- ✅ Clear separation of concerns

### Maintainability
- ✅ Easy to find code (domain-based structure)
- ✅ Easy to add new features
- ✅ Easy to fix bugs
- ✅ Easy to test

### Performance
- ✅ No performance regression
- ✅ Same or better performance

### Documentation
- ✅ Module documentation
- ✅ Function docstrings
- ✅ Type hints

---

## 🚀 Migration Timeline

### Phase 1: User Service (1-2 tuần)
- Setup structure
- Refactor user service
- Test và verify

### Phase 2: Billing Service (1 tuần)
- Refactor billing service
- Test và verify

### Phase 3: API Key Service (1 tuần)
- Refactor API key service
- Test và verify

### Phase 4: Template Refactoring (1 tuần)
- Refactor admin template
- Test và verify

### Phase 5: Shared Utilities (1 tuần)
- Extract shared utilities
- Update imports
- Test và verify

**Total**: ~5-6 tuần

---

## ⚠️ Risks & Mitigation

### Risk 1: Breaking Changes
**Mitigation:**
- Test thoroughly sau mỗi phase
- Keep old code trong git history
- Gradual migration (không refactor hết cùng lúc)

### Risk 2: Import Errors
**Mitigation:**
- Update imports từng bước
- Use IDE refactoring tools
- Test imports sau mỗi change

### Risk 3: Performance Regression
**Mitigation:**
- Benchmark before/after
- No changes to SQL queries (chỉ reorganize code)
- Monitor performance

---

## 📝 Next Steps

1. **Review và approve** kế hoạch này
2. **Start Phase 1**: Refactor user service
3. **Test thoroughly** sau mỗi phase
4. **Document changes** trong commit messages
5. **Continue** với các phases tiếp theo

---

## 💡 Lưu Ý

- **Không cần refactor hết cùng lúc**: Làm từng module một
- **Test kỹ trước khi merge**: Đảm bảo không break existing functionality
- **Gradual migration**: Có thể chạy song song old/new code trong transition period
- **Document changes**: Ghi rõ trong commit messages và PR descriptions
