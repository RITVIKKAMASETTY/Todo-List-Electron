"""
Launcher — starts Flask server and opens browser automatically.
Works in both development and as a packaged .exe.
"""

import sys
import os
import webbrowser
import threading
import time


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_browser(port=8000, delay=2.5):
    def _open():
        time.sleep(delay)
        webbrowser.open(f"http://127.0.0.1:{port}")
    threading.Thread(target=_open, daemon=True).start()


def main():
    base_path = get_base_path()
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    port = 8000

    # Open browser
    open_browser(port)

    # Try waitress first (production-grade Windows WSGI server)
    # Fall back to Flask's built-in dev server
    from app.main import app

    try:
        from waitress import serve
        print(f"\n  Serving on http://127.0.0.1:{port}")
        print("  Close this window to stop.\n")
        serve(app, host="127.0.0.1", port=port, threads=4)
    except ImportError:
        print("  waitress not found — using Flask dev server")
        print(f"  Serving on http://127.0.0.1:{port}")
        app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
