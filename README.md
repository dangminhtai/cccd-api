# CCCD API

<div align="center">

**A production-ready REST API service for parsing Vietnamese Citizen ID Card (CCCD) numbers**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)](https://github.com/dangminhtai/cccd-api)

[Features](#-features) • [Quick Start](#-quick-start) • [API Documentation](#-api-documentation) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Authentication](#-authentication)
- [Rate Limiting](#-rate-limiting)
- [Portal & Admin Dashboard](#-portal--admin-dashboard)
- [Security](#-security)
- [Deployment](#-deployment)
- [Development](#-development)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**CCCD API** is a comprehensive REST API service that extracts structured information from Vietnamese Citizen ID Card (CCCD) numbers. It provides a centralized, reliable solution for parsing CCCD data, eliminating the need for each application to implement its own parsing logic.

### Why CCCD API?

- **Reduce Manual Input**: Automatically extract province, gender, and birth year from CCCD numbers
- **Prevent Data Errors**: Eliminate human errors in data entry
- **Centralized Updates**: Single source of truth for province mappings (handles administrative changes like 64→34 province merge)
- **Standardized Format**: Consistent data format across all applications
- **Production Ready**: Built with security, scalability, and reliability in mind

---

## ✨ Features

### Core Functionality

- ✅ **CCCD Parsing**: Extract province, gender, birth year from 12-digit CCCD numbers
- ✅ **Dual Province Support**: Handles both `legacy_63` (old 63 provinces) and `current_34` (new 34 provinces) formats
- ✅ **Data Validation**: Comprehensive input validation with clear error messages
- ✅ **Plausibility Checks**: Validates birth year, gender, and province code consistency

### Security & Authentication

- 🔐 **API Key Authentication**: Secure API key-based authentication
- 🔐 **Tiered Access Control**: Free, Premium, and Ultra tiers with different rate limits
- 🔐 **Session-based Portal**: User portal with secure session management
- 🔐 **Admin Dashboard**: Separate admin authentication with brute force protection
- 🔐 **Rate Limiting**: Configurable rate limits per tier
- 🔐 **Secure Logging**: Masked CCCD in logs for privacy

### User Portal

- 🌐 **Web Dashboard**: Modern dark-themed user interface
- 🔑 **API Key Management**: Create, delete, label, and manage API keys
- 📊 **Usage Statistics**: Real-time usage tracking and charts
- 💳 **Billing & Subscriptions**: Payment management and tier upgrades
- 📧 **Email Verification**: Secure email verification system
- 🔄 **Password Reset**: Token-based password reset flow

### Admin Features

- 👨‍💼 **Admin Dashboard**: Comprehensive admin control panel
- 👥 **User Management**: View, search, and manage users
- 💰 **Payment Management**: Approve/reject payment requests
- 📈 **Analytics**: System-wide statistics and monitoring
- 🔒 **Security Monitoring**: Failed login attempts and IP blocking

### Developer Experience

- 📚 **Comprehensive Documentation**: API docs, guides, and examples
- 🧪 **Test Suite**: Unit tests and integration tests
- 🔧 **Easy Setup**: Simple installation and configuration
- 📦 **SDK Support**: Python SDK available
- 🐛 **Error Handling**: Clear, actionable error messages

---

## 🏗️ Architecture

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

### Technology Stack

- **Backend**: Python 3.10+, Flask
- **Database**: MySQL (for tiered mode)
- **Authentication**: bcrypt, Flask sessions
- **Frontend**: Tailwind CSS, Material Symbols, Vanilla JavaScript
- **Email**: SMTP
- **Testing**: pytest

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- MySQL 5.7+ (for tiered mode with user management)
- pip

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/dangminhtai/cccd-api.git
cd cccd-api
```

2. **Create virtual environment** (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp env.example .env
```

Edit `.env` with your settings:

```env
# Server
PORT=8000
FLASK_ENV=development

# API Configuration
DEFAULT_PROVINCE_VERSION=current_34
API_KEY_MODE=simple  # or 'tiered' for full features

# For simple mode (optional)
API_KEY=your-api-key-here

# For tiered mode (required)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=cccd_api

# Security
FLASK_SECRET_KEY=your-secret-key-here
ADMIN_SECRET=your-admin-secret-key-here

# Email (for user verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
BASE_URL=http://localhost:8000
```

5. **Setup database** (if using tiered mode)

```bash
mysql -u root -p cccd_api < scripts/db_schema.sql
mysql -u root -p cccd_api < scripts/db_schema_portal.sql
mysql -u root -p cccd_api < scripts/db_schema_admin.sql
```

6. **Run the server**

```bash
python run.py
```

The API will be available at `http://127.0.0.1:8000`

### Verify Installation

```bash
curl -X POST http://127.0.0.1:8000/v1/cccd/parse \
  -H "Content-Type: application/json" \
  -d '{"cccd": "079203012345"}'
```

---

## 📖 API Documentation

### Base URL

```
http://localhost:8000/v1
```

### Endpoints

#### `POST /v1/cccd/parse`

Parse information from a CCCD number.

**Request Headers:**
```
Content-Type: application/json
X-API-Key: <your-api-key>  # Required if API_KEY_MODE is enabled
```

**Request Body:**
```json
{
  "cccd": "079203012345",
  "province_version": "current_34"  // Optional: "legacy_63" | "current_34"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "is_valid_format": true,
  "is_plausible": true,
  "province_version": "current_34",
  "data": {
    "province_code": "079",
    "province_name": "Thành phố Hồ Chí Minh",
    "gender": "Nam",
    "birth_year": 2003,
    "century": 21,
    "age": 21
  },
  "message": null,
  "request_id": "abc12345",
  "warnings": []
}
```

**Error Responses:**

**400 Bad Request** - Invalid input:
```json
{
  "success": false,
  "is_valid_format": false,
  "data": null,
  "message": "CCCD không hợp lệ (cần là chuỗi số, độ dài 12).",
  "request_id": "abc12345"
}
```

**401 Unauthorized** - Invalid or missing API key:
```json
{
  "success": false,
  "message": "API key không hợp lệ hoặc thiếu.",
  "request_id": "abc12345"
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "success": false,
  "message": "Rate limit exceeded. Please try again later.",
  "request_id": "abc12345"
}
```

### Response Format

All API responses follow a consistent format:

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request was successful |
| `is_valid_format` | boolean | Whether the CCCD format is valid |
| `is_plausible` | boolean | Whether the parsed data is plausible |
| `data` | object\|null | Parsed data (null on error) |
| `message` | string\|null | Error or info message |
| `request_id` | string | Unique request identifier for tracking |
| `warnings` | array | Array of warning messages |

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `province_code` | string | 3-digit province code (e.g., "079") |
| `province_name` | string | Full province name |
| `gender` | string | "Nam" or "Nữ" |
| `birth_year` | integer | Birth year (e.g., 2003) |
| `century` | string | Century indicator ("20" or "21") |
| `age` | integer | Calculated age |

---

## 🔐 Authentication

### API Key Authentication

API keys are required when `API_KEY_MODE` is set to `simple` or `tiered`.

**Simple Mode:**
- Single API key for all requests
- Configured via `API_KEY` in `.env`

**Tiered Mode:**
- Multiple API keys per user
- Keys are tied to user accounts and tiers
- Rate limits vary by tier:
  - **Free**: 10 requests/minute
  - **Premium**: 100 requests/minute
  - **Ultra**: 1000 requests/minute

### Getting an API Key

1. **Register** at `/portal/register`
2. **Verify** your email
3. **Create** an API key in the dashboard
4. **Use** the key in `X-API-Key` header

---

## ⚡ Rate Limiting

Rate limits are enforced per API key:

| Tier | Rate Limit |
|------|------------|
| Free | 10 requests/minute |
| Premium | 100 requests/minute |
| Ultra | 1000 requests/minute |

When rate limit is exceeded, the API returns `429 Too Many Requests`.

---

## 🌐 Portal & Admin Dashboard

### User Portal

Access the user portal at `/portal`:

- **Dashboard**: Overview of your account and API usage
- **API Keys**: Create, manage, and delete API keys
- **Usage**: View detailed usage statistics and charts
- **Billing**: Payment history and subscription management
- **Upgrade**: Request tier upgrades

### Admin Dashboard

Access the admin dashboard at `/admin`:

- **Statistics**: System-wide statistics
- **User Management**: View and manage users
- **Payment Management**: Approve/reject payment requests
- **API Key Management**: Create and manage API keys
- **Security Monitoring**: View blocked IPs and failed attempts

**Default Admin Credentials** (change immediately in production):
- Username: `admin`
- Password: `admin123`

---

## 🔒 Security

### Security Features

- ✅ **Password Hashing**: bcrypt with salt
- ✅ **SQL Injection Prevention**: Parameterized queries
- ✅ **XSS Prevention**: Template escaping
- ✅ **CSRF Protection**: Session-based with SameSite cookies
- ✅ **Rate Limiting**: Prevents abuse
- ✅ **Brute Force Protection**: IP blocking after failed attempts
- ✅ **Secure Headers**: CSP, X-Frame-Options, X-XSS-Protection
- ✅ **Masked Logging**: CCCD numbers are masked in logs
- ✅ **Input Validation**: Comprehensive server-side validation

### Security Best Practices

1. **Change default admin password** immediately
2. **Use strong API keys** (32+ characters)
3. **Enable HTTPS** in production
4. **Set secure `FLASK_SECRET_KEY`** in `.env`
5. **Regular security updates**
6. **Monitor failed login attempts**

For detailed security testing guides, see [`docs/security/`](docs/security/).

---

## 🚢 Deployment

### Production Setup

1. **Use a production WSGI server**

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "wsgi:app"
```

2. **Use Nginx as reverse proxy**

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Use systemd for process management**

Create `/etc/systemd/system/cccd-api.service`:

```ini
[Unit]
Description=CCCD API Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/cccd-api
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "wsgi:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Enable HTTPS** with Let's Encrypt

```bash
certbot --nginx -d api.example.com
```

### Docker Deployment

```bash
# Build image
docker build -t cccd-api .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name cccd-api \
  cccd-api
```

See [`docker-compose.yml`](docker-compose.yml) for full Docker setup.

---

## 💻 Development

### Project Structure

```
CCCD-API/
├── app/                    # Flask application
│   ├── __init__.py        # App factory và config
│   ├── config.py          # Settings và configuration
│   ├── templates/         # Jinja2 templates
│   │   ├── portal/       # Portal pages
│   │   ├── admin.html    # Admin dashboard
│   │   └── docs.html     # API documentation
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
│   └── migrate_*.py     # Migration scripts
├── docs/                 # Documentation
│   ├── api/             # API documentation
│   ├── guides/          # Step-by-step guides
│   ├── security/        # Security docs
│   └── project/         # Project docs
├── requirements.txt     # Python dependencies
├── run.py              # Development server entry
└── wsgi.py             # Production WSGI entry
```

### Running in Development

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run development server
python run.py

# Server runs at http://127.0.0.1:8000
```

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where possible
- Write docstrings for functions
- Keep functions focused and small

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_cccd_parser.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Coverage

- Unit tests for parsing logic
- Integration tests for API endpoints
- Security tests for authentication
- Validation tests for input handling

See [`docs/testing/`](docs/testing/) for detailed testing documentation.

---

## 📚 Documentation

### Available Documentation

- **[API Reference](docs/api/README.md)**: Complete API documentation
- **[Quick Start Guide](docs/guides/guide_step_00.md)**: Step-by-step setup
- **[Security Guide](docs/security/security_testing_guide.md)**: Security testing
- **[Project Requirements](docs/project/requirement.md)**: Detailed requirements
- **[Implementation Guide](docs/project/update_guide.md)**: How the system was built
- **[Lessons Learned](docs/project/lession_learn.md)**: Development insights

### API Examples

See [`docs/api/examples/`](docs/api/examples/) for code examples in:
- Python
- JavaScript
- PHP
- cURL

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Write tests** for new features
5. **Ensure all tests pass** (`python -m pytest`)
6. **Commit your changes** (`git commit -m 'Add amazing feature'`)
7. **Push to the branch** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request**

### Development Guidelines

- Write clear commit messages
- Add tests for new features
- Update documentation as needed
- Follow existing code style
- Ensure backward compatibility

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Vietnamese administrative data for province mappings
- Flask community for the excellent framework
- All contributors and users of this project

---

## 📞 Support

- **Documentation**: See [`docs/`](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/dangminhtai/cccd-api/issues)
- **Email**: Contact via GitHub profile

---

<div align="center">

**Made with ❤️ for the Vietnamese developer community**

[⭐ Star this repo](https://github.com/dangminhtai/cccd-api) if you find it useful!

</div>