"""
Flask Blueprint: Sensor API
Routes: /api/sensor/*
"""

from flask import Blueprint, jsonify, request
from app.database.database import (
    get_latest_sensor_data, get_sensor_history, get_sensor_count
)
from app.services.simulator import get_simulator

sensor_bp = Blueprint("sensor", __name__)


@sensor_bp.route("/api/sensor/live")
def live():
    rows = get_latest_sensor_data(limit=1)
    if rows:
        return jsonify({"status": "ok", "data": rows[0]})
    return jsonify({"status": "no_data", "data": None})


@sensor_bp.route("/api/sensor/history")
def history():
    minutes = request.args.get("minutes", 60, type=int)
    rows = get_sensor_history(minutes)
    return jsonify({"status": "ok", "data": rows, "count": len(rows)})


@sensor_bp.route("/api/sensor/status")
def status():
    sim = get_simulator()
    return jsonify({"status": "ok", "simulator": sim.get_status()})


@sensor_bp.route("/api/sensor/fault", methods=["POST", "GET"])
def inject_fault():
    fault_type = request.args.get("fault_type", "heater_failure")
    severity   = request.args.get("severity", 0.5, type=float)
    sim = get_simulator()
    sim.inject_fault(fault_type, severity)
    return jsonify({
        "status": "ok",
        "message": f"Fault '{fault_type}' injected at severity {severity}",
        "active_faults": list(sim.injected_faults.keys())
    })


@sensor_bp.route("/api/sensor/clear-faults", methods=["POST", "GET"])
def clear_faults():
    sim = get_simulator()
    sim.clear_faults()
    return jsonify({"status": "ok", "message": "All faults cleared"})
