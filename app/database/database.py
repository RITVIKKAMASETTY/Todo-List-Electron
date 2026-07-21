"""
SQLite Database Manager for the Digital Twin.

Handles connection management, table creation, and CRUD operations
for sensor_data, health, predictions, and alerts tables.
"""

import aiosqlite
import os
from datetime import datetime
from app.config import DATABASE_PATH


async def get_db():
    """Get an async database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    db = await aiosqlite.connect(str(DATABASE_PATH))
    db.row_factory = aiosqlite.Row
    return db


async def init_database():
    """Create all tables if they don't exist."""
    db = await get_db()
    try:
        # ── sensor_data table ────────────────────────────────────────────
        await db.execute("""
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

        # ── health table ─────────────────────────────────────────────────
        await db.execute("""
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

        # ── predictions table ────────────────────────────────────────────
        await db.execute("""
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

        # ── alerts table ─────────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                message TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        # ── Indexes for performance ──────────────────────────────────────
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_timestamp
            ON sensor_data(timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_timestamp
            ON health(timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
            ON predictions(timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
            ON alerts(timestamp)
        """)

        await db.commit()
    finally:
        await db.close()


# ─── CRUD Operations ────────────────────────────────────────────────────────

async def insert_sensor_data(data: dict):
    """Insert a sensor reading into the database."""
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO sensor_data
            (timestamp, oxygen, temperature, pressure, flow, humidity,
             voltage, current, vibration, heater_temp, altitude,
             flight_hours, thermal_cycles)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data["oxygen"], data["temperature"], data["pressure"],
            data["flow"], data["humidity"], data["voltage"],
            data["current"], data.get("vibration", 0.0),
            data["heater_temp"], data.get("altitude", 0.0),
            data.get("flight_hours", 0.0), data.get("thermal_cycles", 0)
        ))
        await db.commit()
    finally:
        await db.close()


async def insert_health(data: dict):
    """Insert a health assessment record."""
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO health
            (timestamp, health_score, drift, noise, aging_factor,
             sensitivity, fault_probability)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data["health_score"], data.get("drift", 0.0),
            data.get("noise", 0.0), data.get("aging_factor", 0.0),
            data.get("sensitivity", 1.0), data.get("fault_probability", 0.0)
        ))
        await db.commit()
    finally:
        await db.close()


async def insert_prediction(data: dict):
    """Insert a prediction record."""
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO predictions
            (timestamp, predicted_oxygen, predicted_temperature,
             predicted_health, remaining_life, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data.get("predicted_oxygen"), data.get("predicted_temperature"),
            data.get("predicted_health"), data.get("remaining_life"),
            data.get("confidence", 0.0)
        ))
        await db.commit()
    finally:
        await db.close()


async def insert_alert(data: dict):
    """Insert an alert record."""
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO alerts
            (timestamp, alert_type, severity, message)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("timestamp", datetime.utcnow().isoformat()),
            data["alert_type"], data.get("severity", "info"),
            data["message"]
        ))
        await db.commit()
    finally:
        await db.close()


async def get_latest_sensor_data(limit: int = 1):
    """Get the most recent sensor readings."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_sensor_history(minutes: int = 60):
    """Get sensor data from the last N minutes."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT * FROM sensor_data
               WHERE timestamp >= datetime('now', ? || ' minutes')
               ORDER BY id ASC""",
            (f"-{minutes}",)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_latest_health(limit: int = 1):
    """Get the most recent health records."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM health ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_health_history(limit: int = 100):
    """Get health score history."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM health ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]
    finally:
        await db.close()


async def get_latest_prediction():
    """Get the most recent prediction."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_recent_alerts(limit: int = 20):
    """Get recent alerts."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_sensor_count():
    """Get total number of sensor readings."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as count FROM sensor_data")
        row = await cursor.fetchone()
        return row["count"] if row else 0
    finally:
        await db.close()


async def get_alert_count_by_severity():
    """Get alert counts grouped by severity."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT severity, COUNT(*) as count
               FROM alerts GROUP BY severity"""
        )
        rows = await cursor.fetchall()
        return {row["severity"]: row["count"] for row in rows}
    finally:
        await db.close()
