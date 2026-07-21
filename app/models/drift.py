"""
Drift Model — Calibration Drift for Zirconia Oxygen Sensor.

Models the gradual shift in sensor calibration over time:
    drift(t) = α × t + β × sin(ω × t) + γ × t²

Components:
    - Linear drift: Steady baseline shift
    - Sinusoidal drift: Periodic environmental effects
    - Quadratic drift: Accelerating degradation
    - Random walk: Stochastic drift component
    - Temperature-dependent offset
"""

import numpy as np
from app.config import (
    DRIFT_LINEAR_RATE, DRIFT_SINUSOIDAL_AMP,
    DRIFT_SINUSOIDAL_FREQ, DRIFT_QUADRATIC_RATE
)


def linear_drift(flight_hours: float,
                 rate: float = DRIFT_LINEAR_RATE) -> float:
    """
    Calculate linear calibration drift.

    drift_linear = α × t

    Args:
        flight_hours: Total operating hours
        rate: Drift rate (%/hour)

    Returns:
        Linear drift component (%)
    """
    return rate * flight_hours


def sinusoidal_drift(flight_hours: float,
                     amplitude: float = DRIFT_SINUSOIDAL_AMP,
                     frequency: float = DRIFT_SINUSOIDAL_FREQ) -> float:
    """
    Calculate periodic drift component.

    drift_sin = β × sin(ω × t)

    This represents cyclic environmental effects
    (temperature cycles, pressure variations).

    Args:
        flight_hours: Total operating hours
        amplitude: Drift amplitude (%)
        frequency: Angular frequency (rad/hour)

    Returns:
        Sinusoidal drift component (%)
    """
    return float(amplitude * np.sin(frequency * flight_hours))


def quadratic_drift(flight_hours: float,
                    rate: float = DRIFT_QUADRATIC_RATE) -> float:
    """
    Calculate accelerating (quadratic) drift component.

    drift_quad = γ × t²

    Represents degradation that accelerates over time.

    Args:
        flight_hours: Total operating hours
        rate: Quadratic drift coefficient

    Returns:
        Quadratic drift component (%)
    """
    return rate * flight_hours ** 2


def random_walk_drift(current_drift: float, sigma: float = 0.001) -> float:
    """
    Add a random walk component to drift.

    drift_new = drift_old + N(0, σ)

    Models unpredictable stochastic shifts in calibration.

    Args:
        current_drift: Current random walk drift value (%)
        sigma: Standard deviation of walk step

    Returns:
        Updated random walk drift (%)
    """
    step = np.random.normal(0.0, sigma)
    return current_drift + step


def temperature_offset(temperature_c: float,
                       nominal_temp: float = 700.0) -> float:
    """
    Calculate temperature-dependent calibration offset.

    Sensors drift more when operating away from nominal temperature.

    Args:
        temperature_c: Current operating temperature (°C)
        nominal_temp: Nominal operating temperature (°C)

    Returns:
        Temperature-induced offset (%)
    """
    delta_t = temperature_c - nominal_temp
    # 0.01% drift per °C deviation
    return 0.01 * delta_t


def total_drift(flight_hours: float, temperature_c: float = 700.0,
                random_walk_state: float = 0.0) -> dict:
    """
    Calculate total calibration drift from all components.

    total = linear + sinusoidal + quadratic + random_walk + temp_offset

    Args:
        flight_hours: Total operating hours
        temperature_c: Current temperature (°C)
        random_walk_state: Current random walk state

    Returns:
        Dictionary with drift components and total
    """
    d_linear = linear_drift(flight_hours)
    d_sin = sinusoidal_drift(flight_hours)
    d_quad = quadratic_drift(flight_hours)
    d_random = random_walk_drift(random_walk_state)
    d_temp = temperature_offset(temperature_c)

    d_total = d_linear + d_sin + d_quad + d_random + d_temp

    return {
        "linear_drift": round(d_linear, 4),
        "sinusoidal_drift": round(d_sin, 4),
        "quadratic_drift": round(d_quad, 6),
        "random_walk_drift": round(d_random, 4),
        "temperature_offset": round(d_temp, 4),
        "total_drift": round(d_total, 4),
        "drift_rate": round(d_linear / max(flight_hours, 1.0), 6)
    }


def apply_drift(true_value: float, drift_amount: float) -> float:
    """
    Apply drift to a true measurement value.

    measured = true + drift

    Args:
        true_value: True (undrifted) value
        drift_amount: Drift amount in same units

    Returns:
        Drifted measurement
    """
    return true_value + drift_amount


def calculate_drift(sensor_data: dict, random_walk_state: float = 0.0) -> dict:
    """
    Run the complete drift model.

    Args:
        sensor_data: Dictionary with flight_hours, heater_temp
        random_walk_state: Current random walk state

    Returns:
        Dictionary with drift analysis
    """
    hours = sensor_data.get("flight_hours", 0.0)
    temp = sensor_data.get("heater_temp", 700.0)

    result = total_drift(hours, temp, random_walk_state)
    result["random_walk_state"] = result["random_walk_drift"]

    return result
