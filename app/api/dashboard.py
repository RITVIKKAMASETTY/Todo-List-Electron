"""
Dashboard API Router — Dashboard pages and data endpoints.

Provides:
    GET /                     — Main dashboard page
    GET /dashboard            — Full dashboard page
    GET /sensor-detail        — Sensor detail page
    GET /api/dashboard/summary — Aggregated system status
    GET /api/dashboard/twin   — Complete digital twin state
    GET /api/health/history   — Health score history
    GET /api/predictions/latest — Latest predictions
    GET /api/alerts/recent    — Recent alerts
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATES_DIR
from app.database.database import (
    get_latest_sensor_data, get_latest_health, get_health_history,
    get_latest_prediction, get_recent_alerts, get_sensor_count,
    get_alert_count_by_severity
)
from app.services.calculations import get_pipeline
from app.services.simulator import get_simulator

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Dashboard"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page."""
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/sensor-detail", response_class=HTMLResponse)
async def sensor_detail(request: Request):
    """Serve the sensor detail page."""
    return templates.TemplateResponse(request=request, name="sensor.html")


@router.get("/api/dashboard/summary")
async def get_summary():
    """
    Get aggregated dashboard summary.

    Returns all key metrics in a single API call for the dashboard.
    """
    sensor_data = await get_latest_sensor_data(limit=1)
    health_data = await get_latest_health(limit=1)
    prediction = await get_latest_prediction()
    alerts = await get_recent_alerts(limit=5)
    total_readings = await get_sensor_count()
    alert_counts = await get_alert_count_by_severity()

    sim = get_simulator()
    pipeline = get_pipeline()

    return {
        "status": "ok",
        "sensor": sensor_data[0] if sensor_data else None,
        "health": health_data[0] if health_data else None,
        "prediction": prediction,
        "recent_alerts": alerts,
        "statistics": {
            "total_readings": total_readings,
            "alert_counts": alert_counts,
            "simulator_status": sim.get_status(),
            "pipeline_summary": pipeline.get_summary()
        }
    }


@router.get("/api/dashboard/twin")
async def get_twin_state():
    """
    Get the complete digital twin state.

    Returns the full output from the last pipeline run.
    """
    pipeline = get_pipeline()
    sensor_data = await get_latest_sensor_data(limit=1)

    if sensor_data:
        # Run pipeline on latest data
        state = pipeline.process_reading(sensor_data[0])
        return {"status": "ok", "twin_state": state}

    return {"status": "no_data", "twin_state": None}


@router.get("/api/health/history")
async def health_history(limit: int = 100):
    """Get health score history."""
    data = await get_health_history(limit=limit)
    return {"status": "ok", "count": len(data), "data": data}


@router.get("/api/predictions/latest")
async def latest_predictions():
    """Get the latest prediction."""
    data = await get_latest_prediction()
    return {"status": "ok", "data": data}


@router.get("/api/alerts/recent")
async def recent_alerts(limit: int = 20):
    """Get recent alerts."""
    data = await get_recent_alerts(limit=limit)
    return {"status": "ok", "count": len(data), "data": data}
