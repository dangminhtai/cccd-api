import secrets
import traceback
import uuid

from flask import Flask, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import Settings


def _rate_limit_key():
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    return get_remote_address()


limiter = Limiter(key_func=_rate_limit_key, default_limits=["30 per minute"], storage_uri="memory://")


def create_app() -> Flask:
    app = Flask(__name__)
    
    # Session configuration for user authentication
    import os
    from datetime import timedelta
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)  # 24 hours (for remember me)
    # Note: Regular sessions (without remember me) expire when browser closes
    # Permanent sessions (with remember me) last 24 hours

    # Allow Vietnamese characters in JSON responses (no Unicode escape)
    app.json.ensure_ascii = False

    settings = Settings.from_env()
    app.config["SETTINGS"] = settings

    limiter.init_app(app)

    # Generate request_id for each request (for tracing)
    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]

    # Remove Server header to prevent information disclosure
    # Note: Werkzeug development server adds Server header AFTER after_request runs
    # This means we cannot fully remove it in dev mode
    # Solution: 
    # - Development: Accept Server header leak (low risk for local/dev)
    # - Production: Use Gunicorn + Nginx (Server header automatically removed by Nginx)
    @app.after_request
    def add_security_headers(response):
        """Add security headers and remove Server header"""
        # Remove Server header to prevent leaking framework/version information
        # This works for production (Gunicorn), but not for Werkzeug dev server
        # Werkzeug dev server adds Server header after this handler runs
        response.headers.pop("Server", None)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy: restrict resources to same origin
        # Note: Allow inline scripts/styles for demo.html (needed for the demo page)
        # In production, consider removing 'unsafe-inline' and using nonces/hashes
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
        
        # Strict-Transport-Security: only add if using HTTPS
        # For local development (HTTP), we skip this header
        # In production with HTTPS, uncomment the line below:
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

    # Custom 429 handler to return JSON instead of HTML
    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f"rate_limited | request_id={g.get('request_id', '-')} | {e.description}")
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": f"Quá nhiều request. Giới hạn: {e.description}",
                }
            ),
            429,
        )

    # Custom 500 handler: generic message to client, concise log
    @app.errorhandler(500)
    def internal_error_handler(e):
        req_id = g.get("request_id", "-")
        # Concise log: only error type and message, no full stacktrace
        app.logger.error(f"internal_error | request_id={req_id} | {type(e).__name__}: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": "Lỗi hệ thống. Vui lòng thử lại sau.",
                    "request_id": req_id,
                }
            ),
            500,
        )

    # Catch-all for unhandled exceptions (but NOT HTTP exceptions like 404)
    @app.errorhandler(Exception)
    def unhandled_exception_handler(e):
        # Let HTTP exceptions (404, 405, etc.) be handled by Flask default
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e
        req_id = g.get("request_id", "-")
        # Concise log: type, message, and location (last frame)
        tb_lines = traceback.format_exc().strip().split("\n")
        location = tb_lines[-2].strip() if len(tb_lines) >= 2 else "-"
        app.logger.error(f"unhandled_exception | request_id={req_id} | {type(e).__name__}: {e} | at: {location}")
        return (
            jsonify(
                {
                    "success": False,
                    "is_valid_format": False,
                    "data": None,
                    "message": "Lỗi hệ thống. Vui lòng thử lại sau.",
                    "request_id": req_id,
                }
            ),
            500,
        )

    # Swagger/OpenAPI documentation
    try:
        from flasgger import Swagger
        import os
        
        swagger_config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": "apispec",
                    "route": "/apispec.json",
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/api-docs",
        }
        
        swagger_template = {
            "swagger": "2.0",
            "info": {
                "title": "CCCD API",
                "description": "API để parse thông tin từ số CCCD (Căn cước công dân) 12 chữ số của Việt Nam.\n\n## Authentication\nAPI yêu cầu API key được gửi qua header `X-API-Key`.\n\n## Rate Limits\n- **Free**: 10 requests/minute\n- **Premium**: 100 requests/minute\n- **Ultra**: 1000 requests/minute\n\n## Error Handling\nTất cả errors trả về JSON với format:\n```json\n{\n  \"success\": false,\n  \"is_valid_format\": false,\n  \"data\": null,\n  \"message\": \"Error message\"\n}\n```",
                "version": "1.0.0",
                "contact": {
                    "name": "API Support",
                    "email": "support@cccd-api.com",
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT",
                },
            },
            "host": os.getenv("API_DOCS_HOST", "127.0.0.1:8000"),
            "basePath": "/",
            "schemes": ["http", "https"],
            "securityDefinitions": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for authentication. Lấy từ Customer Portal sau khi đăng ký.",
                }
            },
        }
        
        swagger = Swagger(app, config=swagger_config, template=swagger_template)
        app.logger.info("Swagger/OpenAPI documentation enabled at /api-docs and /docs")
        
        # Add redirect from /docs to /api-docs for convenience
        @app.route("/docs")
        def docs_redirect():
            """Redirect /docs to /api-docs for convenience"""
            from flask import redirect
            return redirect("/api-docs", code=301)
            
    except ImportError:
        app.logger.warning("flasgger not installed. Install with: pip install flasgger")
        
        # Add a simple HTML page at /docs explaining how to install flasgger
        @app.route("/docs")
        @app.route("/api-docs")
        def docs_missing():
            from flask import render_template_string
            return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation - flasgger Required</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        .install { background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .error { color: #d32f2f; }
    </style>
</head>
<body>
    <h1>API Documentation</h1>
    <p class="error">Swagger UI chưa được kích hoạt vì <code>flasgger</code> chưa được cài đặt.</p>
    <div class="install">
        <h2>Để kích hoạt API Documentation:</h2>
        <ol>
            <li>Cài đặt <code>flasgger</code>:
                <pre><code>pip install flasgger</code></pre>
            </li>
            <li>Hoặc cài đặt tất cả dependencies:
                <pre><code>pip install -r requirements.txt</code></pre>
            </li>
            <li>Restart server:
                <pre><code>py run.py</code></pre>
            </li>
            <li>Truy cập lại <a href="/docs">/docs</a> hoặc <a href="/api-docs">/api-docs</a></li>
        </ol>
    </div>
    <h2>Documentation Files</h2>
    <p>Bạn có thể xem tài liệu offline tại:</p>
    <ul>
        <li><a href="/docs/api/README.md">docs/api/README.md</a> - Main API documentation</li>
        <li><a href="/docs/api/ERROR_CODES.md">docs/api/ERROR_CODES.md</a> - Error codes reference</li>
        <li><a href="/docs/api/RATE_LIMITS.md">docs/api/RATE_LIMITS.md</a> - Rate limits documentation</li>
        <li><a href="/docs/api/openapi.yaml">docs/api/openapi.yaml</a> - OpenAPI 3.0 specification</li>
    </ul>
</body>
</html>
            """), 503
    except Exception as e:
        app.logger.warning(f"Failed to initialize Swagger: {e}")
        
        @app.route("/docs")
        @app.route("/api-docs")
        def docs_error():
            from flask import render_template_string
            return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation - Error</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        .error {{ background: #ffebee; padding: 20px; border-radius: 8px; color: #c62828; }}
    </style>
</head>
<body>
    <h1>API Documentation - Error</h1>
    <div class="error">
        <p><strong>Lỗi khi khởi tạo Swagger UI:</strong></p>
        <pre>{e}</pre>
    </div>
    <p>Vui lòng kiểm tra logs để biết thêm chi tiết.</p>
</body>
</html>
            """), 500

    # Routes
    from routes.health import health_bp
    from routes.cccd import cccd_bp
    from routes.portal import portal_bp
    
    # Root route - redirect to portal
    @app.route("/")
    def root():
        """Redirect root to portal login or dashboard"""
        from flask import redirect, session, url_for
        # Nếu đã đăng nhập, redirect đến dashboard
        if "user_id" in session:
            return redirect(url_for("portal.dashboard"))
        # Nếu chưa đăng nhập, redirect đến login
        return redirect(url_for("portal.login"))

    app.register_blueprint(health_bp)
    app.register_blueprint(cccd_bp)
    app.register_blueprint(portal_bp)

    # Admin routes (only if tiered mode is enabled)
    import os
    if os.getenv("API_KEY_MODE") == "tiered":
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp)

    return app


