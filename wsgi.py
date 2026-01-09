from dotenv import load_dotenv

from app import create_app

load_dotenv()

app = create_app()
# Note: Server header removal is handled in app/__init__.py via wsgi_app wrapper


