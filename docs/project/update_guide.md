# Hướng dẫn xây dựng hệ thống CCCD API

> Tài liệu này mô tả quy trình và kiến trúc để xây dựng hệ thống CCCD API từ đầu.  
> **Lưu ý**: Tài liệu này tập trung vào quy trình và kiến trúc, không chứa code cụ thể.

---

## 0. Tại sao cần hệ thống CCCD API?

### 0.1 Vấn đề thực tế

**Người dùng phải nhập tay nhiều trường:**
- Người dùng phải nhập số Căn cước công dân (CCCD), sau đó tiếp tục phải chọn thủ công: **Giới tính**, **Năm sinh**, và **Tỉnh/Thành phố** (Nơi đăng ký khai sinh).
- Trong khi đó, các thông tin này đã nằm ngay trong chính số CCCD họ vừa nhập.

**Rủi ro sai lệch dữ liệu:**
- Việc nhập tay dẫn đến rủi ro sai lệch thông tin (ví dụ: Nhập số CCCD là nam, nhưng chọn giới tính là nữ do bấm nhầm).
- Giảm thiểu trường hợp CCCD giả mạo (API có thể validate format và tính hợp lý).
- Giảm sai sót dữ liệu được lưu trong Database.

### 0.2 Lợi ích cho người dùng

- **Tự điền nhanh**: Chỉ cần nhập CCCD → hệ thống tự động điền các trường còn lại.
- **Tăng tỷ lệ hoàn tất**: Ít thao tác hơn → người dùng ít bỏ cuộc giữa chừng.
- **Trải nghiệm nhất quán**: Mọi hệ thống đều hiển thị cùng một kết quả từ cùng một CCCD.

### 0.3 Lợi ích cho vận hành/CSKH

- **Giảm chi phí sửa dữ liệu**: Ít case sai thông tin → CSKH đỡ phải gọi/nhắn xác minh, đỡ thao tác chỉnh sửa.
- **Dữ liệu đồng nhất**: Một CCCD ra một kết quả thống nhất ở mọi hệ thống → báo cáo ít lệch, ít tranh cãi.
- **Giảm thời gian đối soát**: KYC/CRM/BI đồng nhất → số liệu báo cáo chính xác hơn.

### 0.4 Lợi ích cho kỹ thuật/IT

- **Chỉ cập nhật một nơi**: Khi có thay đổi quy tắc hoặc cập nhật tên tỉnh/thành (ví dụ: sáp nhập 64 → 34 tỉnh), chỉ cần cập nhật API.
- **Tích hợp nhanh**: Ứng dụng/đối tác chỉ cần gọi API, không phải tự xây logic riêng.
- **Tiết kiệm chi phí kỹ thuật**: Không phải duy trì "nhiều phiên bản xử lý CCCD" ở nhiều hệ thống.

### 0.5 Giải quyết vấn đề "tỉnh/thành sáp nhập"

- **Vấn đề**: Khi tỉnh/thành sáp nhập hoặc đổi tên, mỗi hệ thống cập nhật theo lịch khác nhau → cùng một người nhưng hiển thị tỉnh khác nhau ở các nơi.
- **Giải pháp**: Bảng tên tỉnh/thành được cập nhật tập trung trong API. Các hệ thống khác chỉ "dùng kết quả từ API", không phải tự cập nhật danh sách tỉnh/thành ở từng nơi.

### 0.6 Tiết kiệm chi phí tổng thể

- **Tiết kiệm chi phí vận hành**: Giảm số lần CSKH phải hỗ trợ/sửa hồ sơ do sai thông tin cơ bản.
- **Tiết kiệm chi phí kỹ thuật**: Không phải duy trì logic xử lý CCCD ở nhiều hệ thống.
- **Tăng doanh thu gián tiếp**: Ít bước hơn, ít lỗi hơn → tỷ lệ hoàn tất quy trình cao hơn.

---

## 1. Tổng quan hệ thống

### 1.1 Mục tiêu

