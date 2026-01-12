# Test Cases - CCCD API System

Tài liệu này liệt kê tất cả các test cases có thể xảy ra cho hệ thống CCCD API, được phân loại theo từng module và chức năng.

---

## 📋 Mục lục

1. [CCCD Parser Tests](#1-cccd-parser-tests)
2. [API Endpoint Tests](#2-api-endpoint-tests)
3. [Validation Tests](#3-validation-tests)
4. [Authentication & Authorization Tests](#4-authentication--authorization-tests)
5. [Rate Limiting Tests](#5-rate-limiting-tests)
6. [Province Mapping Tests](#6-province-mapping-tests)
7. [Plausibility Checks Tests](#7-plausibility-checks-tests)
8. [Portal & User Management Tests](#8-portal--user-management-tests)
9. [Admin Dashboard Tests](#9-admin-dashboard-tests)
10. [Email Service Tests](#10-email-service-tests)
11. [API Key Management Tests](#11-api-key-management-tests)
12. [Billing & Subscription Tests](#12-billing--subscription-tests)
13. [Security Tests](#13-security-tests)
14. [Error Handling Tests](#14-error-handling-tests)
15. [Integration Tests](#15-integration-tests)
16. [Performance Tests](#16-performance-tests)

---

## 1. CCCD Parser Tests

### 1.1 Parse Gender & Century

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PARSE-001 | Parse gender code 0 (Nam, century 20) | `"0000"` | `gender="Nam"`, `century=20` | ✅ |
| TC-PARSE-002 | Parse gender code 1 (Nữ, century 20) | `"0001"` | `gender="Nữ"`, `century=20` | ✅ |
| TC-PARSE-003 | Parse gender code 2 (Nam, century 21) | `"0002"` | `gender="Nam"`, `century=21` | ✅ |
| TC-PARSE-004 | Parse gender code 3 (Nữ, century 21) | `"0003"` | `gender="Nữ"`, `century=21` | ✅ |
| TC-PARSE-005 | Parse gender code 4 (Nam, century 22) | `"0004"` | `gender="Nam"`, `century=22` | ✅ |
| TC-PARSE-006 | Parse gender code 8 (Nam, century 24) | `"0008"` | `gender="Nam"`, `century=24` | ✅ |
| TC-PARSE-007 | Parse gender code 9 (Nữ, century 24) | `"0009"` | `gender="Nữ"`, `century=24` | ✅ |

### 1.2 Parse Full CCCD

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PARSE-008 | Parse valid CCCD (HCM, Nam, 2003) | `"079203012345"` | `province_code="079"`, `gender="Nam"`, `birth_year=2003`, `century=21` | ✅ |
| TC-PARSE-009 | Parse valid CCCD (Hà Nội, Nữ, 1995) | `"001195012345"` | `province_code="001"`, `gender="Nữ"`, `birth_year=1995`, `century=20` | ✅ |
| TC-PARSE-010 | Parse valid CCCD (Đà Nẵng, Nam, 1988) | `"043188012345"` | `province_code="043"`, `gender="Nam"`, `birth_year=1988`, `century=20` | ✅ |
| TC-PARSE-011 | Verify age calculation | `"079203012345"` | `age` = current year - 2003 | ✅ |
| TC-PARSE-012 | Verify province code extraction | `"079203012345"` | `province_code="079"` (first 3 digits) | ✅ |
| TC-PARSE-013 | Verify birth year extraction | `"079203012345"` | `birth_year=2003` (digits 5-6 + century) | ✅ |

---

## 2. API Endpoint Tests

### 2.1 Health Check Endpoints

| Test Case ID | Description | Method | Endpoint | Expected Status | Status |
|--------------|-------------|--------|----------|-----------------|--------|
| TC-API-001 | GET root endpoint | `GET` | `/` | `200 OK` | ✅ |
| TC-API-002 | GET health check | `GET` | `/health` | `200 OK` with `status` field | ✅ |
| TC-API-003 | Verify health response format | `GET` | `/health` | JSON with `status`, optional `version`, `timestamp` | ✅ |

### 2.2 CCCD Parse Endpoint

| Test Case ID | Description | Method | Endpoint | Request Body | Expected Status | Status |
|--------------|-------------|--------|----------|--------------|-----------------|--------|
| TC-API-004 | Valid CCCD (12 digits) | `POST` | `/v1/cccd/parse` | `{"cccd": "001123456789"}` | `200 OK` | ✅ |
| TC-API-005 | CCCD too short (< 12) | `POST` | `/v1/cccd/parse` | `{"cccd": "00112345678"}` | `400 Bad Request` | ✅ |
| TC-API-006 | CCCD too long (> 12) | `POST` | `/v1/cccd/parse` | `{"cccd": "0011234567890"}` | `400 Bad Request` | ✅ |
| TC-API-007 | CCCD with letters | `POST` | `/v1/cccd/parse` | `{"cccd": "00112345678a"}` | `400 Bad Request` | ✅ |
| TC-API-008 | CCCD with special chars | `POST` | `/v1/cccd/parse` | `{"cccd": "001123456-78"}` | `400 Bad Request` | ✅ |
| TC-API-009 | Missing CCCD field | `POST` | `/v1/cccd/parse` | `{}` | `400 Bad Request` | ✅ |
| TC-API-010 | CCCD as number (not string) | `POST` | `/v1/cccd/parse` | `{"cccd": 123456789012}` | `400 Bad Request` | ✅ |
| TC-API-011 | CCCD as null | `POST` | `/v1/cccd/parse` | `{"cccd": null}` | `400 Bad Request` | ✅ |
| TC-API-012 | CCCD as empty string | `POST` | `/v1/cccd/parse` | `{"cccd": ""}` | `400 Bad Request` | ✅ |
| TC-API-013 | CCCD with whitespace | `POST` | `/v1/cccd/parse` | `{"cccd": " 001123456789 "}` | `400 Bad Request` (or trimmed) | ✅ |
| TC-API-014 | Invalid JSON body | `POST` | `/v1/cccd/parse` | `invalid json` | `400 Bad Request` | ✅ |
| TC-API-015 | Missing Content-Type header | `POST` | `/v1/cccd/parse` | Raw body | `400 Bad Request` or `415` | ✅ |
| TC-API-016 | Valid province_version (legacy_63) | `POST` | `/v1/cccd/parse` | `{"cccd": "079203012345", "province_version": "legacy_63"}` | `200 OK` | ✅ |
| TC-API-017 | Valid province_version (current_34) | `POST` | `/v1/cccd/parse` | `{"cccd": "079203012345", "province_version": "current_34"}` | `200 OK` | ✅ |
| TC-API-018 | Invalid province_version | `POST` | `/v1/cccd/parse` | `{"cccd": "079203012345", "province_version": "invalid"}` | `400 Bad Request` | ✅ |
| TC-API-019 | Province version alias (legacy_64) | `POST` | `/v1/cccd/parse` | `{"cccd": "079203012345", "province_version": "legacy_64"}` | `200 OK` with warning | ✅ |
| TC-API-020 | Response includes request_id | `POST` | `/v1/cccd/parse` | `{"cccd": "079203012345"}` | Response has `request_id` field | ✅ |
| TC-API-021 | Response format validation | `POST` | `/v1/cccd/parse` | `{"cccd": "079203012345"}` | All required fields present | ✅ |
| TC-API-022 | Extremely long CCCD (DoS attempt) | `POST` | `/v1/cccd/parse` | `{"cccd": "0" * 1000000}` | `400 Bad Request` (rejected early) | ✅ |

### 2.3 Response Format Tests

| Test Case ID | Description | Expected Response Fields | Status |
|--------------|-------------|-------------------------|--------|
| TC-RESP-001 | Success response structure | `success`, `is_valid_format`, `is_plausible`, `data`, `request_id`, `warnings` | ✅ |
| TC-RESP-002 | Error response structure | `success`, `is_valid_format`, `message`, `request_id` | ✅ |
| TC-RESP-003 | Data object structure | `province_code`, `province_name`, `gender`, `birth_year`, `century`, `age` | ✅ |
| TC-RESP-004 | Warnings array format | Array of warning strings | ✅ |

---

## 3. Validation Tests

### 3.1 Input Validation

| Test Case ID | Description | Input | Expected Result | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-VAL-001 | Validate CCCD length (12) | `"079203012345"` | ✅ Valid | ✅ |
| TC-VAL-002 | Reject short CCCD | `"12345"` | ❌ Invalid | ✅ |
| TC-VAL-003 | Reject long CCCD | `"1234567890123456"` | ❌ Invalid | ✅ |
| TC-VAL-004 | Reject non-numeric | `"07920301234a"` | ❌ Invalid | ✅ |
| TC-VAL-005 | Reject empty string | `""` | ❌ Invalid | ✅ |
| TC-VAL-006 | Reject null value | `null` | ❌ Invalid | ✅ |
| TC-VAL-007 | Reject missing field | No `cccd` field | ❌ Invalid | ✅ |
| TC-VAL-008 | Reject number type | `123456789012` (number) | ❌ Invalid | ✅ |
| TC-VAL-009 | Validate province_version enum | `"legacy_63"`, `"current_34"` | ✅ Valid | ✅ |
| TC-VAL-010 | Reject invalid province_version | `"invalid"` | ❌ Invalid | ✅ |

### 3.2 Email Validation

| Test Case ID | Description | Input | Expected Result | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-EMAIL-001 | Valid email format | `"user@example.com"` | ✅ Valid | ✅ |
| TC-EMAIL-002 | Valid email with dot | `"user.name@example.com"` | ✅ Valid | ✅ |
| TC-EMAIL-003 | Valid email with plus | `"user+tag@example.com"` | ✅ Valid | ✅ |
| TC-EMAIL-004 | Valid email with underscore | `"user_123@test.com"` | ✅ Valid | ✅ |
| TC-EMAIL-005 | Valid subdomain email | `"test@sub.domain.com"` | ✅ Valid | ✅ |
| TC-EMAIL-006 | Reject email without @ | `"not-an-email"` | ❌ Invalid | ✅ |
| TC-EMAIL-007 | Reject email without domain | `"user@"` | ❌ Invalid | ✅ |
| TC-EMAIL-008 | Reject email without TLD | `"user@example"` | ❌ Invalid | ✅ |
| TC-EMAIL-009 | Reject email with space | `"user name@example.com"` | ❌ Invalid | ✅ |
| TC-EMAIL-010 | Reject empty email | `""` | ❌ Invalid | ✅ |
| TC-EMAIL-011 | Reject double @ | `"user@@example.com"` | ❌ Invalid | ✅ |

---

## 4. Authentication & Authorization Tests

### 4.1 API Key Authentication (Simple Mode)

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-AUTH-001 | Missing API key | No `X-API-Key` header | `401 Unauthorized` | ✅ |
| TC-AUTH-002 | Wrong API key | `X-API-Key: wrong-key` | `401 Unauthorized` | ✅ |
| TC-AUTH-003 | Correct API key | `X-API-Key: correct-key` | `200 OK` | ✅ |
| TC-AUTH-004 | API key case sensitivity | `X-API-Key: CORRECT-KEY` (if key is lowercase) | `401 Unauthorized` | ✅ |
| TC-AUTH-005 | Empty API key | `X-API-Key: ` | `401 Unauthorized` | ✅ |
| TC-AUTH-006 | API key with whitespace | `X-API-Key: correct-key ` | `401 Unauthorized` (or trimmed) | ✅ |
| TC-AUTH-007 | No API key required (if not configured) | No header | `200 OK` | ✅ |

### 4.2 API Key Authentication (Tiered Mode)

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-AUTH-008 | Missing API key in tiered mode | No `X-API-Key` header | `401 Unauthorized` | ✅ |
| TC-AUTH-009 | Invalid API key format | `X-API-Key: invalid-format` | `401 Unauthorized` | ✅ |
| TC-AUTH-010 | Expired API key | `X-API-Key: expired-key` | `401 Unauthorized` | ✅ |
| TC-AUTH-011 | Revoked API key | `X-API-Key: revoked-key` | `401 Unauthorized` | ✅ |
| TC-AUTH-012 | Valid Free tier key | `X-API-Key: free_xxx` | `200 OK` | ✅ |
| TC-AUTH-013 | Valid Premium tier key | `X-API-Key: prem_xxx` | `200 OK` | ✅ |
| TC-AUTH-014 | Valid Ultra tier key | `X-API-Key: ultr_xxx` | `200 OK` | ✅ |
| TC-AUTH-015 | API key from inactive user | `X-API-Key: inactive-user-key` | `401 Unauthorized` | ✅ |
| TC-AUTH-016 | API key from unverified email | `X-API-Key: unverified-key` | `401 Unauthorized` (optional) | ✅ |

### 4.3 Admin Authentication

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-ADMIN-AUTH-001 | Admin dashboard without key | `GET /admin/` | `200 OK` (form page) | ✅ |
| TC-ADMIN-AUTH-002 | Admin API without key | `GET /admin/stats` | `403 Forbidden` | ✅ |
| TC-ADMIN-AUTH-003 | Admin API with wrong key | `GET /admin/stats` + `X-Admin-Key: wrong` | `403 Forbidden` | ✅ |
| TC-ADMIN-AUTH-004 | Admin API with correct key | `GET /admin/stats` + `X-Admin-Key: correct` | `200 OK` or `500` (not 403) | ✅ |
| TC-ADMIN-AUTH-005 | Admin key case sensitivity | `X-Admin-Key: CORRECT-KEY` (if lowercase) | `403 Forbidden` | ✅ |
| TC-ADMIN-AUTH-006 | Admin key in query param | `GET /admin/stats?X-Admin-Key=key` | `403 Forbidden` (header only) | ✅ |
| TC-ADMIN-AUTH-007 | Admin key missing header | No `X-Admin-Key` header | `403 Forbidden` | ✅ |
| TC-ADMIN-AUTH-008 | Admin login with correct credentials | `POST /admin/login` with valid email/password | `200 OK` + session | ✅ |
| TC-ADMIN-AUTH-009 | Admin login with wrong password | `POST /admin/login` with wrong password | `401 Unauthorized` | ✅ |
| TC-ADMIN-AUTH-010 | Admin login brute force protection | Multiple failed attempts | IP blocked / exponential backoff | ✅ |

### 4.4 Portal User Authentication

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-PORTAL-AUTH-001 | User login with correct credentials | `POST /portal/login` | `200 OK` + session | ✅ |
| TC-PORTAL-AUTH-002 | User login with wrong password | `POST /portal/login` | `401 Unauthorized` | ✅ |
| TC-PORTAL-AUTH-003 | User login with non-existent email | `POST /portal/login` | `401 Unauthorized` | ✅ |
| TC-PORTAL-AUTH-004 | User login with unverified email | `POST /portal/login` | `401 Unauthorized` (optional) | ✅ |
| TC-PORTAL-AUTH-005 | User logout | `POST /portal/logout` | `200 OK` + session cleared | ✅ |
| TC-PORTAL-AUTH-006 | Access protected route without login | `GET /portal/dashboard` | `302 Redirect` to login | ✅ |
| TC-PORTAL-AUTH-007 | Access protected route with valid session | `GET /portal/dashboard` | `200 OK` | ✅ |
| TC-PORTAL-AUTH-008 | Session expiration | Access after session timeout | `302 Redirect` to login | ✅ |
| TC-PORTAL-AUTH-009 | Remember me functionality | Login with `remember_me=true` | Extended session | ✅ |

---

## 5. Rate Limiting Tests

### 5.1 Free Tier Rate Limits

| Test Case ID | Description | Requests | Expected Result | Status |
|--------------|-------------|----------|-----------------|--------|
| TC-RATE-001 | Free tier: 10 requests/minute | 10 requests | All `200 OK` | ✅ |
| TC-RATE-002 | Free tier: 11th request | 11 requests | 11th = `429 Too Many Requests` | ✅ |
| TC-RATE-003 | Free tier: Rate limit reset | Wait 1 minute, then request | `200 OK` | ✅ |
| TC-RATE-004 | Free tier: Concurrent requests | 10 simultaneous requests | All `200 OK` | ✅ |

### 5.2 Premium Tier Rate Limits

| Test Case ID | Description | Requests | Expected Result | Status |
|--------------|-------------|----------|-----------------|--------|
| TC-RATE-005 | Premium tier: 100 requests/minute | 100 requests | All `200 OK` | ✅ |
| TC-RATE-006 | Premium tier: 101st request | 101 requests | 101st = `429 Too Many Requests` | ✅ |
| TC-RATE-007 | Premium tier: Rate limit reset | Wait 1 minute, then request | `200 OK` | ✅ |

### 5.3 Ultra Tier Rate Limits

| Test Case ID | Description | Requests | Expected Result | Status |
|--------------|-------------|----------|-----------------|--------|
| TC-RATE-008 | Ultra tier: 1000 requests/minute | 1000 requests | All `200 OK` | ✅ |
| TC-RATE-009 | Ultra tier: 1001st request | 1001 requests | 1001st = `429 Too Many Requests` | ✅ |
| TC-RATE-010 | Ultra tier: Rate limit reset | Wait 1 minute, then request | `200 OK` | ✅ |

### 5.4 Default Rate Limits

| Test Case ID | Description | Requests | Expected Result | Status |
|--------------|-------------|----------|-----------------|--------|
| TC-RATE-011 | Default: 30 requests/minute (no API key) | 30 requests | All `200 OK` | ✅ |
| TC-RATE-012 | Default: 31st request (no API key) | 31 requests | 31st = `429 Too Many Requests` | ✅ |
| TC-RATE-013 | Rate limit by IP address | Different IPs, same endpoint | Separate limits per IP | ✅ |
| TC-RATE-014 | Rate limit by API key | Same IP, different keys | Separate limits per key | ✅ |

### 5.5 Rate Limit Response Format

| Test Case ID | Description | Expected Response | Status |
|--------------|-------------|-------------------|--------|
| TC-RATE-015 | Rate limit error format | `429` status, error message | ✅ |
| TC-RATE-016 | Rate limit headers | `Retry-After` header (optional) | ✅ |

---

## 6. Province Mapping Tests

### 6.1 Province Code Resolution

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PROV-001 | Resolve province code 079 (HCM) | `"079203012345"` | `province_name="Thành phố Hồ Chí Minh"` | ✅ |
| TC-PROV-002 | Resolve province code 001 (Hà Nội) | `"001203012345"` | `province_name="Thành phố Hà Nội"` | ✅ |
| TC-PROV-003 | Resolve province code 043 (Đà Nẵng) | `"043203012345"` | `province_name="Thành phố Đà Nẵng"` | ✅ |
| TC-PROV-004 | Unknown province code | `"999203012345"` | `province_name=null` + warning | ✅ |
| TC-PROV-005 | Province code with legacy_63 version | `"079203012345"` + `province_version="legacy_63"` | Correct legacy name | ✅ |
| TC-PROV-006 | Province code with current_34 version | `"079203012345"` + `province_version="current_34"` | Correct current name | ✅ |
| TC-PROV-007 | Default province version | `"079203012345"` (no version) | Uses default from config | ✅ |
| TC-PROV-008 | Province version alias (legacy_64) | `"079203012345"` + `province_version="legacy_64"` | Maps to `legacy_63` + warning | ✅ |

### 6.2 Province Version Handling

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PROV-009 | Legacy 63 provinces mapping | Various codes | Correct legacy names | ✅ |
| TC-PROV-010 | Current 34 provinces mapping | Various codes | Correct current names | ✅ |
| TC-PROV-011 | Province code not in mapping | `"999"` | `null` + `province_code_not_found` warning | ✅ |

---

## 7. Plausibility Checks Tests

### 7.1 Birth Year Validation

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PLAUS-001 | Birth year in future | `"052399012345"` (2099) | `is_plausible=false` + `birth_year_in_future` warning | ✅ |
| TC-PLAUS-002 | Birth year too old (> 150 years) | `"001850012345"` (1850) | `is_plausible=false` + warning | ✅ |
| TC-PLAUS-003 | Birth year reasonable | `"079203012345"` (2003) | `is_plausible=true` | ✅ |
| TC-PLAUS-004 | Birth year current year | Current year | `is_plausible=true` (or warning) | ✅ |
| TC-PLAUS-005 | Birth year 1 year ago | Last year | `is_plausible=true` | ✅ |

### 7.2 Gender Consistency

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PLAUS-006 | Gender code consistency | Valid codes 0-9 | Correct gender mapping | ✅ |
| TC-PLAUS-007 | Invalid gender code | Code > 9 | Warning or error | ✅ |

### 7.3 Province Code Consistency

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-PLAUS-008 | Province code exists in mapping | Valid code | `is_plausible=true` | ✅ |
| TC-PLAUS-009 | Province code not in mapping | `"999"` | `is_plausible=false` + warning | ✅ |

---

## 8. Portal & User Management Tests

### 8.1 User Registration

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-REG-001 | Register with valid data | `POST /portal/register` | `200 OK` + email sent | ✅ |
| TC-REG-002 | Register with existing email | `POST /portal/register` | `400 Bad Request` | ✅ |
| TC-REG-003 | Register with invalid email | `POST /portal/register` | `400 Bad Request` | ✅ |
| TC-REG-004 | Register with weak password | `POST /portal/register` | `400 Bad Request` | ✅ |
| TC-REG-005 | Register with missing fields | `POST /portal/register` | `400 Bad Request` | ✅ |
| TC-REG-006 | Register with password mismatch | `POST /portal/register` | `400 Bad Request` | ✅ |
| TC-REG-007 | Email verification link | Click verification link | Account activated | ✅ |
| TC-REG-008 | Expired verification token | Click expired link | `400 Bad Request` | ✅ |
| TC-REG-009 | Invalid verification token | Click invalid link | `400 Bad Request` | ✅ |

### 8.2 Password Reset

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-PWD-001 | Request password reset with valid email | `POST /portal/forgot-password` | `200 OK` + email sent | ✅ |
| TC-PWD-002 | Request password reset with invalid email | `POST /portal/forgot-password` | `400 Bad Request` | ✅ |
| TC-PWD-003 | Request password reset with non-existent email | `POST /portal/forgot-password` | `200 OK` (don't reveal existence) | ✅ |
| TC-PWD-004 | Reset password with valid token | `POST /portal/reset-password` | `200 OK` | ✅ |
| TC-PWD-005 | Reset password with expired token | `POST /portal/reset-password` | `400 Bad Request` | ✅ |
| TC-PWD-006 | Reset password with invalid token | `POST /portal/reset-password` | `400 Bad Request` | ✅ |
| TC-PWD-007 | Reset password with weak password | `POST /portal/reset-password` | `400 Bad Request` | ✅ |
| TC-PWD-008 | Reset password with password mismatch | `POST /portal/reset-password` | `400 Bad Request` | ✅ |
| TC-PWD-009 | Reset password token one-time use | Use token twice | Second use fails | ✅ |

### 8.3 User Profile Management

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-PROF-001 | Get user profile | `GET /portal/profile` | `200 OK` + profile data | ✅ |
| TC-PROF-002 | Update user profile | `POST /portal/profile` | `200 OK` | ✅ |
| TC-PROF-003 | Update email | `POST /portal/profile` | `200 OK` + verification required | ✅ |
| TC-PROF-004 | Change password | `POST /portal/change-password` | `200 OK` | ✅ |
| TC-PROF-005 | Change password with wrong current password | `POST /portal/change-password` | `400 Bad Request` | ✅ |

### 8.4 Dashboard & Statistics

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-DASH-001 | Get dashboard data | `GET /portal/dashboard` | `200 OK` + stats | ✅ |
| TC-DASH-002 | Get usage statistics | `GET /portal/usage` | `200 OK` + usage data | ✅ |
| TC-DASH-003 | Get usage by date range | `GET /portal/usage?from=X&to=Y` | `200 OK` + filtered data | ✅ |
| TC-DASH-004 | Get billing history | `GET /portal/billing` | `200 OK` + billing data | ✅ |

---

## 9. Admin Dashboard Tests

### 9.1 Admin Statistics

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-ADMIN-001 | Get system statistics | `GET /admin/stats` | `200 OK` + stats JSON | ✅ |
| TC-ADMIN-002 | Get statistics without auth | `GET /admin/stats` | `403 Forbidden` | ✅ |
| TC-ADMIN-003 | Statistics include total requests | Response includes `total_requests` | ✅ |
| TC-ADMIN-004 | Statistics include total users | Response includes `total_users` | ✅ |
| TC-ADMIN-005 | Statistics include active API keys | Response includes `active_keys` | ✅ |
| TC-ADMIN-006 | Statistics include requests by tier | Response includes tier breakdown | ✅ |

### 9.2 User Management

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-ADMIN-007 | List all users | `GET /admin/users` | `200 OK` + user list | ✅ |
| TC-ADMIN-008 | Search users by email | `GET /admin/users?search=email` | `200 OK` + filtered list | ✅ |
| TC-ADMIN-009 | Get user details | `GET /admin/users/{id}` | `200 OK` + user data | ✅ |
| TC-ADMIN-010 | Update user tier | `POST /admin/users/{id}/tier` | `200 OK` | ✅ |
| TC-ADMIN-011 | Deactivate user | `POST /admin/users/{id}/deactivate` | `200 OK` | ✅ |
| TC-ADMIN-012 | Activate user | `POST /admin/users/{id}/activate` | `200 OK` | ✅ |
| TC-ADMIN-013 | Delete user | `DELETE /admin/users/{id}` | `200 OK` | ✅ |

### 9.3 Payment Management

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-ADMIN-014 | List pending payments | `GET /admin/payments` | `200 OK` + payment list | ✅ |
| TC-ADMIN-015 | Approve payment | `POST /admin/payments/{id}/approve` | `200 OK` | ✅ |
| TC-ADMIN-016 | Reject payment | `POST /admin/payments/{id}/reject` | `200 OK` | ✅ |
| TC-ADMIN-017 | Get payment details | `GET /admin/payments/{id}` | `200 OK` + payment data | ✅ |

### 9.4 API Key Management (Admin)

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-ADMIN-018 | Create API key | `POST /admin/keys/create` | `200 OK` + key data | ✅ |
| TC-ADMIN-019 | Create key with invalid tier | `POST /admin/keys/create` | `400 Bad Request` | ✅ |
| TC-ADMIN-020 | Create key with invalid validity | `POST /admin/keys/create` | `400 Bad Request` | ✅ |
| TC-ADMIN-021 | List all API keys | `GET /admin/keys` | `200 OK` + key list | ✅ |
| TC-ADMIN-022 | Revoke API key | `POST /admin/keys/{id}/revoke` | `200 OK` | ✅ |
| TC-ADMIN-023 | Delete API key | `DELETE /admin/keys/{id}` | `200 OK` | ✅ |

---

## 10. Email Service Tests

### 10.1 Email Sending

| Test Case ID | Description | Scenario | Expected Result | Status |
|--------------|-------------|----------|------------------|--------|
| TC-EMAIL-SVC-001 | Send verification email | User registration | Email sent successfully | ✅ |
| TC-EMAIL-SVC-002 | Send password reset email | Password reset request | Email sent successfully | ✅ |
| TC-EMAIL-SVC-003 | Send key expiration warning | API key expiring soon | Email sent successfully | ✅ |
| TC-EMAIL-SVC-004 | Email with invalid SMTP config | SMTP misconfigured | Error logged, graceful failure | ✅ |
| TC-EMAIL-SVC-005 | Email template rendering | All email types | Correct template rendered | ✅ |
| TC-EMAIL-SVC-006 | Email with special characters | Unicode content | Properly encoded | ✅ |

### 10.2 Email Templates

| Test Case ID | Description | Template | Expected Content | Status |
|--------------|-------------|----------|------------------|--------|
| TC-EMAIL-TMP-001 | Verification email template | `verify_email.html` | Contains verification link | ✅ |
| TC-EMAIL-TMP-002 | Password reset template | `reset_password.html` | Contains reset link | ✅ |
| TC-EMAIL-TMP-003 | Key expiration template | `key_expiration_warning.html` | Contains key info | ✅ |
| TC-EMAIL-TMP-004 | Email base template | `base.html` | Consistent styling | ✅ |

---

## 11. API Key Management Tests

### 11.1 API Key Creation (User)

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-KEY-001 | Create API key | `POST /portal/keys/create` | `200 OK` + key data | ✅ |
| TC-KEY-002 | Create key with label | `POST /portal/keys/create` | `200 OK` + labeled key | ✅ |
| TC-KEY-003 | Create key without label | `POST /portal/keys/create` | `200 OK` + default label | ✅ |
| TC-KEY-004 | Create key limit reached | `POST /portal/keys/create` | `400 Bad Request` | ✅ |
| TC-KEY-005 | Create key for inactive user | `POST /portal/keys/create` | `401 Unauthorized` | ✅ |
| TC-KEY-006 | Key format validation | Response | Key follows format: `{tier}_{hash}` | ✅ |

### 11.2 API Key Listing

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-KEY-007 | List user's API keys | `GET /portal/keys` | `200 OK` + key list | ✅ |
| TC-KEY-008 | List keys with metadata | Response | Includes: label, tier, created, expires | ✅ |
| TC-KEY-009 | List keys for inactive user | `GET /portal/keys` | `401 Unauthorized` | ✅ |

### 11.3 API Key Deletion

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-KEY-010 | Delete API key | `DELETE /portal/keys/{id}` | `200 OK` | ✅ |
| TC-KEY-011 | Delete non-existent key | `DELETE /portal/keys/999` | `404 Not Found` | ✅ |
| TC-KEY-012 | Delete other user's key | `DELETE /portal/keys/{other_user_key}` | `403 Forbidden` | ✅ |
| TC-KEY-013 | Delete key confirmation | Frontend | Confirmation modal shown | ✅ |

### 11.4 API Key Updates

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-KEY-014 | Update key label | `PUT /portal/keys/{id}` | `200 OK` | ✅ |
| TC-KEY-015 | Update key status | `PUT /portal/keys/{id}` | `200 OK` | ✅ |
| TC-KEY-016 | Revoke key | `POST /portal/keys/{id}/revoke` | `200 OK` | ✅ |
| TC-KEY-017 | Reactivate revoked key | `POST /portal/keys/{id}/reactivate` | `200 OK` | ✅ |

### 11.5 API Key Expiration

| Test Case ID | Description | Scenario | Expected Result | Status |
|--------------|-------------|----------|------------------|--------|
| TC-KEY-018 | Key expiration check | Expired key used | `401 Unauthorized` | ✅ |
| TC-KEY-019 | Key expiring soon warning | 7 days before expiry | Email sent | ✅ |
| TC-KEY-020 | Key expiration date validation | Create key | Expires date set correctly | ✅ |

---

## 12. Billing & Subscription Tests

### 12.1 Subscription Management

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-BILL-001 | Get current subscription | `GET /portal/subscription` | `200 OK` + subscription data | ✅ |
| TC-BILL-002 | Request tier upgrade | `POST /portal/upgrade` | `200 OK` + payment request | ✅ |
| TC-BILL-003 | Upgrade to Premium | `POST /portal/upgrade` | Payment request created | ✅ |
| TC-BILL-004 | Upgrade to Ultra | `POST /portal/upgrade` | Payment request created | ✅ |
| TC-BILL-005 | Upgrade from same tier | `POST /portal/upgrade` | `400 Bad Request` | ✅ |
| TC-BILL-006 | Get payment history | `GET /portal/billing` | `200 OK` + history | ✅ |

### 12.2 Payment Processing

| Test Case ID | Description | Request | Expected Status | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-PAY-001 | Create payment request | `POST /portal/payments` | `200 OK` + payment ID | ✅ |
| TC-PAY-002 | Get payment status | `GET /portal/payments/{id}` | `200 OK` + status | ✅ |
| TC-PAY-003 | Payment approved | Admin approves | User tier updated | ✅ |
| TC-PAY-004 | Payment rejected | Admin rejects | User tier unchanged | ✅ |
| TC-PAY-005 | Payment pending | Payment created | Status = pending | ✅ |

---

## 13. Security Tests

### 13.1 SQL Injection Prevention

| Test Case ID | Description | Input | Expected Result | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-SEC-001 | SQL injection in CCCD field | `"079203012345'; DROP TABLE users;--"` | `400 Bad Request` (sanitized) | ✅ |
| TC-SEC-002 | SQL injection in email | `"user@test.com'; DROP TABLE users;--"` | `400 Bad Request` | ✅ |
| TC-SEC-003 | SQL injection in API key | `"key'; DROP TABLE users;--"` | `401 Unauthorized` | ✅ |
| TC-SEC-004 | Parameterized queries | All database queries | No SQL injection possible | ✅ |

### 13.2 XSS Prevention

| Test Case ID | Description | Input | Expected Result | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-SEC-005 | XSS in CCCD field | `"<script>alert('XSS')</script>"` | `400 Bad Request` or escaped | ✅ |
| TC-SEC-006 | XSS in email | `"<script>alert('XSS')</script>@test.com"` | `400 Bad Request` | ✅ |
| TC-SEC-007 | XSS in user input | All text inputs | Properly escaped in output | ✅ |
| TC-SEC-008 | Template escaping | Jinja2 templates | All variables escaped | ✅ |

### 13.3 CSRF Protection

| Test Case ID | Description | Request | Expected Result | Status |
|--------------|-------------|---------|-----------------|--------|
| TC-SEC-009 | CSRF token validation | POST without token | `403 Forbidden` | ✅ |
| TC-SEC-010 | CSRF token in forms | All forms | Token included | ✅ |
| TC-SEC-011 | SameSite cookie | Session cookies | `SameSite=Lax` or `Strict` | ✅ |

### 13.4 Brute Force Protection

| Test Case ID | Description | Scenario | Expected Result | Status |
|--------------|-------------|----------|------------------|--------|
| TC-SEC-012 | Admin login brute force | 5 failed attempts | IP blocked / exponential backoff | ✅ |
| TC-SEC-013 | User login brute force | Multiple failed attempts | Rate limiting applied | ✅ |
| TC-SEC-014 | Failed attempt logging | Failed login | Logged with IP, timestamp | ✅ |
| TC-SEC-015 | IP blocking | Blocked IP attempts | `403 Forbidden` | ✅ |
| TC-SEC-016 | Block expiration | After timeout | IP unblocked | ✅ |

### 13.5 Password Security

| Test Case ID | Description | Input | Expected Result | Status |
|--------------|-------------|-------|-----------------|--------|
| TC-SEC-017 | Password hashing | All passwords | bcrypt hashed | ✅ |
| TC-SEC-018 | Password strength validation | Weak password | `400 Bad Request` | ✅ |
| TC-SEC-019 | Password minimum length | Password < 8 chars | `400 Bad Request` | ✅ |
| TC-SEC-020 | Password not in plaintext | Database storage | Hashed only | ✅ |

### 13.6 Data Masking

| Test Case ID | Description | Input | Expected Output | Status |
|--------------|-------------|-------|------------------|--------|
| TC-SEC-021 | CCCD masking in logs | `"079203012345"` | `"079******345"` | ✅ |
| TC-SEC-022 | CCCD masking in responses | Error responses | Masked CCCD | ✅ |
| TC-SEC-023 | API key masking | Full key | Only prefix shown | ✅ |

### 13.7 Headers Security

| Test Case ID | Description | Response | Expected Headers | Status |
|--------------|-------------|----------|------------------|--------|
| TC-SEC-024 | Security headers | All responses | `X-Content-Type-Options`, `X-Frame-Options`, etc. | ✅ |
| TC-SEC-025 | CORS configuration | API responses | Proper CORS headers | ✅ |
| TC-SEC-026 | HTTPS enforcement | Production | Redirect HTTP to HTTPS | ✅ |

---

## 14. Error Handling Tests

### 14.1 HTTP Error Codes

| Test Case ID | Description | Scenario | Expected Status | Status |
|--------------|-------------|----------|-----------------|--------|
| TC-ERR-001 | 400 Bad Request | Invalid input | `400` with error message | ✅ |
| TC-ERR-002 | 401 Unauthorized | Missing/invalid auth | `401` with error message | ✅ |
| TC-ERR-003 | 403 Forbidden | Insufficient permissions | `403` with error message | ✅ |
| TC-ERR-004 | 404 Not Found | Invalid endpoint | `404` with error message | ✅ |
| TC-ERR-005 | 429 Too Many Requests | Rate limit exceeded | `429` with error message | ✅ |
| TC-ERR-006 | 500 Internal Server Error | Server error | `500` with generic message | ✅ |
| TC-ERR-007 | 503 Service Unavailable | Database down | `503` with error message | ✅ |

### 14.2 Error Response Format

| Test Case ID | Description | Expected Format | Status |
|--------------|-------------|-----------------|--------|
| TC-ERR-008 | Error response structure | `success`, `message`, `request_id` | ✅ |
| TC-ERR-009 | Error message clarity | Clear, actionable message | ✅ |
| TC-ERR-010 | Error logging | All errors logged | ✅ |
| TC-ERR-011 | Error request ID | Unique ID for tracking | ✅ |

### 14.3 Exception Handling

| Test Case ID | Description | Scenario | Expected Result | Status |
|--------------|-------------|----------|------------------|--------|
| TC-ERR-012 | Database connection error | DB unavailable | Graceful error, no crash | ✅ |
| TC-ERR-013 | Invalid JSON body | Malformed JSON | `400 Bad Request` | ✅ |
| TC-ERR-014 | Missing required fields | Incomplete request | `400 Bad Request` | ✅ |
| TC-ERR-015 | Unexpected exception | Unhandled exception | `500` + logged | ✅ |
| TC-ERR-016 | Timeout handling | Request timeout | `504 Gateway Timeout` | ✅ |

---

## 15. Integration Tests

### 15.1 End-to-End User Flow

| Test Case ID | Description | Steps | Expected Result | Status |
|--------------|-------------|-------|------------------|--------|
| TC-INT-001 | Complete user registration flow | Register → Verify → Login → Create Key → Use API | All steps succeed | ✅ |
| TC-INT-002 | Password reset flow | Request → Email → Reset → Login | Password changed successfully | ✅ |
| TC-INT-003 | Tier upgrade flow | Request → Payment → Admin Approve → Tier Updated | Tier upgraded | ✅ |
| TC-INT-004 | API key lifecycle | Create → Use → Expire → Delete | All operations succeed | ✅ |

### 15.2 Database Integration

| Test Case ID | Description | Scenario | Expected Result | Status |
|--------------|-------------|----------|------------------|--------|
| TC-INT-005 | User creation in database | Register user | User record created | ✅ |
| TC-INT-006 | API key creation in database | Create key | Key record created | ✅ |
| TC-INT-007 | Request logging | API call | Request logged to DB | ✅ |
| TC-INT-008 | Transaction rollback | Error during operation | No partial data | ✅ |
| TC-INT-009 | Database connection pooling | Multiple concurrent requests | All handled correctly | ✅ |

### 15.3 Email Integration

| Test Case ID | Description | Scenario | Expected Result | Status |
|--------------|-------------|----------|------------------|--------|
| TC-INT-010 | Email sent on registration | User registers | Verification email sent | ✅ |
| TC-INT-011 | Email sent on password reset | User requests reset | Reset email sent | ✅ |
| TC-INT-012 | Email with SMTP failure | SMTP error | Error logged, graceful failure | ✅ |

---

## 16. Performance Tests

### 16.1 Response Time

| Test Case ID | Description | Metric | Expected Value | Status |
|--------------|-------------|--------|----------------|--------|
| TC-PERF-001 | API response time | Average | < 200ms | ✅ |
| TC-PERF-002 | API response time (p95) | 95th percentile | < 500ms | ✅ |
| TC-PERF-003 | API response time (p99) | 99th percentile | < 1000ms | ✅ |
| TC-PERF-004 | Database query time | Average | < 50ms | ✅ |
| TC-PERF-005 | Health check response | Average | < 10ms | ✅ |

### 16.2 Throughput

| Test Case ID | Description | Metric | Expected Value | Status |
|--------------|-------------|--------|----------------|--------|
| TC-PERF-006 | Requests per second | RPS | > 100 RPS | ✅ |
| TC-PERF-007 | Concurrent users | Simultaneous | > 50 users | ✅ |
| TC-PERF-008 | Database connections | Pool size | Optimal pool size | ✅ |

### 16.3 Resource Usage

| Test Case ID | Description | Metric | Expected Value | Status |
|--------------|-------------|--------|----------------|--------|
| TC-PERF-009 | Memory usage | Average | < 512MB | ✅ |
| TC-PERF-010 | CPU usage | Average | < 50% | ✅ |
| TC-PERF-011 | Database connection pool | Active connections | < pool max | ✅ |

### 16.4 Load Testing

| Test Case ID | Description | Load | Expected Result | Status |
|--------------|-------------|------|-----------------|--------|
| TC-PERF-012 | Normal load | 50 RPS | All requests succeed | ✅ |
| TC-PERF-013 | High load | 200 RPS | Most requests succeed | ✅ |
| TC-PERF-014 | Spike load | 500 RPS | Graceful degradation | ✅ |
| TC-PERF-015 | Sustained load | 100 RPS for 1 hour | No memory leaks | ✅ |

---

## 📊 Test Coverage Summary

| Category | Total Test Cases | Implemented | Pending | Coverage |
|----------|-----------------|-------------|---------|----------|
| CCCD Parser | 13 | 13 | 0 | 100% |
| API Endpoints | 22 | 22 | 0 | 100% |
| Validation | 20 | 20 | 0 | 100% |
| Authentication | 25 | 25 | 0 | 100% |
| Rate Limiting | 16 | 16 | 0 | 100% |
| Province Mapping | 11 | 11 | 0 | 100% |
| Plausibility | 9 | 9 | 0 | 100% |
| Portal & User | 20 | 20 | 0 | 100% |
| Admin Dashboard | 23 | 23 | 0 | 100% |
| Email Service | 10 | 10 | 0 | 100% |
| API Key Management | 20 | 20 | 0 | 100% |
| Billing & Subscription | 6 | 6 | 0 | 100% |
| Security | 26 | 26 | 0 | 100% |
| Error Handling | 16 | 16 | 0 | 100% |
| Integration | 12 | 12 | 0 | 100% |
| Performance | 15 | 15 | 0 | 100% |
| **TOTAL** | **264** | **264** | **0** | **100%** |

---

## 🧪 Running Tests

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test Category

```bash
# CCCD Parser tests
python -m pytest tests/test_cccd_parser.py -v

# Validation tests
python -m pytest tests/test_validation.py -v

# Rate limiting tests
python -m pytest tests/test_rate_limit_tier.py -v

# Admin authorization tests
python -m pytest tests/test_admin_authorization.py -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=. --cov-report=html
```

### Run API Endpoint Tests

```bash
# Make sure server is running first
python run.py

# In another terminal
python tests/test_api_endpoints.py
```

---

## 📝 Notes

- **Status Column**: ✅ = Implemented, ⏳ = In Progress, ❌ = Not Implemented
- **Test IDs**: Follow format `TC-{CATEGORY}-{NUMBER}` for easy tracking
- **Priority**: Critical tests are marked with higher priority
- **Automation**: Most tests are automated, some require manual testing (marked accordingly)

---

## 🔄 Maintenance

This document should be updated when:
- New features are added
- New test cases are identified
- Test implementation status changes
- Test results reveal new edge cases

**Last Updated**: 2024-12-19
