# Implementation Roadmap - Priority Features

Tài liệu này track việc triển khai các tính năng ưu tiên đã được chốt.

---

## 🎯 Các tính năng đã chốt triển khai

1. ✅ **Email System** - CRITICAL
2. ✅ **Password Reset & Account Recovery** - CRITICAL
3. ✅ **Email Verification** - CRITICAL
4. ✅ **API Key Rotation & Management** - CRITICAL
5. ✅ **API Documentation** - HIGH PRIORITY
6. ✅ **Audit Logging** - HIGH PRIORITY
7. ✅ **API Key Scopes/Permissions** - MEDIUM PRIORITY
8. ✅ **Advanced Security** - LOW PRIORITY

---

## 📋 Implementation Plan

### Phase 1: Email System & Authentication (Foundation)

#### 1.1 Email System Setup
**Status:** ✅ **COMPLETED**  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 3-5 days  
**Actual Time:** 1 day

**Tasks:**
- [x] Chọn email service provider: SMTP ✅
- [x] Cài đặt email library (SMTP với built-in Python libraries) ✅
- [x] Tạo `services/email_service.py` ✅
- [x] Cấu hình email templates (HTML) ✅
- [x] Test email sending (có test script `scripts/test_email.py`) ✅
- [x] Environment variables cho email config ✅

**Files created:**
- ✅ `services/email_service.py` - SMTP email service với singleton pattern
- ✅ `app/templates/emails/base.html` - Base email template
- ✅ `app/templates/emails/welcome.html` - Welcome email template
- ✅ `app/templates/emails/verification.html` - Email verification template
- ✅ `app/templates/emails/password_reset.html` - Password reset template
- ✅ `scripts/test_email.py` - Test script để verify email sending
- ✅ Updated `.env.example` với SMTP configuration
- ✅ Updated `app/config.py` với email settings

**Verification:**
- ✅ Code implemented và tested
- ✅ Email service supports SMTP (Gmail, Outlook, etc.)
- ✅ Email templates created với HTML styling
- ✅ Test script available
- ✅ Environment variables documented
- ✅ Configuration updated in app/config.py
- ⚠️ **Note:** User cần test với SMTP credentials thực tế để verify production readiness

---

#### 1.2 Email Verification
**Status:** ✅ **COMPLETED**  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2-3 days  
**Actual Time:** 1 day  
**Dependencies:** Email System (1.1) ✅

**Tasks:**
- [x] Thêm `email_verified` column vào `users` table ✅
- [x] Thêm `verification_token` column vào `users` table ✅
- [x] Thêm `verification_token_expires` column ✅
- [x] Generate verification token khi user đăng ký ✅
- [x] Send verification email với link ✅
- [x] Tạo route `/portal/verify-email/<token>` ✅
- [x] Block user chưa verify (không thể tạo API key) ✅
- [x] Resend verification email functionality ✅
- [x] Update registration flow để show verification message ✅
- [x] Update dashboard và keys page để show verification warning ✅

**Files created/modified:**
- ✅ `scripts/db_schema_email_verification.sql` - Database migration script
- ✅ `services/user_service.py` - Added `generate_verification_token()`, `verify_email()`, `generate_new_verification_token()`
- ✅ `routes/portal.py` - Added `/portal/verify-email/<token>` and `/portal/resend-verification` routes
- ✅ `app/templates/portal/dashboard.html` - Added email verification warning
- ✅ `app/templates/portal/keys.html` - Added email verification warning and disabled form
- ✅ `app/templates/emails/verification.html` - Email template (already created in 1.1)

**Verification:**
- ✅ Database columns added (email_verified, verification_token, verification_token_expires)
- ✅ Verification token generated on registration (24h expiry)
- ✅ Verification email sent after registration
- ✅ Verification route works and updates database
- ✅ Unverified users blocked from creating API keys
- ✅ Resend verification email functionality
- ✅ UI warnings shown in dashboard and keys page
- ⚠️ **Note:** User cần run database migration script: `mysql -u root -p cccd_api < scripts/db_schema_email_verification.sql`

---

#### 1.3 Password Reset & Account Recovery
**Status:** ✅ **COMPLETED**  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2-3 days  
**Actual Time:** 1 day  
**Dependencies:** Email System (1.1) ✅

**Tasks:**
- [x] Thêm `password_reset_token` và `password_reset_expires` columns vào `users` table ✅
- [x] Tạo "Forgot Password" link trên login page ✅
- [x] Route `/portal/forgot-password` (GET/POST) ✅
- [x] Generate secure reset token (expires sau 1 giờ) ✅
- [x] Send reset email với link ✅
- [x] Route `/portal/reset-password/<token>` (GET/POST) ✅
- [x] Validate token và expiry ✅
- [x] Update password và clear token ✅
- [x] Rate limiting cho reset requests (max 3 requests/hour per email) ✅
- [x] Security: Invalidate all sessions sau khi reset password (placeholder) ✅