Hệ thống CCCD API là một **API service** cho phép các ứng dụng khác gửi số CCCD và nhận về thông tin đã được parse:
- Tỉnh/Thành (`province_name`)
- Giới tính (`gender`)
- Năm sinh (`birth_year`)
- Các thông tin bổ sung: `province_code`, `age`, `century`

### 1.2 Kiến trúc tổng thể

Hệ thống được xây dựng theo mô hình **3-tier architecture**:

```
┌─────────────────────────────────────────┐
│         Client Applications             │
│  (Web, Mobile, Backend Services)        │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON
               ▼
┌─────────────────────────────────────────┐
│         Flask Application Layer         │
│  - Routes (API endpoints)               │
│  - Authentication & Authorization       │
│  - Rate Limiting                        │
│  - Error Handling                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Business Logic Layer            │
│  - Services (CCCD parser, User mgmt)    │
│  - Validation & Mapping                 │
│  - Email Service                         │
│  - Billing Service                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Data Layer                      │
│  - MySQL Database                        │
│  - JSON Data Files (Provinces)          │
│  - File System (Logs)                   │
└─────────────────────────────────────────┘
```

### 1.3 Các thành phần chính

1. **API Core**: Xử lý parse CCCD và trả về kết quả
2. **Portal**: Web interface cho users quản lý API keys và xem usage
3. **Admin Dashboard**: Quản lý users, keys, payments
4. **Authentication System**: User registration, login, password reset
5. **Billing System**: Subscription tiers, payment management

---

## 2. Công nghệ và thư viện

### 2.1 Backend Framework

- **Flask**: Web framework chính
- **Python 3.10+**: Ngôn ngữ lập trình

### 2.2 Database

- **MySQL**: Database chính cho users, API keys, subscriptions, payments
- **PyMySQL**: MySQL connector cho Python

### 2.3 Authentication & Security

- **bcrypt**: Hash passwords
- **Flask-Limiter**: Rate limiting
- **Session-based auth**: Flask sessions với permanent cookies

### 2.4 Frontend

- **Tailwind CSS**: Utility-first CSS framework (CDN)
- **Material Symbols**: Icon library
- **Chart.js**: Charts cho usage statistics
- **Vanilla JavaScript**: Không dùng framework JS

### 2.5 Email Service

- **SMTP**: Gửi email verification, password reset
- **smtplib**: Python SMTP library

### 2.6 Testing

- **pytest**: Unit testing framework

---

## 3. Cấu trúc thư mục dự án

```
CCCD-API/
├── app/                    # Flask application
│   ├── __init__.py        # App factory và config
│   ├── config.py          # Settings và configuration
│   ├── templates/         # Jinja2 templates
│   │   ├── portal/       # Portal pages
│   │   ├── admin.html    # Admin dashboard
│   │   ├── docs.html     # API documentation
│   │   └── 404.html      # Custom error page
│   └── static/           # Static files
│       ├── css/          # Stylesheets
│       └── js/           # JavaScript files
├── routes/                # Route handlers
│   ├── cccd.py          # Main API endpoint
│   ├── portal.py        # Portal routes
│   ├── admin.py         # Admin routes
│   └── health.py        # Health check
├── services/             # Business logic
│   ├── cccd_parser.py   # CCCD parsing logic
│   ├── province_mapping.py  # Province mapping
│   ├── user_service.py  # User management
│   ├── api_key_service.py   # API key management
│   ├── billing_service.py   # Billing & subscriptions
│   ├── usage_service.py     # Usage tracking
│   ├── email_service.py     # Email sending
│   └── logging_service.py  # Request logging
├── data/                 # Data files
│   ├── provinces_legacy_63.json
│   └── provinces_current_34.json
├── tests/                # Test files
├── scripts/              # Utility scripts
│   ├── db_schema.sql    # Database schema
│   ├── generate_keys.py  # Key generation
│   └── migrate_*.py     # Migration scripts
├── docs/                 # Documentation
│   ├── api/             # API documentation
│   ├── guides/          # Step-by-step guides
│   └── project/        # Project docs
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in repo)
├── run.py              # Development server entry
└── wsgi.py             # Production WSGI entry
```

---

## 4. Quy trình xây dựng từ đầu

### 4.1 Phase 1: Setup cơ bản

