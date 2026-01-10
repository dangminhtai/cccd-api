import os

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def index():
    return (
        jsonify(
            {
                "message": "CCCD API is running. Try GET /health",
                "health": "/health",
            }
        ),
        200,
    )


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@health_bp.get("/test-500")
def test_500():
    """Only works in development mode. Used to test 500 error handling."""
    if os.getenv("FLASK_ENV") != "development":
        return jsonify({"message": "Only available in development"}), 403
    raise RuntimeError("This is a test error for step 7")

