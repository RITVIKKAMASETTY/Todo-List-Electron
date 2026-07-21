"""
Flask Application — Entry Point

Replaces FastAPI/uvicorn with Flask + waitress (for Windows)
or Flask's built-in dev server.

Starts:
  1. SQLite database
  2. Sensor simulator (background thread)
  3. Flask web server with two blueprints
"""

import os
import sys
import threading

from flask import Flask

from app.database.database import init_database, insert_sensor_data, insert_health, insert_prediction
from app.services.simulator import get_simulator
from app.services.calculations import get_pipeline
from app.services.alerts import get_alert_engine
from app.api.sensor import sensor_bp
from app.api.dashboard import dashboard_bp


# ── Build correct paths (works in dev AND packaged .exe) ──────────
if getattr(sys, "frozen", False):
    # Running as PyInstaller bundle
    BASE_DIR = os.path.dirname(sys.executable)
    template_folder = os.path.join(BASE_DIR, "app", "templates")
    static_folder   = os.path.join(BASE_DIR, "app", "static")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(BASE_DIR, "app", "templates")
    static_folder   = os.path.join(BASE_DIR, "app", "static")


# ── Create Flask app ──────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=template_folder,
    static_folder=static_folder,
    static_url_path="/static"
)

# Allow cross-origin requests from the browser (needed for local dev)
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ── Register Blueprints ───────────────────────────────────────────
app.register_blueprint(sensor_bp)
app.register_blueprint(dashboard_bp)


# ── Sensor callback: runs in background thread ────────────────────
_db_lock = threading.Lock()

def process_reading(reading: dict):
    """Called by simulator on every tick. Runs the full model pipeline."""
    try:
        pipeline = get_pipeline()
        twin_state = pipeline.process_reading(reading)

        with _db_lock:
            # Store raw sensor data
            insert_sensor_data(reading)

            # Store health record
            h = twin_state.get("health", {})
            d = twin_state.get("drift", {})
            n = twin_state.get("noise", {})
            a = twin_state.get("aging", {})
            f = twin_state.get("fault", {})
            if h:
                insert_health({
                    "timestamp":        reading["timestamp"],
                    "health_score":     h.get("health_score", 100.0),
                    "drift":            abs(d.get("total_drift", 0.0)),
                    "noise":            n.get("noise_rms", 0.0),
                    "aging_factor":     a.get("aging_factor", 0.0),
                    "sensitivity":      a.get("sensitivity", 1.0),
                    "fault_probability": f.get("fault_probability", 0.0),
                })

            # Store prediction (every 10th tick to save writes)
            p = twin_state.get("prediction")
            if p:
                insert_prediction({
                    "timestamp":           reading["timestamp"],
                    "predicted_oxygen":    p.get("predicted_oxygen"),
                    "predicted_temperature": p.get("predicted_temperature"),
                    "predicted_health":    p.get("predicted_health"),
                    "remaining_life":      twin_state.get("rul", {}).get("remaining_life_hours"),
                    "confidence":          p.get("confidence", 0.5),
                })

        # Run alert engine
        get_alert_engine().evaluate_and_store(twin_state)

    except Exception as e:
        print(f"[Pipeline] Error: {e}")


def start_app():
    """Initialize DB and start simulator. Call before serving."""
    print("=" * 60)
    print("  Digital Twin: Zirconia Oxygen Sensor (OBOGS)")
    print("  Starting up...")
    print("=" * 60)

    init_database()
    print("✓ Database initialized")

    sim = get_simulator()
    sim.start(callback=process_reading)
    print("✓ Sensor simulator started")
    print(f"  Time acceleration: {10}x")
    print("=" * 60)
    print("  Dashboard: http://127.0.0.1:8000")
    print("=" * 60)


# ── Start DB + simulator as soon as module loads ──────────────────
# (works for both `python app/main.py` and `from app.main import app`)
_started = False
def _auto_start():
    global _started
    if not _started:
        _started = True
        start_app()

_auto_start()


# ── Dev server entry ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False, threaded=True)
