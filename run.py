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

    # In debug mode, Flask reloader starts the app twice.
    # Only open browser in the reloader child; in non-debug mode open once.
    is_reloader_child = os.getenv("WERKZEUG_RUN_MAIN", "").lower() == "true"
    is_debug_env = os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1"

    if (is_debug_env and is_reloader_child) or (not is_debug_env and not is_reloader_child):
        threading.Timer(0.8, open_demo).start()

    app.run(host="0.0.0.0", port=port, debug=True)


