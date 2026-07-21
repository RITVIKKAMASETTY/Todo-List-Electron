"""
jupyter_run.py
==============
Run this from a Jupyter Notebook cell to start the Digital Twin server
WITHOUT blocking the notebook.

The server runs in a background thread, so you can keep using Jupyter
while the dashboard is live at http://127.0.0.1:8000

USAGE (in a Jupyter Notebook cell):
    %run jupyter_run.py

OR:
    exec(open('jupyter_run.py').read())
"""

import threading
import time
import webbrowser
import sys
import os

# ── Make sure the project root is in the Python path ──────────────
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_server():
    """Start Uvicorn server in background thread."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="warning"   # quieter logs inside Jupyter
    )


def open_browser_delayed(delay=3.0):
    """Open browser after server has had time to start."""
    def _open():
        time.sleep(delay)
        webbrowser.open("http://127.0.0.1:8000")
    threading.Thread(target=_open, daemon=True).start()


# ── Check if server is already running ────────────────────────────
import socket

def is_port_in_use(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if is_port_in_use(8000):
    print("=" * 55)
    print("  Server is already running!")
    print("  Dashboard → http://127.0.0.1:8000")
    print("=" * 55)
    webbrowser.open("http://127.0.0.1:8000")
else:
    print("=" * 55)
    print("  Digital Twin — Zirconia Oxygen Sensor (OBOGS)")
    print("  Starting server in background...")
    print("=" * 55)

    # Start server thread (daemon=True means it stops when Jupyter stops)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Open browser after 3 seconds
    open_browser_delayed(delay=3.0)

    print("  ✓ Server starting at http://127.0.0.1:8000")
    print("  ✓ Browser will open in 3 seconds")
    print("  ✓ Jupyter notebook remains usable")
    print("=" * 55)
    print()
    print("  To STOP the server: Kernel → Restart (in Jupyter)")
    print("  OR close the Jupyter Notebook tab")
