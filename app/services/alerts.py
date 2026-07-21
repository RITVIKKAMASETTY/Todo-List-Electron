"""
Alert Engine — Synchronous version for Flask.
"""

import time
from datetime import datetime
from app.config import (
    ALERT_HEALTH_WARNING, ALERT_HEALTH_CRITICAL,
    ALERT_DRIFT_WARNING, ALERT_DRIFT_CRITICAL,
    ALERT_RUL_WARNING, ALERT_RUL_CRITICAL,
    ALERT_OXYGEN_LOW, ALERT_DEDUP_WINDOW
)
from app.database.database import insert_alert


class AlertEngine:
    def __init__(self):
        self.last_alert_time = {}
        self.pending_alerts = []

    def _should_alert(self, alert_type: str) -> bool:
        last_time = self.last_alert_time.get(alert_type, 0)
        return (time.time() - last_time) > ALERT_DEDUP_WINDOW

    def _add_alert(self, alert_type: str, severity: str, message: str):
        if self._should_alert(alert_type):
            self.last_alert_time[alert_type] = time.time()
            self.pending_alerts.append({
                "timestamp":  datetime.utcnow().isoformat(),
                "alert_type": alert_type,
                "severity":   severity,
                "message":    message,
            })

    def evaluate(self, twin_state: dict) -> list:
        self.pending_alerts = []

        health = twin_state.get("health", {})
        drift  = twin_state.get("drift", {})
        rul    = twin_state.get("rul", {})
        fault  = twin_state.get("fault", {})
        sensor = twin_state.get("sensor_data", {})

        h = health.get("health_score", 100.0)
        if h < ALERT_HEALTH_CRITICAL:
            self._add_alert("health_critical", "critical",
                f"CRITICAL: Health score {h:.1f}%. Immediate replacement recommended.")
        elif h < ALERT_HEALTH_WARNING:
            self._add_alert("health_warning", "warning",
                f"Health score {h:.1f}%. Schedule maintenance soon.")

        d = abs(drift.get("total_drift", 0.0))
        if d > ALERT_DRIFT_CRITICAL:
            self._add_alert("drift_critical", "critical",
                f"CRITICAL: Sensor drift {d:.2f}%. Recalibration required.")
        elif d > ALERT_DRIFT_WARNING:
            self._add_alert("drift_warning", "warning",
                f"Sensor drift {d:.2f}%. Schedule recalibration.")

        rul_hrs = rul.get("remaining_life_hours", 9999)
        if rul_hrs < ALERT_RUL_CRITICAL:
            self._add_alert("rul_critical", "critical",
                f"CRITICAL: Only {rul_hrs:.0f} hours remaining. Replace sensor immediately.")
        elif rul_hrs < ALERT_RUL_WARNING:
            self._add_alert("rul_warning", "warning",
                f"Remaining life {rul_hrs:.0f} hours. Order replacement sensor.")

        o2 = sensor.get("oxygen", 100.0)
        if o2 < ALERT_OXYGEN_LOW:
            self._add_alert("oxygen_low", "critical",
                f"CRITICAL: O₂ at {o2:.1f}% — below safe minimum {ALERT_OXYGEN_LOW}%.")

        fp = fault.get("fault_probability", 0.0)
        faults = fault.get("faults_detected", [])
        if fp > 0.7:
            self._add_alert("fault_critical", "critical",
                f"CRITICAL: Fault probability {fp*100:.1f}%. Detected: {', '.join(faults) or 'unknown'}.")
        elif fp > 0.3:
            self._add_alert("fault_warning", "warning",
                f"Fault probability {fp*100:.1f}%. Monitoring: {', '.join(faults) or 'anomaly'}.")

        ht = sensor.get("heater_temp", 700.0)
        if ht < 600.0:
            self._add_alert("heater_low", "critical",
                f"CRITICAL: Heater temp {ht:.1f}°C. Below minimum operating temperature.")

        return self.pending_alerts

    def evaluate_and_store(self, twin_state: dict) -> list:
        alerts = self.evaluate(twin_state)
        for alert in alerts:
            try:
                insert_alert(alert)
            except Exception as e:
                print(f"[Alerts] DB error: {e}")
        return alerts


_alert_engine = None

def get_alert_engine() -> AlertEngine:
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine
