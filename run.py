import os
import threading
import webbrowser

from dotenv import load_dotenv

from app import create_app

load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))

    def open_demo():
        url = f"http://127.0.0.1:{port}/demo"
        try:
            webbrowser.open(url)
        except Exception:
            pass

    # In debug mode, Flask reloader starts the app twice; only open browser in the reloader child.
    if os.getenv("WERKZEUG_RUN_MAIN") == "true" or os.getenv("FLASK_ENV") != "development":
        threading.Timer(0.8, open_demo).start()

    app.run(host="0.0.0.0", port=port, debug=True)


