"""
Fault Detection Model — Anomaly Detection for Zirconia Sensor.

Detects sensor faults through:
    - Residual analysis: measured vs. physics-predicted values
    - Threshold-based detection: hard limits on key parameters
    - Statistical anomaly detection: z-score based
    - Multi-fault classification

Fault Types:
    1. Heater failure (low heater temperature)
    2. Pressure leak (rapid pressure drop)
    3. Sensor crack (erratic voltage)
    4. Voltage drop (degraded output)
    5. Wiring fault (current anomaly)
"""

import numpy as np
from app.config import (
    FAULT_RESIDUAL_THRESHOLD, FAULT_VOLTAGE_DROP_LIMIT,
    FAULT_HEATER_TEMP_MIN, FAULT_PRESSURE_LEAK_RATE
)


def residual_analysis(measured_voltage: float, ideal_voltage: float) -> dict:
    """
    Calculate the residual between measured and ideal voltage.

    Large residuals indicate sensor malfunction.

    Args:
        measured_voltage: Actual sensor output (V)
        ideal_voltage: Physics-predicted ideal output (V)

    Returns:
        Dictionary with residual analysis
    """
    residual = measured_voltage - ideal_voltage
    abs_residual = abs(residual)
    relative_error = abs_residual / max(abs(ideal_voltage), 1e-10) * 100.0

    return {
        "residual": round(residual, 6),
        "abs_residual": round(abs_residual, 6),
        "relative_error": round(relative_error, 2),
        "is_anomaly": relative_error > FAULT_RESIDUAL_THRESHOLD * 10
    }


def detect_heater_failure(heater_temp: float) -> dict:
    """
    Detect heater element failure.

    A functioning heater maintains temperature above the minimum.
    Failure modes: open circuit, partial failure, degraded heating.

    Args:
        heater_temp: Current heater temperature (°C)

    Returns:
        Fault detection result
    """
    severity = 0.0
    if heater_temp < FAULT_HEATER_TEMP_MIN:
        severity = 1.0 - (heater_temp / FAULT_HEATER_TEMP_MIN)
        severity = float(np.clip(severity, 0.0, 1.0))

    return {
        "fault_type": "heater_failure",
        "detected": heater_temp < FAULT_HEATER_TEMP_MIN,
        "severity": round(severity, 4),
        "heater_temp": heater_temp,
        "threshold": FAULT_HEATER_TEMP_MIN
    }


def detect_pressure_leak(current_pressure: float, previous_pressure: float,
                         dt: float = 1.0) -> dict:
    """
    Detect pressure leak from rapid pressure drop.

    Args:
        current_pressure: Current pressure reading (psi)
        previous_pressure: Previous pressure reading (psi)
        dt: Time between readings (seconds)

    Returns:
        Fault detection result
    """
    pressure_rate = (previous_pressure - current_pressure) / dt  # psi/sec
    # Convert to psi/min for threshold comparison
    pressure_rate_min = pressure_rate * 60.0

    detected = pressure_rate_min > FAULT_PRESSURE_LEAK_RATE
    severity = float(np.clip(pressure_rate_min / (FAULT_PRESSURE_LEAK_RATE * 3), 0.0, 1.0))

    return {
        "fault_type": "pressure_leak",
        "detected": detected,
        "severity": round(severity, 4),
        "pressure_drop_rate": round(pressure_rate_min, 4),
        "threshold": FAULT_PRESSURE_LEAK_RATE
    }


def detect_voltage_drop(voltage: float) -> dict:
    """
    Detect abnormal voltage drop indicating sensor degradation.

    Args:
        voltage: Current sensor voltage (V)

    Returns:
        Fault detection result
    """
    detected = voltage < FAULT_VOLTAGE_DROP_LIMIT
    severity = 0.0
    if detected:
        severity = 1.0 - (voltage / FAULT_VOLTAGE_DROP_LIMIT)
        severity = float(np.clip(severity, 0.0, 1.0))

    return {
        "fault_type": "voltage_drop",
        "detected": detected,
        "severity": round(severity, 4),
        "voltage": voltage,
        "threshold": FAULT_VOLTAGE_DROP_LIMIT
    }