1. **Tạo cấu trúc project**
   - Tạo thư mục `app/`, `routes/`, `services/`, `data/`, `tests/`
   - Setup Flask app factory pattern
   - Cấu hình environment variables (`.env`)

2. **Database setup**
   - Thiết kế schema cho users, api_keys, subscriptions, payments
   - Tạo migration scripts
   - Setup MySQL connection

3. **API Core**
   - Implement CCCD parser (parse birth_year, gender, province_code)
   - Tạo province mapping service (legacy_63, current_34)
   - Implement validation logic

### 4.2 Phase 2: API Endpoint

1. **Main API endpoint**
   - Tạo route `POST /v1/cccd/parse`
   - Implement request validation
   - Implement response formatting
   - Add error handling (400, 429, 500)

2. **Security**
   - Implement API key authentication
   - Add rate limiting per API key
   - Mask CCCD trong logs
   - Add security headers (CSP, X-Frame-Options, etc.)

3. **Logging**
   - Implement request logging với request_id
   - Log errors với stacktrace (server-side only)
   - Log usage statistics

### 4.3 Phase 3: User Portal

1. **Authentication System**
   - User registration với email verification
   - Login/Logout với session management
   - Password reset flow (forgot → email → reset)
   - "Remember Me" với permanent sessions

2. **Portal Pages**
   - Dashboard: Hiển thị stats và subscription
   - API Keys: Create, delete, rotate, label management
   - Usage: Charts và statistics
   - Billing: Payment history và upgrade flow

3. **UI/UX**
   - Dark theme với Tailwind CSS
   - Responsive design
   - Material Symbols icons
   - Custom scrollbars
   - Flash messages

### 4.4 Phase 4: Admin Dashboard

1. **Admin Authentication**
   - Admin key từ environment variable
   - Session-based admin auth

2. **Admin Features**
   - User management (list, search, change tier, delete)
   - API key management (list, deactivate)
   - Payment management (approve/reject)
   - Statistics dashboard

### 4.5 Phase 5: Advanced Features

1. **Tier System**
   - Free, Premium, Ultra tiers
   - Rate limits per tier
   - Subscription management
   - Payment requests với admin approval

2. **Usage Tracking**
   - Track API calls per key
   - Store usage statistics
   - Generate charts và reports

3. **Email Service**
   - Email verification
   - Password reset emails
   - Key expiration reminders

4. **Error Handling**
   - Custom 404 page
   - JSON responses cho API errors
   - HTML pages cho web errors

---

## 5. Database Schema Design

### 5.1 Core Tables

- **users**: User accounts với email, password_hash, status
- **api_keys**: API keys với tier, owner, expiry
- **subscriptions**: User subscriptions với tier, status, expires_at
- **payments**: Payment records với status, amount, currency
- **api_usage**: Usage tracking per key per day
- **request_logs**: Detailed request logs (optional, for tiered mode)

### 5.2 Relationships

- `users` 1:N `api_keys` (user_id)
- `users` 1:1 `subscriptions` (user_id)
- `users` 1:N `payments` (user_id)
- `api_keys` 1:N `api_usage` (api_key_id)

---

## 6. API Design Principles

### 6.1 Response Format

Tất cả API responses đều theo format thống nhất:

```json
{
  "success": boolean,
  "is_valid_format": boolean,
  "is_plausible": boolean,
  "data": object | null,
  "message": string | null,
  "request_id": string,
  "warnings": array
}
```

### 6.2 Error Handling

- **400**: Input validation errors (rõ ràng, dễ hiểu)
- **401**: Authentication required
- **429**: Rate limit exceeded
- **500**: Internal server error (generic message, detailed log)

### 6.3 Security

- Không log CCCD đầy đủ (chỉ mask)
- Rate limiting per API key
- Input validation (độ dài, format)
- SQL injection prevention (parameterized queries)
- XSS prevention (template escaping)

---

## 7. Portal Design Principles

### 7.1 Authentication Flow

1. User đăng ký → Email verification required
2. User login → Session created
3. "Remember Me" → Permanent session (24h)
4. Password reset → Token-based với expiry

