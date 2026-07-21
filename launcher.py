"""
Launcher — Entry point for the packaged .exe application.

Starts the Uvicorn server and auto-opens the browser to the dashboard.
This is what PyInstaller will bundle as the main entry point.
"""

import sys
import os
import webbrowser
import threading
import time


def get_base_path():
    """Get the base path for bundled application or development."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_browser(port=8000, delay=2.0):
    """Open the dashboard in the default browser after a delay."""
    def _open():
        time.sleep(delay)
        url = f"http://127.0.0.1:{port}"
        print(f"\n  Opening browser: {url}\n")
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def main():
    """Main entry point."""
    # Ensure the app directory is in the Python path
    base_path = get_base_path()
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    port = 8000
    host = "127.0.0.1"

    print("=" * 60)
    print("  Digital Twin: Zirconia Oxygen Sensor (OBOGS)")
    print("=" * 60)
    print(f"  Server: http://{host}:{port}")
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)

    # Open browser
    open_browser(port)

    # Start Uvicorn server
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
