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


