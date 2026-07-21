"""
SQLite Database Manager (Synchronous — uses built-in sqlite3).

No external packages needed. sqlite3 is part of Python's standard library.
Handles connection management, table creation, and CRUD operations
for sensor_data, health, predictions, and alerts tables.
"""

import sqlite3
import os
from datetime import datetime
from app.config import DATABASE_PATH


def get_db():
    """Get a synchronous SQLite connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create all tables if they don't exist."""
    conn = get_db()
    try:
        cur = conn.cursor()

        # ── sensor_data ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                oxygen REAL NOT NULL,
                temperature REAL NOT NULL,
                pressure REAL NOT NULL,
                flow REAL NOT NULL,
                humidity REAL NOT NULL,
                voltage REAL NOT NULL,
                current REAL NOT NULL,
                vibration REAL DEFAULT 0.0,
                heater_temp REAL NOT NULL,
                altitude REAL DEFAULT 0.0,
                flight_hours REAL DEFAULT 0.0,
                thermal_cycles INTEGER DEFAULT 0
            )
        """)

        # ── health ───────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                health_score REAL NOT NULL,
                drift REAL DEFAULT 0.0,
                noise REAL DEFAULT 0.0,
                aging_factor REAL DEFAULT 0.0,
                sensitivity REAL DEFAULT 1.0,
                fault_probability REAL DEFAULT 0.0
            )
        """)

        # ── predictions ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                predicted_oxygen REAL,
                predicted_temperature REAL,
                predicted_health REAL,
                remaining_life REAL,
                confidence REAL DEFAULT 0.0
            )
        """)

        # ── alerts ───────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                message TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        # ── Indexes ──────────────────────────────────────────────
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor_ts ON sensor_data(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_health_ts ON health(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pred_ts ON predictions(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alert_ts ON alerts(timestamp)")

        conn.commit()
        print("✓ Database initialized")
    finally:
        conn.close()


# ─── CRUD ────────────────────────────────────────────────────────

def insert_sensor_data(data: dict):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO sensor_data
            (timestamp, oxygen, temperature, pressure, flow, humidity,
             voltage, current, vibration, heater_temp, altitude,
             flight_hours, thermal_cycles)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data["oxygen"], data["temperature"], data["pressure"],
            data["flow"], data["humidity"], data["voltage"],
            data["current"], data.get("vibration", 0.0),
            data["heater_temp"], data.get("altitude", 0.0),
            data.get("flight_hours", 0.0), data.get("thermal_cycles", 0)
        ))
        conn.commit()
    finally:
        conn.close()


def insert_health(data: dict):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO health
            (timestamp, health_score, drift, noise, aging_factor,
             sensitivity, fault_probability)
            VALUES (?,?,?,?,?,?,?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data["health_score"], data.get("drift", 0.0),
            data.get("noise", 0.0), data.get("aging_factor", 0.0),
            data.get("sensitivity", 1.0), data.get("fault_probability", 0.0)
        ))
        conn.commit()
    finally:
        conn.close()


def insert_prediction(data: dict):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO predictions
            (timestamp, predicted_oxygen, predicted_temperature,
             predicted_health, remaining_life, confidence)
            VALUES (?,?,?,?,?,?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data.get("predicted_oxygen"), data.get("predicted_temperature"),
            data.get("predicted_health"), data.get("remaining_life"),
            data.get("confidence", 0.0)
        ))
        conn.commit()
    finally:
        conn.close()


def insert_alert(data: dict):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO alerts (timestamp, alert_type, severity, message)
            VALUES (?,?,?,?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data["alert_type"], data.get("severity", "info"),
            data["message"]
        ))
        conn.commit()
    finally:
        conn.close()


def _rows_to_list(rows):
    return [dict(r) for r in rows]


def get_latest_sensor_data(limit=1):
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?", (limit,)
        )
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def get_sensor_history(minutes=60):
    conn = get_db()
    try:
        cur = conn.execute(
            """SELECT * FROM sensor_data
               WHERE timestamp >= datetime('now', ? || ' minutes')
               ORDER BY id ASC""",
            (f"-{minutes}",)
        )
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def get_latest_health(limit=1):
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT * FROM health ORDER BY id DESC LIMIT ?", (limit,)
        )
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def get_health_history(limit=100):
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT * FROM health ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = _rows_to_list(cur.fetchall())
        return list(reversed(rows))
    finally:
        conn.close()


def get_latest_prediction():
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_recent_alerts(limit=20):
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
        )
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def get_sensor_count():
    conn = get_db()
    try:
        cur = conn.execute("SELECT COUNT(*) as count FROM sensor_data")
        row = cur.fetchone()
        return row["count"] if row else 0
    finally:
        conn.close()


def get_alert_count_by_severity():
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT severity, COUNT(*) as count FROM alerts GROUP BY severity"
        )
        return {r["severity"]: r["count"] for r in cur.fetchall()}
    finally:
        conn.close()
