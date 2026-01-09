import os

from dotenv import load_dotenv

from app import create_app

load_dotenv()

flask_app = create_app()
# Note: Server header removal is handled in app/__init__.py via wsgi_app wrapper
app = flask_app  # For compatibility with wsgi.py

if __name__ == "__main__":
    settings = flask_app.config.get("SETTINGS")
    port = getattr(settings, "port", 8000)
    flask_app.run(host="0.0.0.0", port=port, debug=True)


