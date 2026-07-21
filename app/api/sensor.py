"""
Sensor API Router — Endpoints for sensor data operations.

Provides:
    GET  /api/sensor/live     — Latest sensor reading
    GET  /api/sensor/history  — Historical readings
    POST /api/sensor          — Manual data injection
    GET  /api/sensor/status   — Simulator status
    POST /api/sensor/fault    — Inject fault for testing
    POST /api/sensor/clear-faults — Clear injected faults
"""

from fastapi import APIRouter, Query
from app.database.database import (
    get_latest_sensor_data, get_sensor_history, insert_sensor_data
)
from app.services.simulator import get_simulator

router = APIRouter(prefix="/api/sensor", tags=["Sensor"])


@router.get("/live")
async def get_live_reading():
    """Get the most recent sensor reading."""
    data = await get_latest_sensor_data(limit=1)
    if data:
        return {"status": "ok", "data": data[0]}
    return {"status": "no_data", "data": None}


@router.get("/history")
async def get_history(minutes: int = Query(default=60, ge=1, le=1440)):
    """
    Get sensor readings from the last N minutes.

    Args:
        minutes: Number of minutes of history (1-1440)
    """
    data = await get_sensor_history(minutes=minutes)
    return {"status": "ok", "count": len(data), "data": data}


@router.post("")
async def inject_reading(data: dict):
    """
    Manually inject a sensor reading.

    Useful for testing with specific values.
    """
    await insert_sensor_data(data)
    return {"status": "ok", "message": "Reading stored"}


@router.get("/status")
async def get_status():
    """Get the simulator status."""
    sim = get_simulator()
    return {"status": "ok", "simulator": sim.get_status()}


@router.post("/fault")
async def inject_fault(fault_type: str, severity: float = 0.5):
    """
    Inject a fault into the simulator for testing.

    Fault types: heater_failure, pressure_leak, sensor_crack,
                 voltage_drop, wiring_fault

    Args:
        fault_type: Type of fault to inject
        severity: Fault severity (0-1)
    """
    sim = get_simulator()
    valid_faults = ["heater_failure", "pressure_leak", "sensor_crack",
                    "voltage_drop", "wiring_fault"]

    if fault_type not in valid_faults:
        return {
            "status": "error",
            "message": f"Invalid fault type. Valid: {valid_faults}"
        }

    sim.inject_fault(fault_type, min(max(severity, 0.0), 1.0))
    return {
        "status": "ok",
        "message": f"Fault '{fault_type}' injected with severity {severity}"
    }


@router.post("/clear-faults")
async def clear_faults():
    """Clear all injected faults."""
    sim = get_simulator()
    sim.clear_faults()
    return {"status": "ok", "message": "All faults cleared"}
