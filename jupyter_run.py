"""
jupyter_run.py — Start the Flask Digital Twin server from a Jupyter cell.

USAGE (in a Jupyter Notebook cell):
    %run jupyter_run.py
"""

import threading, time, webbrowser, sys, os, socket

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def is_port_free(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0

def run_server():
    from app.main import app
    app.run(host="127.0.0.1", port=8000, debug=False, threaded=True, use_reloader=False)

def open_browser_after(delay=3.0):
    def _open():
        time.sleep(delay)
        webbrowser.open("http://127.0.0.1:8000")
    threading.Thread(target=_open, daemon=True).start()

print()
print("╔══════════════════════════════════════════════╗")
print("║  Digital Twin — Zirconia Oxygen Sensor       ║")
print("╠══════════════════════════════════════════════╣")

if not is_port_free(8000):
    print("║  Server already running!                     ║")
    print("║  Dashboard → http://127.0.0.1:8000           ║")
    print("╚══════════════════════════════════════════════╝")
    webbrowser.open("http://127.0.0.1:8000")
else:
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    open_browser_after(delay=3.0)
    print("║  ✓ Starting Flask server in background...    ║")
    print("║  ✓ Dashboard → http://127.0.0.1:8000         ║")
    print("║  ✓ Browser opens in 3 seconds                ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  Stop: Kernel → Restart in Jupyter menu      ║")
    print("╚══════════════════════════════════════════════╝")
