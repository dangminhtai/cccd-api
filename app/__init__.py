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
    
    # IMPORTANT: FLASK_SECRET_KEY must be set in .env for "Remember Me" to work across server restarts
    # If secret_key changes, all existing session cookies become invalid
    flask_secret_key = os.getenv("FLASK_SECRET_KEY")
    if not flask_secret_key:
        # Generate a random key as fallback, but warn user
        flask_secret_key = secrets.token_hex(32)
        import warnings
        warnings.warn(
            "FLASK_SECRET_KEY not set in .env. "
            "Sessions will be invalidated on server restart. "
            "Set FLASK_SECRET_KEY in .env for persistent sessions.",
            UserWarning
        )
    app.secret_key = flask_secret_key
    
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
        # Allow Google Fonts for Material Symbols icons
        # Allow Tailwind CSS CDN for login page
        # In production, consider removing 'unsafe-inline' and using nonces/hashes
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; worker-src 'self' blob:;"
        
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

    # API Documentation endpoint (static HTML page)
    @app.route("/docs")
    @app.route("/api-docs")
    def api_docs():
        """API Documentation - static HTML page với examples và hướng dẫn"""
        from flask import render_template
        return render_template("docs.html")

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


