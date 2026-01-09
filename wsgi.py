from dotenv import load_dotenv

from app import create_app

load_dotenv()

app = create_app()

# WSGI middleware to remove Server header (for production with gunicorn)
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

# Wrap app with middleware for production
app = RemoveServerHeaderMiddleware(app)


