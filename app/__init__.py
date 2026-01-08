from flask import Flask

from app.config import Settings
from routes.health import health_bp


def create_app() -> Flask:
    app = Flask(__name__)

    settings = Settings.from_env()
    app.config["SETTINGS"] = settings

    # Routes
    app.register_blueprint(health_bp)

    return app