**Files created/modified:**
- ✅ `scripts/db_schema_password_reset.sql` - Database migration script
- ✅ `services/user_service.py` - Added `generate_password_reset_token()`, `request_password_reset()`, `reset_password()`, `invalidate_user_sessions()`
- ✅ `routes/portal.py` - Added `/portal/forgot-password` and `/portal/reset-password/<token>` routes
- ✅ `app/templates/portal/login.html` - Added "Forgot Password" link
- ✅ `app/templates/portal/forgot_password.html` - New template for forgot password form
- ✅ `app/templates/portal/reset_password.html` - New template for reset password form
- ✅ `app/templates/emails/password_reset.html` - Email template (already created in 1.1)

**Verification:**
- ✅ Database columns added (password_reset_token, password_reset_expires)
- ✅ Reset token generated on request (1h expiry)
- ✅ Reset email sent with link
- ✅ Reset route validates token and expiry
- ✅ Password updated and token cleared after reset
- ✅ Rate limiting applied (3/hour per email using Flask-Limiter)
- ✅ Security: Don't reveal if email exists
- ✅ Session invalidation placeholder implemented
- ⚠️ **Note:** User cần run database migration script: `mysql -u root -p cccd_api < scripts/db_schema_password_reset.sql`

---

### Phase 2: API Key Management

#### 2.1 API Key Rotation & Management
**Status:** ✅ COMPLETED  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 4-5 days  
**Actual Time:** ~4 days

**Tasks:**
- [x] Thêm `label` column vào `api_keys` table (để user đặt tên cho key)
- [x] Thêm `rotated_from` column (track key rotation)
- [x] API key rotation:
  - [x] Tạo key mới
  - [x] Set expiry cho key cũ (grace period 7 ngày)
  - [x] Link key mới với key cũ
- [x] Key management UI:
  - [x] Edit key label
  - [x] Suspend/Resume key (không xóa, chỉ tạm dừng)
  - [x] View key usage per key
  - [ ] Export keys (backup) - **Deferred to future**
- [x] Key expiration reminders:
  - [x] Email warning 7 ngày trước khi hết hạn
  - [x] Email warning 3 ngày trước khi hết hạn
  - [x] Email warning 1 ngày trước khi hết hạn
- [x] Key history (track changes) - **Implemented via `api_key_history` table**

**Files to modify:**
- `services/api_key_service.py` - add rotation functions
- `routes/portal.py` - add key management routes
- `app/templates/portal/keys.html` - enhance UI
- `scripts/db_schema.sql` - add columns

---

#### 2.2 API Key Scopes/Permissions
**Status:** ⏳ Pending  
**Priority:** 🟡 MEDIUM  
**Estimated Time:** 5-7 days

**Tasks:**
- [ ] Design scope system:
  - Scopes: `cccd:read`, `cccd:write`, `admin:read`, `admin:write`
  - Default scope: `cccd:read` (cho tất cả keys)
- [ ] Thêm `scopes` column vào `api_keys` table (JSON array)
- [ ] Thêm `ip_whitelist` column (JSON array)
- [ ] Thêm `allowed_domains` column (JSON array)
- [ ] Thêm `time_restrictions` column (JSON: `{"start": "09:00", "end": "18:00", "timezone": "Asia/Ho_Chi_Minh"}`)
- [ ] Update API key validation:
  - [ ] Check scopes khi request
  - [ ] Check IP whitelist
  - [ ] Check domain restrictions
  - [ ] Check time restrictions
- [ ] UI để configure scopes và restrictions
- [ ] Admin UI để manage scopes

**Files to modify:**
- `services/api_key_service.py` - add scope validation
- `routes/cccd.py` - add scope checking
- `routes/portal.py` - add scope configuration UI
- `app/templates/portal/keys.html` - add scope/restriction settings
- `scripts/db_schema.sql` - add columns

---

### Phase 3: Documentation & Monitoring

#### 3.1 API Documentation
**Status:** ⏳ Pending  
**Priority:** 🟠 HIGH  
**Estimated Time:** 5-7 days

**Tasks:**
- [ ] Setup Swagger/OpenAPI:
  - [ ] Install `flask-swagger-ui` hoặc `flasgger`
  - [ ] Create OpenAPI spec file
  - [ ] Add API endpoint `/api-docs` hoặc `/swagger`
- [ ] Document all endpoints:
  - [ ] `/v1/cccd/parse` - main endpoint
  - [ ] `/health` - health check
  - [ ] Portal endpoints (nếu cần)
- [ ] Code examples:
  - [ ] Python (requests library)
  - [ ] JavaScript (fetch API)
  - [ ] cURL
  - [ ] PHP
