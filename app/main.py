"""
Digital Twin: Zirconia Oxygen Sensor (OBOGS)
============================================

Main FastAPI application entry point.

This is the heart of the Digital Twin system. It:
    1. Initializes the SQLite database
    2. Starts the sensor simulator as a background task
    3. Processes each reading through the full model pipeline
    4. Stores results in the database
    5. Generates alerts
    6. Serves the HTML dashboard

Run with: uvicorn app.main:app --reload
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import STATIC_DIR, DATA_DIR
from app.database.database import (
    init_database, insert_sensor_data, insert_health, insert_prediction
)
from app.api.sensor import router as sensor_router
from app.api.dashboard import router as dashboard_router
from app.services.simulator import get_simulator
from app.services.calculations import get_pipeline
from app.services.alerts import get_alert_engine

import os


async def process_reading(reading: dict):
    """
    Process a sensor reading through the entire digital twin pipeline.

    This is the callback function called by the simulator for each tick.
    It chains: sensor → models → database → alerts.

    Args:
        reading: Raw sensor data dictionary from simulator
    """
    # Store raw sensor data
    await insert_sensor_data(reading)

    # Run through the digital twin pipeline
    pipeline = get_pipeline()
    twin_state = pipeline.process_reading(reading)

    # Store health assessment
    health = twin_state.get("health", {})
    drift = twin_state.get("drift", {})
    aging = twin_state.get("aging", {})
    fault = twin_state.get("fault", {})

    await insert_health({
        "timestamp": reading["timestamp"],
        "health_score": health.get("health_score", 100.0),
        "drift": abs(drift.get("total_drift", 0.0)),
        "noise": twin_state.get("noise", {}).get("noise_rms", 0.0),
        "aging_factor": aging.get("aging_factor", 0.0),
        "sensitivity": aging.get("sensitivity", 1.0),
        "fault_probability": fault.get("fault_probability", 0.0)
    })

    # Store predictions (when available)
    prediction = twin_state.get("prediction")
    if prediction:
        rul = twin_state.get("rul", {})
        await insert_prediction({
            "timestamp": reading["timestamp"],
            "predicted_oxygen": prediction.get("predicted_oxygen"),
            "predicted_temperature": prediction.get("predicted_temperature"),
            "predicted_health": prediction.get("predicted_health"),
            "remaining_life": rul.get("remaining_life_hours"),
            "confidence": prediction.get("confidence", 0.0)
        })

    # Evaluate alerts
    alert_engine = get_alert_engine()
    await alert_engine.evaluate_and_store(twin_state)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──────────────────────────────────────────────────────
    print("=" * 60)
    print("  Digital Twin: Zirconia Oxygen Sensor (OBOGS)")
    print("  Starting up...")
    print("=" * 60)

    # Initialize database
    await init_database()
    print("✓ Database initialized")

    # Create data directory
    os.makedirs(str(DATA_DIR), exist_ok=True)

    # Start simulator as background task
    simulator = get_simulator()
    sim_task = asyncio.create_task(simulator.start(callback=process_reading))
    print("✓ Sensor simulator started")
    print(f"  Time acceleration: {simulator.get_status()['time_acceleration']}x")
    print("=" * 60)
    print(f"  Dashboard: http://127.0.0.1:8000")
    print("=" * 60)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    print("\nShutting down...")
    simulator.stop()
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass
    print("✓ Simulator stopped")


# ── Create FastAPI Application ───────────────────────────────────────────
app = FastAPI(
    title="Digital Twin: Zirconia Oxygen Sensor",
    description="OBOGS Digital Twin with physics models, aging, fault detection, and predictive maintenance",
    version="1.0.0",
    lifespan=lifespan
)

# ── CORS Middleware ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Static Files ──────────────────────────────────────────────────
os.makedirs(str(STATIC_DIR / "css"), exist_ok=True)
os.makedirs(str(STATIC_DIR / "js"), exist_ok=True)
os.makedirs(str(STATIC_DIR / "images"), exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Include API Routers ─────────────────────────────────────────────────
app.include_router(dashboard_router)
app.include_router(sensor_router)
