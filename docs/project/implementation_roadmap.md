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
**Status:** ⏳ Pending  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2-3 days  
**Dependencies:** Email System (1.1)

**Tasks:**
- [ ] Thêm `email_verified` column vào `users` table
- [ ] Thêm `verification_token` column vào `users` table
- [ ] Generate verification token khi user đăng ký
- [ ] Send verification email với link
- [ ] Tạo route `/portal/verify-email/<token>`
- [ ] Block user chưa verify (không thể tạo API key)
- [ ] Resend verification email functionality
- [ ] Update registration flow để show verification message

**Files to modify:**
- `services/user_service.py` - add `generate_verification_token()`, `verify_email()`
- `routes/portal.py` - add verification routes
- `app/templates/portal/register.html` - show verification message
- `app/templates/emails/verification.html` - email template
- `scripts/db_schema_portal.sql` - add columns

---

#### 1.3 Password Reset & Account Recovery
**Status:** ⏳ Pending  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2-3 days  
**Dependencies:** Email System (1.1)

**Tasks:**
- [ ] Thêm `password_reset_token` và `password_reset_expires` columns vào `users` table
- [ ] Tạo "Forgot Password" link trên login page
- [ ] Route `/portal/forgot-password` (GET/POST)
- [ ] Generate secure reset token (expires sau 1 giờ)
- [ ] Send reset email với link
- [ ] Route `/portal/reset-password/<token>` (GET/POST)
- [ ] Validate token và expiry
- [ ] Update password và clear token
- [ ] Rate limiting cho reset requests (max 3 requests/hour per email)
- [ ] Security: Invalidate all sessions sau khi reset password

**Files to modify:**
- `services/user_service.py` - add `generate_reset_token()`, `reset_password()`
- `routes/portal.py` - add forgot/reset password routes
- `app/templates/portal/login.html` - add "Forgot Password" link
- `app/templates/portal/forgot_password.html` - new template
- `app/templates/portal/reset_password.html` - new template
- `app/templates/emails/password_reset.html` - email template
- `scripts/db_schema_portal.sql` - add columns

---

### Phase 2: API Key Management

#### 2.1 API Key Rotation & Management
**Status:** ⏳ Pending  
**Priority:** 🔴 CRITICAL  
**Estimated Time:** 4-5 days

**Tasks:**
- [ ] Thêm `label` column vào `api_keys` table (để user đặt tên cho key)
- [ ] Thêm `rotated_from` column (track key rotation)
- [ ] API key rotation:
  - [ ] Tạo key mới
  - [ ] Set expiry cho key cũ (grace period 7 ngày)
  - [ ] Link key mới với key cũ
- [ ] Key management UI:
  - [ ] Edit key label
  - [ ] Suspend/Resume key (không xóa, chỉ tạm dừng)
  - [ ] View key usage per key
  - [ ] Export keys (backup)
- [ ] Key expiration reminders:
  - [ ] Email warning 7 ngày trước khi hết hạn
  - [ ] Email warning 3 ngày trước khi hết hạn
  - [ ] Email warning 1 ngày trước khi hết hạn
- [ ] Key history (track changes)

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

### Phase 4: Advanced Security

#### 4.1 Advanced Security Features
**Status:** ⏳ Pending  
**Priority:** 🔵 LOW  
**Estimated Time:** 7-10 days

**Tasks:**
- [ ] DDoS Protection:
  - [ ] Rate limiting per IP (global)
  - [ ] IP-based blocking (temporary ban)
  - [ ] Request size limits
- [ ] WAF (Web Application Firewall):
  - [ ] SQL injection detection
  - [ ] XSS detection
  - [ ] Path traversal detection
  - [ ] Use library như `flask-limiter` hoặc Cloudflare
- [ ] IP Reputation Checking:
  - [ ] Check IP against blacklists
  - [ ] Block known malicious IPs
  - [ ] Optional: Integrate với services như AbuseIPDB
- [ ] Bot Detection:
  - [ ] CAPTCHA cho sensitive operations (password reset, payment)
  - [ ] reCAPTCHA v3 integration
  - [ ] Behavioral analysis (detect bot patterns)
- [ ] Security Headers:
  - [ ] CSP (Content Security Policy)
  - [ ] HSTS (HTTP Strict Transport Security)
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Referrer-Policy
- [ ] Security Monitoring:
  - [ ] Log security events
  - [ ] Alert on suspicious patterns
  - [ ] Security dashboard

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

- **Email Service:** Bắt đầu với SendGrid free tier, upgrade khi cần
- **API Documentation:** Bắt đầu với Swagger UI, sau đó có thể tạo custom docs page
- **Audit Logging:** Log tất cả actions, có thể optimize sau (archive old logs)
- **Security:** Implement từng layer, test kỹ trước khi deploy

---

*Last updated: 2026-01-10*