- [ ] SDK libraries:
  - [ ] Python SDK (priority)
  - [ ] Node.js SDK (optional)
- [ ] Postman collection:
  - [ ] Export Postman collection
  - [ ] Include examples
- [ ] Error codes reference:
  - [ ] Document all error codes
  - [ ] Error handling guide
- [ ] Rate limit documentation:
  - [ ] Explain rate limits per tier
  - [ ] Rate limit headers
  - [ ] Best practices

**Files to create:**
- `docs/api/` - API documentation
- `docs/api/openapi.yaml` - OpenAPI spec
- `docs/api/examples/` - code examples
- `sdk/python/` - Python SDK (optional)
- `postman/` - Postman collection

**Files to modify:**
- `app/__init__.py` - add Swagger UI
- `routes/cccd.py` - add API docstrings

---

#### 3.2 Audit Logging
**Status:** ⏳ Pending  
**Priority:** 🟠 HIGH  
**Estimated Time:** 4-5 days

**Tasks:**
- [ ] Design audit log schema:
  - Table: `audit_logs`
  - Columns: `id`, `user_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `user_agent`, `details` (JSON), `created_at`
- [ ] Create audit log service:
  - [ ] `services/audit_service.py`
  - [ ] Function `log_action(user_id, action, resource_type, resource_id, ip, user_agent, details)`
- [ ] Log user actions:
  - [ ] Login, Logout
  - [ ] Register
  - [ ] Change password
  - [ ] Update profile
  - [ ] Create API key
  - [ ] Delete API key
  - [ ] Rotate API key
  - [ ] Update subscription
- [ ] Log admin actions:
  - [ ] Approve payment
  - [ ] Create key for user
  - [ ] Deactivate key
  - [ ] View sensitive data
- [ ] Audit log UI:
  - [ ] Admin dashboard - view all audit logs
  - [ ] User dashboard - view own audit logs
  - [ ] Filter by action, date range, user
  - [ ] Export audit logs (CSV)
- [ ] Security alerts:
  - [ ] Alert on suspicious activities (nhiều failed logins, IP changes, etc.)
  - [ ] Email admin on critical actions

**Files to create:**
- `services/audit_service.py`
- `scripts/db_schema_audit.sql`
- `app/templates/admin/audit_logs.html`
- `app/templates/portal/audit_logs.html`

**Files to modify:**
- `routes/portal.py` - add audit logging
- `routes/admin.py` - add audit logging
- `services/user_service.py` - add audit logging
- `services/api_key_service.py` - add audit logging

---


**Files to create:**
- `services/security_service.py`
- `middleware/security.py` - security headers middleware
- `app/templates/security/` - security settings UI

**Files to modify:**
- `app/__init__.py` - add security middleware
- `routes/portal.py` - add CAPTCHA
- `routes/cccd.py` - add WAF checks

---

## 📊 Implementation Timeline

### Week 1-2: Email System & Authentication
- Email System Setup
- Email Verification
- Password Reset

### Week 3-4: API Key Management
- API Key Rotation
- API Key Scopes/Permissions

### Week 5-6: Documentation & Monitoring
- API Documentation
- Audit Logging

### Week 7-8: Advanced Security
- DDoS Protection
- WAF
- Bot Detection
- Security Headers

**Total Estimated Time:** 8 weeks (2 months)

---

## 🔧 Technical Stack

### Email Service
- **Recommended:** SendGrid (free tier: 100 emails/day)
- **Alternative:** Mailgun (free tier: 5,000 emails/month)
- **Library:** `sendgrid-python` hoặc `flask-mail`

### API Documentation
- **Recommended:** Flasgger (Flask + Swagger)
- **Alternative:** flask-swagger-ui
- **Format:** OpenAPI 3.0

### Audit Logging
- **Database:** MySQL (existing)
- **Format:** JSON for details column
- **Retention:** 90 days (configurable)

### Security
- **Rate Limiting:** Flask-Limiter (already in use)
- **CAPTCHA:** reCAPTCHA v3
- **WAF:** Custom middleware hoặc Cloudflare

---

## ✅ Definition of Done

Mỗi tính năng được coi là "Done" khi:
- [ ] Code implemented và tested
- [ ] Unit tests written (nếu có)
- [ ] Integration tests passed
- [ ] Documentation updated
- [ ] Database migrations created
- [ ] UI/UX completed
- [ ] Security review passed
- [ ] Deployed to staging environment
- [ ] User acceptance testing passed

---

## 📝 Notes

- **Email Service:** Bắt đầu với SMTP
- **API Documentation:** Bắt đầu với Swagger UI, sau đó có thể tạo custom docs page
- **Audit Logging:** Log tất cả actions, có thể optimize sau (archive old logs)
- **Security:** Implement từng layer, test kỹ trước khi deploy

---

*Last updated: 2026-01-10*
