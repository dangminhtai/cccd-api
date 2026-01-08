from flask import Flask, request
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

    settings = Settings.from_env()
    app.config["SETTINGS"] = settings

    limiter.init_app(app)

    # Routes
    from routes.health import health_bp
    from routes.cccd import cccd_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(cccd_bp)

    return app


