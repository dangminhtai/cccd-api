import os
import threading
import webbrowser

from dotenv import load_dotenv

from app import create_app

load_dotenv()

flask_app = create_app()

# WSGI middleware to remove Server header (works for development server too)
class RemoveServerHeaderMiddleware:
    """WSGI middleware to remove Server header from all responses"""
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            # Remove Server header from response headers
            headers = [(name, value) for name, value in headers if name.lower() != 'server']
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)

# Wrap app with middleware for WSGI servers (gunicorn, etc.)
app = RemoveServerHeaderMiddleware(flask_app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))

    def open_demo():
        url = f"http://127.0.0.1:{port}/demo"
        try:
            webbrowser.open(url)
        except Exception:
            pass

    # In debug mode, Flask reloader starts the app twice.
    # Only open browser in the reloader child; in non-debug mode open once.
    is_reloader_child = os.getenv("WERKZEUG_RUN_MAIN", "").lower() == "true"
    is_debug_env = os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1"

    if (is_debug_env and is_reloader_child) or (not is_debug_env and not is_reloader_child):
        threading.Timer(0.8, open_demo).start()

    # Use flask_app (not wrapped middleware) for .run() method
    flask_app.run(host="0.0.0.0", port=port, debug=True)


