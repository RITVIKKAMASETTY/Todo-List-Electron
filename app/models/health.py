"""
Health Index Model — Composite Sensor Health Score.

Combines multiple degradation indicators into a single health score (0-100):
    H = w₁×(1-drift_norm) + w₂×(1-noise_norm) + w₃×(1-fault_prob)
        + w₄×sensitivity + w₅×(1-age_factor)

Health Categories:
    95-100: Excellent (new/near-new)
    85-95:  Good (normal operation)
    70-85:  Fair (monitor closely)
    50-70:  Poor (maintenance recommended)
    0-50:   Critical (replace immediately)
"""

import numpy as np
from app.config import (
    HEALTH_WEIGHT_DRIFT, HEALTH_WEIGHT_NOISE,
    HEALTH_WEIGHT_FAULT, HEALTH_WEIGHT_SENSITIVITY,
    HEALTH_WEIGHT_AGE, ALERT_DRIFT_CRITICAL
)


def normalize_drift(drift_value: float, max_drift: float = ALERT_DRIFT_CRITICAL) -> float:
    """
    Normalize drift to 0-1 range.

    Args:
        drift_value: Absolute drift value (%)
        max_drift: Maximum expected drift (%)

    Returns:
        Normalized drift (0 = no drift, 1 = max drift)
    """
    return float(np.clip(abs(drift_value) / max_drift, 0.0, 1.0))


def normalize_noise(noise_rms: float, max_noise: float = 0.5) -> float:
    """
    Normalize noise RMS to 0-1 range.

    Args:
        noise_rms: RMS noise value
        max_noise: Maximum acceptable noise

    Returns:
        Normalized noise (0 = no noise, 1 = max noise)
    """
    return float(np.clip(noise_rms / max_noise, 0.0, 1.0))


def health_score(drift: float, noise_rms: float, fault_probability: float,
                 sensitivity: float, aging_factor: float) -> float:
    """
    Calculate the composite health index.

    H = Σ(wᵢ × componentᵢ) × 100

    Each component is normalized so that:
        1.0 = perfect health for that dimension
        0.0 = complete failure

    Args:
        drift: Current drift value (%)
        noise_rms: RMS noise level
        fault_probability: Overall fault probability (0-1)
        sensitivity: Current sensitivity (0-1)
        aging_factor: Current aging factor (0-1)

    Returns:
        Health score (0-100)
    """
    drift_component = 1.0 - normalize_drift(drift)
    noise_component = 1.0 - normalize_noise(noise_rms)
    fault_component = 1.0 - fault_probability
    sensitivity_component = float(np.clip(sensitivity, 0.0, 1.0))
    age_component = 1.0 - aging_factor

    score = (
        HEALTH_WEIGHT_DRIFT * drift_component +
        HEALTH_WEIGHT_NOISE * noise_component +
        HEALTH_WEIGHT_FAULT * fault_component +
        HEALTH_WEIGHT_SENSITIVITY * sensitivity_component +
        HEALTH_WEIGHT_AGE * age_component
    ) * 100.0

    return float(np.clip(score, 0.0, 100.0))


def health_category(score: float) -> str:
    """
    Categorize health score into human-readable status.

    Args:
        score: Health score (0-100)

    Returns:
        Health category string
    """
    if score >= 95:
        return "Excellent"
    elif score >= 85:
        return "Good"
    elif score >= 70:
        return "Fair"
    elif score >= 50:
        return "Poor"
    else:
        return "Critical"


def degradation_rate(health_history: list) -> float:
    """
    Calculate the rate of health degradation.

    Uses linear regression on recent health scores.

    Args:
        health_history: List of recent health scores

    Returns:
        Degradation rate (health points lost per reading)
    """
    if len(health_history) < 2:
        return 0.0

    n = len(health_history)
    x = np.arange(n)
    y = np.array(health_history)

    # Simple linear regression
    slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / \
            (n * np.sum(x**2) - np.sum(x)**2 + 1e-10)

    return float(slope)


def health_trend(health_history: list, window: int = 20) -> str:
    """
    Determine health trend direction.

    Args:
        health_history: List of health scores
        window: Analysis window

    Returns:
        Trend string: "improving", "stable", "degrading", "rapid_degradation"
    """
    if len(health_history) < window:
        return "insufficient_data"

    recent = health_history[-window:]
    rate = degradation_rate(recent)

    if rate > 0.1:
        return "improving"
    elif rate > -0.05:
        return "stable"
    elif rate > -0.2:
        return "degrading"
    else:
        return "rapid_degradation"


def calculate_health(drift: float = 0.0, noise_rms: float = 0.0,
                     fault_probability: float = 0.0,
                     sensitivity: float = 1.0,
                     aging_factor: float = 0.0,
                     health_history: list = None) -> dict:
    """
    Run the complete health assessment.

    Args:
        drift: Current drift (%)
        noise_rms: Current noise RMS
        fault_probability: Current fault probability (0-1)
        sensitivity: Current sensitivity (0-1)
        aging_factor: Current aging factor (0-1)
        health_history: Previous health scores for trend analysis

    Returns:
        Dictionary with health assessment
    """
    score = health_score(drift, noise_rms, fault_probability,
                         sensitivity, aging_factor)
    category = health_category(score)

    result = {
        "health_score": round(score, 2),
        "category": category,
        "components": {
            "drift_health": round((1.0 - normalize_drift(drift)) * 100, 2),
            "noise_health": round((1.0 - normalize_noise(noise_rms)) * 100, 2),
            "fault_health": round((1.0 - fault_probability) * 100, 2),
            "sensitivity_health": round(sensitivity * 100, 2),
            "age_health": round((1.0 - aging_factor) * 100, 2)
        }
    }

    if health_history and len(health_history) >= 2:
        result["degradation_rate"] = round(degradation_rate(health_history), 4)
        result["trend"] = health_trend(health_history)
    else:
        result["degradation_rate"] = 0.0
        result["trend"] = "insufficient_data"

    return result
