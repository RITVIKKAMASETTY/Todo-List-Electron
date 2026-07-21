"""
Alert Engine — Rule-Based Alert System.

Generates alerts based on:
    - Health score thresholds
    - Drift limits
    - RUL warnings
    - Oxygen level drops
    - Fault detections

Features:
    - Severity levels: info, warning, critical
    - De-duplication (don't repeat same alert within window)
    - Alert storage in database
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
    """
    Rule-based alert engine with de-duplication.

    Evaluates digital twin state against thresholds
    and generates severity-classified alerts.
    """

    def __init__(self):
        # Track last alert time by type for de-duplication
        self.last_alert_time = {}
        # Queue of pending alerts
        self.pending_alerts = []

    def _should_alert(self, alert_type: str) -> bool:
        """Check if enough time has passed since last alert of this type."""
        last_time = self.last_alert_time.get(alert_type, 0)
        return (time.time() - last_time) > ALERT_DEDUP_WINDOW

    def _add_alert(self, alert_type: str, severity: str, message: str):
        """Add an alert if not de-duplicated."""
        if self._should_alert(alert_type):
            self.last_alert_time[alert_type] = time.time()
            alert = {
                "timestamp": datetime.utcnow().isoformat(),
                "alert_type": alert_type,
                "severity": severity,
                "message": message
            }
            self.pending_alerts.append(alert)

    def evaluate(self, twin_state: dict) -> list:
        """
        Evaluate digital twin state and generate alerts.

        Args:
            twin_state: Complete digital twin state from pipeline

        Returns:
            List of generated alerts
        """
        self.pending_alerts = []

        health = twin_state.get("health", {})
        drift = twin_state.get("drift", {})
        rul = twin_state.get("rul", {})
        fault = twin_state.get("fault", {})
        sensor = twin_state.get("sensor_data", {})

        # ── Health Score Alerts ──────────────────────────────────────
        health_score = health.get("health_score", 100.0)

        if health_score < ALERT_HEALTH_CRITICAL:
            self._add_alert(
                "health_critical", "critical",
                f"CRITICAL: Health score at {health_score:.1f}%. "
                f"Immediate sensor replacement recommended."
            )
        elif health_score < ALERT_HEALTH_WARNING:
            self._add_alert(
                "health_warning", "warning",
                f"Health score at {health_score:.1f}%. "
                f"Schedule maintenance soon."
            )

        # ── Drift Alerts ─────────────────────────────────────────────
        total_drift = abs(drift.get("total_drift", 0.0))

        if total_drift > ALERT_DRIFT_CRITICAL:
            self._add_alert(
                "drift_critical", "critical",
                f"CRITICAL: Sensor drift at {total_drift:.2f}%. "
                f"Recalibration required immediately."
            )
        elif total_drift > ALERT_DRIFT_WARNING:
            self._add_alert(
                "drift_warning", "warning",
                f"Sensor drift at {total_drift:.2f}%. "
                f"Schedule recalibration."
            )

        # ── RUL Alerts ───────────────────────────────────────────────
        remaining_life = rul.get("remaining_life_hours", 9999)

        if remaining_life < ALERT_RUL_CRITICAL:
            self._add_alert(
                "rul_critical", "critical",
                f"CRITICAL: Remaining useful life only {remaining_life:.0f} hours. "
                f"Replace sensor immediately."
            )
        elif remaining_life < ALERT_RUL_WARNING:
            self._add_alert(
                "rul_warning", "warning",
                f"Remaining useful life {remaining_life:.0f} hours. "
                f"Order replacement sensor."
            )

        # ── Oxygen Level Alerts ──────────────────────────────────────
        oxygen = sensor.get("oxygen", 93.0)

        if oxygen < ALERT_OXYGEN_LOW:
            self._add_alert(
                "oxygen_low", "critical",
                f"CRITICAL: Oxygen concentration at {oxygen:.1f}%. "
                f"Below minimum safe level ({ALERT_OXYGEN_LOW}%)."
            )

        # ── Fault Alerts ─────────────────────────────────────────────
        fault_prob = fault.get("fault_probability", 0.0)
        detected_faults = fault.get("faults_detected", [])

        if fault_prob > 0.7:
            self._add_alert(
                "fault_critical", "critical",
                f"CRITICAL: Fault probability {fault_prob*100:.1f}%. "
                f"Detected: {', '.join(detected_faults) if detected_faults else 'unknown'}."
            )
        elif fault_prob > 0.3:
            self._add_alert(
                "fault_warning", "warning",
                f"Fault probability {fault_prob*100:.1f}%. "
                f"Monitoring: {', '.join(detected_faults) if detected_faults else 'anomaly'}."
            )

        # ── Heater Temperature Alert ─────────────────────────────────
        heater_temp = sensor.get("heater_temp", 700.0)
        if heater_temp < 600.0:
            self._add_alert(
                "heater_low", "critical",
                f"CRITICAL: Heater temperature {heater_temp:.1f}°C. "
                f"Below minimum operating temperature."
            )

        return self.pending_alerts

    async def evaluate_and_store(self, twin_state: dict) -> list:
        """
        Evaluate state, generate alerts, and store them in database.

        Args:
            twin_state: Complete digital twin state

        Returns:
            List of generated alerts
        """
        alerts = self.evaluate(twin_state)

        for alert in alerts:
            await insert_alert(alert)

        return alerts

    def get_recent_alerts(self) -> list:
        """Get recently generated alerts."""
        return self.pending_alerts


# Module-level singleton
_alert_engine = None


def get_alert_engine() -> AlertEngine:
    """Get or create the singleton alert engine."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine
