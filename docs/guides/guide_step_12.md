# guide_step_12.md — Bước 12: Customer Portal & Thanh toán

## Mục tiêu

Tạo trang web để khách hàng có thể:
- Đăng ký tài khoản
- Tạo và quản lý API keys
- Xem usage statistics
- Thanh toán để nâng cấp tier
- Xem billing history

## Kiến trúc

### 1. Database Schema

**Bảng `users`** (khách hàng):
- `id`, `email`, `password_hash`, `full_name`
- `created_at`, `last_login_at`
- `status` (active/suspended)

**Bảng `subscriptions`** (đăng ký tier):
- `id`, `user_id`, `tier` (free/premium/ultra)
- `status` (active/expired/cancelled)
- `started_at`, `expires_at`
- `payment_method`, `amount`

**Bảng `payments`** (lịch sử thanh toán):
- `id`, `user_id`, `subscription_id`
- `amount`, `currency`, `status` (pending/success/failed)
- `payment_gateway`, `transaction_id`
- `created_at`, `paid_at`

### 2. Routes

**Public Routes:**
- `GET /portal/` - Landing page
- `GET /portal/register` - Đăng ký
- `POST /portal/register` - Xử lý đăng ký
- `GET /portal/login` - Đăng nhập
- `POST /portal/login` - Xử lý đăng nhập
- `GET /portal/logout` - Đăng xuất

**Protected Routes (cần login):**
- `GET /portal/dashboard` - Dashboard chính
- `GET /portal/keys` - Quản lý API keys
- `POST /portal/keys/create` - Tạo API key mới
- `POST /portal/keys/delete` - Xóa API key
- `GET /portal/usage` - Xem usage stats
- `GET /portal/billing` - Xem billing history
- `GET /portal/upgrade` - Nâng cấp tier
- `POST /portal/upgrade` - Xử lý thanh toán

### 3. Features

#### A. Authentication
- Email/password login
- Session management
- Password hashing (bcrypt)
- Remember me option

#### B. API Key Management
- Tạo API key với tier (free/premium/ultra)
- Xem danh sách keys
- Xóa/revoke keys
- Copy key dễ dàng

#### C. Usage Dashboard
- Requests per day/week/month
- Response time stats
- Error rate
- Top endpoints

#### D. Billing & Payment
- Xem current tier
- Upgrade tier (free → premium → ultra)
- Payment integration (Stripe/PayPal hoặc manual)
- Invoice history

## Implementation Plan

### Phase 1: Database & Auth (Core)
- [X] Tạo database schema (`users`, `subscriptions`, `payments`)
- [X] Implement user registration/login
- [X] Session management
- [X] Password hashing
- [X]  Ghi nhớ đăng nhập hoạt động đúng
### Phase 2: API Key Management
- [X] Portal UI để tạo API keys
- [X] Link với existing `api_keys` table
- [X] List/delete keys từ portal

### Phase 3: Dashboard & Stats
- [X] Backend: Query từ `request_logs` table (Python/SQL)
- [X] Backend: Aggregate data (requests per day, status codes, response times)
- [X] Backend: Trả về JSON API endpoint `/portal/usage/api`
- [X] Frontend: Dashboard UI hiển thị stats (`/portal/usage`)
- [X] Frontend: Charts/graphs với Chart.js (JavaScript chạy trên browser)

**Lưu ý về kiến trúc:**
- **Backend (Python)**: Query database → aggregate data → trả JSON
- **Frontend (HTML/JS)**: Nhận JSON → render chart với Chart.js
- **Không cần pandas**: Data đơn giản, SQL query đủ (SUM, COUNT, GROUP BY)
- **Chart.js**: Thư viện JavaScript chạy trên browser, không phải backend

### Phase 4: Billing & Payment
- [X] Backend: Billing service (`services/billing_service.py`)
- [X] Backend: Routes `/portal/billing` và `/portal/upgrade`
- [ ] Frontend: Billing history page (`billing.html`)
- [ ] Frontend: Upgrade tier page (`upgrade.html`)
- [ ] Manual payment flow (admin approve)
- [ ] (Optional) Payment gateway integration (Stripe) - sau MVP

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript (hoặc có thể dùng Bootstrap cho nhanh)
- **Backend**: Flask (đã có)
- **Database**: MySQL (đã có)
- **Payment**: Stripe (hoặc manual payment cho MVP)
- **Charts**: Chart.js hoặc simple HTML tables

## Hoàn thành khi

- [ ] Khách hàng có thể đăng ký/login
- [ ] Khách hàng có thể tạo API key từ portal
- [ ] Khách hàng có thể xem usage stats
- [ ] Khách hàng có thể upgrade tier (ít nhất manual payment)
- [ ] Admin có thể approve payments (nếu manual)

## Tự test (Self-check)

### 1. Test Registration & Login
1. Mở `http://127.0.0.1:8000/portal/register`
2. Đăng ký tài khoản mới
3. Login với email/password
4. ✅ Thấy dashboard

### 2. Test API Key Creation
1. Login vào portal
2. Vào "API Keys" → "Create New Key"
3. Chọn tier (free/premium/ultra)
4. Tạo key
5. ✅ Thấy key mới trong list, có thể copy

### 3. Test Usage Stats
1. Dùng API key vừa tạo để gọi API vài lần
2. Vào portal → "Usage"
3. ✅ Thấy stats (requests count, response time, etc.)

### 4. Test Upgrade Tier
1. Vào "Billing" → "Upgrade"
2. Chọn tier mới (premium/ultra)
3. Thanh toán (manual hoặc Stripe)
4. ✅ Tier được update, rate limit thay đổi

---

## ✅ DoD (Definition of Done) - Bước 12

| Tiêu chí | Cách verify | Kết quả |
|----------|-------------|---------|
| User registration | Đăng ký thành công → có thể login | ⏳ |
| User login | Login thành công → thấy dashboard | ⏳ |
| Create API key from portal | Tạo key từ portal → dùng được ngay | ⏳ |
| View usage stats | Xem stats → thấy requests/errors | ⏳ |
| Upgrade tier | Upgrade → rate limit thay đổi | ⏳ |
| Payment integration | Thanh toán → subscription active | ⏳ |

---

## Notes

### Payment Options

**Option 1: Manual Payment (MVP)**
- Khách hàng chọn tier
- Admin approve payment manually
- Update subscription trong database
- ✅ Đơn giản, không cần payment gateway
- ❌ Không tự động

**Option 2: Stripe Integration**
- Tích hợp Stripe Checkout
- Tự động xử lý payment
- Webhook để update subscription
- ✅ Tự động, professional
- ❌ Cần Stripe account, phức tạp hơn

**Recommendation**: Bắt đầu với Manual Payment cho MVP, sau đó upgrade sang Stripe.

### Security Considerations

- Password hashing (bcrypt với salt)
- CSRF protection cho forms
- Rate limiting cho login attempts
- Session timeout
- HTTPS trong production (required cho payment)

### UI/UX

- Responsive design (mobile-friendly)
- Clear pricing table
- Easy API key copy button
- Visual charts cho stats
- Clear error messages