def detect_sensor_crack(voltage_history: list, window: int = 10) -> dict:
    """
    Detect sensor crack from erratic voltage patterns.

    A cracked sensor produces highly variable, noisy readings.
    Uses coefficient of variation (CV) as the indicator.

    Args:
        voltage_history: Recent voltage readings
        window: Analysis window size

    Returns:
        Fault detection result
    """
    if len(voltage_history) < window:
        return {
            "fault_type": "sensor_crack",
            "detected": False,
            "severity": 0.0,
            "cv": 0.0,
            "message": "Insufficient data"
        }

    recent = voltage_history[-window:]
    mean_v = np.mean(recent)
    std_v = np.std(recent)

    cv = std_v / max(abs(mean_v), 1e-10) * 100.0  # Coefficient of variation (%)

    # Normal CV < 2%, crack if > 5%
    detected = cv > 5.0
    severity = float(np.clip((cv - 2.0) / 8.0, 0.0, 1.0))

    return {
        "fault_type": "sensor_crack",
        "detected": detected,
        "severity": round(severity, 4),
        "cv": round(cv, 2)
    }


def detect_wiring_fault(voltage: float, current: float) -> dict:
    """
    Detect wiring fault from voltage-current inconsistency.

    Normal: V/I ≈ expected impedance
    Fault: Open circuit (high V, low I) or short (low V, high I)

    Args:
        voltage: Sensor voltage (V)
        current: Sensor current (A)

    Returns:
        Fault detection result
    """
    if current < 1e-6:
        # Near-zero current: possible open circuit
        return {
            "fault_type": "wiring_fault",
            "detected": True,
            "severity": 0.9,
            "impedance": float('inf'),
            "sub_type": "open_circuit"
        }

    impedance = voltage / current
    # Normal impedance range: 50-200 Ω
    detected = impedance < 10.0 or impedance > 500.0
    severity = 0.0
    sub_type = "normal"

    if impedance < 10.0:
        severity = float(np.clip(1.0 - impedance / 10.0, 0.0, 1.0))
        sub_type = "short_circuit"
    elif impedance > 500.0:
        severity = float(np.clip((impedance - 500.0) / 500.0, 0.0, 1.0))
        sub_type = "high_resistance"

    return {
        "fault_type": "wiring_fault",
        "detected": detected,
        "severity": round(severity, 4),
        "impedance": round(impedance, 2),
        "sub_type": sub_type
    }


def overall_fault_probability(faults: list) -> float:
    """
    Calculate overall fault probability from individual fault detections.

    Uses maximum severity with a small boost for multiple concurrent faults.

    Args:
        faults: List of fault detection dictionaries

    Returns:
        Overall fault probability (0-1)
    """
    if not faults:
        return 0.0

    severities = [f.get("severity", 0.0) for f in faults]
    max_severity = max(severities)
    num_detected = sum(1 for f in faults if f.get("detected", False))

    # Boost for multiple simultaneous faults
    multi_fault_boost = 0.05 * max(num_detected - 1, 0)

    return float(np.clip(max_severity + multi_fault_boost, 0.0, 1.0))


def calculate_fault(sensor_data: dict, ideal_voltage: float = 0.82,
                    previous_pressure: float = None,
                    voltage_history: list = None) -> dict:
    """
    Run the complete fault detection model.

    Args:
        sensor_data: Current sensor readings
        ideal_voltage: Physics-predicted ideal voltage
        previous_pressure: Previous pressure reading for leak detection
        voltage_history: Recent voltage readings for crack detection

    Returns:
        Dictionary with all fault detection results
    """
    voltage = sensor_data.get("voltage", 0.82)
    current = sensor_data.get("current", 0.21)
    heater_temp = sensor_data.get("heater_temp", 700.0)
    pressure = sensor_data.get("pressure", 29.0)

    # Run all detectors
    faults = []

    residual = residual_analysis(voltage, ideal_voltage)
    heater = detect_heater_failure(heater_temp)
    faults.append(heater)

    voltage_fault = detect_voltage_drop(voltage)
    faults.append(voltage_fault)

    wiring = detect_wiring_fault(voltage, current)
    faults.append(wiring)

    if previous_pressure is not None:
        leak = detect_pressure_leak(pressure, previous_pressure)
        faults.append(leak)
    else:
        leak = {"fault_type": "pressure_leak", "detected": False, "severity": 0.0}

    if voltage_history is not None:
        crack = detect_sensor_crack(voltage_history)
        faults.append(crack)
    else:
        crack = {"fault_type": "sensor_crack", "detected": False, "severity": 0.0}

    fault_prob = overall_fault_probability(faults)

    return {
        "residual_analysis": residual,
        "heater_failure": heater,
        "pressure_leak": leak,
        "voltage_drop": voltage_fault,
        "sensor_crack": crack,
        "wiring_fault": wiring,
        "fault_probability": round(fault_prob, 4),
        "faults_detected": [f["fault_type"] for f in faults if f.get("detected", False)]
    }
