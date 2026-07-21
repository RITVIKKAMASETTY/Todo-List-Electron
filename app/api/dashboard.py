"""
Flask Blueprint: Dashboard API + HTML Pages
Routes: /, /dashboard, /sensor-detail, /api/dashboard/*
"""

from flask import Blueprint, jsonify, request, render_template
from app.database.database import (
    get_latest_sensor_data, get_latest_health,
    get_health_history, get_latest_prediction,
    get_recent_alerts, get_sensor_count, get_alert_count_by_severity
)
from app.services.simulator import get_simulator
from app.services.calculations import get_pipeline

dashboard_bp = Blueprint("dashboard", __name__)


# ── HTML Pages ────────────────────────────────────────────────────

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def index():
    return render_template("dashboard.html")


@dashboard_bp.route("/sensor-detail")
def sensor_detail():
    return render_template("sensor.html")


# ── JSON API ──────────────────────────────────────────────────────

@dashboard_bp.route("/api/dashboard/summary")
def summary():
    sensor_rows  = get_latest_sensor_data(limit=1)
    health_rows  = get_latest_health(limit=1)
    prediction   = get_latest_prediction()
    alerts       = get_recent_alerts(limit=5)
    sim_status   = get_simulator().get_status()
    pipeline_sum = get_pipeline().get_summary()

    return jsonify({
        "status":        "ok",
        "sensor":        sensor_rows[0] if sensor_rows else None,
        "health":        health_rows[0] if health_rows else None,
        "prediction":    prediction,
        "recent_alerts": alerts,
        "statistics": {
            "total_readings":    get_sensor_count(),
            "alert_counts":      get_alert_count_by_severity(),
            "simulator_status":  sim_status,
            "pipeline_summary":  pipeline_sum,
        }
    })


@dashboard_bp.route("/api/dashboard/twin")
def twin_state():
    sensor_rows = get_latest_sensor_data(limit=1)
    health_rows = get_latest_health(limit=1)
    prediction  = get_latest_prediction()
    alerts      = get_recent_alerts(limit=10)

    return jsonify({
        "status":     "ok",
        "sensor":     sensor_rows[0] if sensor_rows else None,
        "health":     health_rows[0] if health_rows else None,
        "prediction": prediction,
        "alerts":     alerts,
    })


@dashboard_bp.route("/api/health/history")
def health_history():
    limit = request.args.get("limit", 100, type=int)
    rows  = get_health_history(limit)
    return jsonify({"status": "ok", "data": rows, "count": len(rows)})


@dashboard_bp.route("/api/predictions/latest")
def predictions_latest():
    pred = get_latest_prediction()
    return jsonify({"status": "ok", "data": pred})


@dashboard_bp.route("/api/alerts/recent")
def alerts_recent():
    limit  = request.args.get("limit", 10, type=int)
    alerts = get_recent_alerts(limit)
    return jsonify({"status": "ok", "data": alerts, "count": len(alerts)})