### 7.2 UI/UX Guidelines

- **Dark theme**: Consistent across all pages
- **Responsive**: Mobile-first design
- **Accessibility**: Proper labels, ARIA attributes
- **Performance**: Lazy loading, optimized assets
- **Error messages**: User-friendly, không expose technical details

### 7.3 State Management

- **Server-side sessions**: User authentication state
- **Flash messages**: Temporary notifications
- **AJAX requests**: Inline updates (không reload page)

---

## 8. Development Workflow

### 8.1 Local Development

1. Setup virtual environment
2. Install dependencies (`pip install -r requirements.txt`)
3. Copy `.env.example` to `.env` và fill values
4. Setup MySQL database và run migrations
5. Run development server: `python run.py`

### 8.2 Testing

1. **Unit tests**: Test individual functions (parser, validation, mapping)
2. **Integration tests**: Test API endpoints
3. **Manual testing**: Test portal flows (registration, login, key management)

### 8.3 Code Organization

- **Separation of concerns**: Routes → Services → Database
- **DRY principle**: Reuse code, avoid duplication
- **Single responsibility**: Mỗi function/class chỉ làm 1 việc
- **Error handling**: Try/except với proper logging

---

## 9. Deployment Considerations

### 9.1 Production Server

- **WSGI Server**: Gunicorn (Linux) hoặc Waitress (Windows)
- **Reverse Proxy**: Nginx (recommended)
- **Process Manager**: systemd hoặc supervisor

### 9.2 Environment Variables

- `FLASK_SECRET_KEY`: Session encryption key
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- `API_KEY_MODE`: `simple` hoặc `tiered`
- `BASE_URL`: Base URL cho email links
- `SMTP_*`: Email server configuration

### 9.3 Security in Production

- HTTPS only
- Secure session cookies (HttpOnly, Secure, SameSite)
- Rate limiting enabled
- Error messages generic (không expose stack traces)
- Regular security updates

---

## 10. Best Practices đã áp dụng

### 10.1 Code Quality

- **Input validation**: Luôn validate ở backend, không tin frontend
- **Error handling**: Catch exceptions, log details, return generic messages
- **Type hints**: Sử dụng type hints cho function signatures
- **Documentation**: Docstrings cho functions quan trọng

### 10.2 Security

- **Password hashing**: bcrypt với salt
- **SQL injection**: Parameterized queries only
- **XSS prevention**: Template escaping
- **CSRF protection**: Session-based với SameSite cookies
- **Rate limiting**: Prevent abuse

### 10.3 User Experience

- **Flash messages**: Clear, actionable error messages
- **Loading states**: Show feedback khi processing
- **Responsive design**: Works on mobile và desktop
- **Accessibility**: Proper semantic HTML

### 10.4 Maintainability

- **Modular structure**: Services tách biệt, dễ test
- **Configuration**: Environment variables, không hardcode
- **Logging**: Structured logging với request_id
- **Documentation**: README, guides, API docs

---

## 11. Lessons Learned

Xem file `lession_learn.md` để biết các bài học rút ra trong quá trình phát triển, bao gồm:

- Overflow strategy cho scrollbars
- Function return signature phải khớp
- Database column names phải consistent
- Custom error pages
- Và nhiều bài học khác...

---

## 12. Tài liệu tham khảo

- **API Documentation**: `docs/api/README.md`
- **Step-by-step Guides**: `docs/guides/guide_step_*.md`
- **Requirements**: `docs/project/requirement.md`
- **Checklist**: `docs/project/checklist.md`
- **Issues & Solutions**: `docs/project/issues_list.md`

---

## 13. Kết luận

Hệ thống CCCD API được xây dựng theo nguyên tắc:
- **Modular**: Dễ maintain và extend
- **Secure**: Bảo mật từ đầu đến cuối
- **User-friendly**: UI/UX tốt, error messages rõ ràng
- **Scalable**: Có thể mở rộng với nhiều users và requests
- **Well-documented**: Đầy đủ tài liệu cho developers

Để bắt đầu, hãy xem các file guide từng bước trong `docs/guides/` và follow checklist trong `docs/project/checklist.md`.
