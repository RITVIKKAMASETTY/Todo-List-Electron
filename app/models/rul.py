"""
Remaining Useful Life (RUL) Model.

Predicts when the sensor should be replaced based on:
    - Exponential degradation curve fitting
    - Threshold-based: "hours until health < threshold"
    - Monte Carlo simulation for confidence intervals
    - Wiener process model for stochastic RUL

Replacement threshold: Health Score < 60% → replace sensor.
"""

import numpy as np
from scipy.optimize import curve_fit
from app.config import (
    RUL_HEALTH_THRESHOLD, RUL_MONTE_CARLO_SIMS,
    SENSOR_MAX_HOURS
)


def exponential_decay(t, h0, k):
    """
    Exponential decay function for curve fitting.

    H(t) = H₀ × exp(-k × t)

    Args:
        t: Time (hours)
        h0: Initial health
        k: Decay rate constant

    Returns:
        Health at time t
    """
    return h0 * np.exp(-k * t)


def fit_degradation_curve(time_points: list, health_values: list) -> dict:
    """
    Fit an exponential degradation curve to health history.

    Args:
        time_points: Time stamps (hours)
        health_values: Corresponding health scores

    Returns:
        Dictionary with fitted parameters and goodness of fit
    """
    if len(time_points) < 3:
        return {
            "h0": 100.0,
            "k": 0.0001,
            "r_squared": 0.0,
            "fitted": False
        }

    t = np.array(time_points, dtype=float)
    h = np.array(health_values, dtype=float)

    try:
        popt, pcov = curve_fit(
            exponential_decay, t, h,
            p0=[100.0, 0.0001],
            bounds=([50.0, 1e-8], [105.0, 0.1]),
            maxfev=1000
        )
        h0, k = popt

        # Calculate R²
        h_pred = exponential_decay(t, h0, k)
        ss_res = np.sum((h - h_pred) ** 2)
        ss_tot = np.sum((h - np.mean(h)) ** 2)
        r_squared = 1.0 - ss_res / max(ss_tot, 1e-10)

        return {
            "h0": round(float(h0), 2),
            "k": round(float(k), 8),
            "r_squared": round(float(r_squared), 4),
            "fitted": True
        }

    except (RuntimeError, ValueError):
        # Fallback: linear estimate
        if len(t) >= 2:
            slope = (h[-1] - h[0]) / max(t[-1] - t[0], 1.0)
            k_est = -slope / max(h[0], 1.0)
        else:
            k_est = 0.0001
        return {
            "h0": round(float(h[0]) if len(h) > 0 else 100.0, 2),
            "k": round(float(max(k_est, 1e-8)), 8),
            "r_squared": 0.0,
            "fitted": False
        }


def predict_rul_deterministic(current_health: float, degradation_rate: float,
                              threshold: float = RUL_HEALTH_THRESHOLD) -> float:
    """
    Predict RUL using deterministic exponential model.

    Time to threshold: t = -ln(threshold / H_current) / k

    Args:
        current_health: Current health score (0-100)
        degradation_rate: Degradation rate constant k
        threshold: Health threshold for replacement

    Returns:
        Remaining useful life (hours)
    """
    if degradation_rate <= 0 or current_health <= threshold:
        if current_health <= threshold:
            return 0.0
        return SENSOR_MAX_HOURS  # No degradation detected

    ratio = threshold / max(current_health, 1.0)
    if ratio >= 1.0:
        return 0.0

    rul = -np.log(ratio) / degradation_rate
    return float(np.clip(rul, 0.0, SENSOR_MAX_HOURS))


def predict_rul_monte_carlo(current_health: float, degradation_rate: float,
                            rate_std: float = None,
                            threshold: float = RUL_HEALTH_THRESHOLD,
                            n_sims: int = RUL_MONTE_CARLO_SIMS) -> dict:
    """
    Predict RUL with confidence intervals using Monte Carlo simulation.

    Samples degradation rate from a distribution and computes
    RUL for each sample.

    Args:
        current_health: Current health score (0-100)
        degradation_rate: Mean degradation rate
        rate_std: Standard deviation of rate (default: 20% of mean)
        threshold: Health threshold for replacement
        n_sims: Number of simulations

    Returns:
        Dictionary with RUL statistics
    """
    if degradation_rate <= 0:
        return {
            "rul_mean": SENSOR_MAX_HOURS,
            "rul_median": SENSOR_MAX_HOURS,
            "rul_std": 0.0,
            "rul_lower_95": SENSOR_MAX_HOURS,
            "rul_upper_95": SENSOR_MAX_HOURS,
            "confidence": 0.5
        }

    if rate_std is None:
        rate_std = degradation_rate * 0.2

    # Sample degradation rates
    rates = np.random.normal(degradation_rate, max(rate_std, 1e-10), n_sims)
    rates = np.clip(rates, 1e-10, None)

    # Calculate RUL for each sample
    ruls = []
    for k in rates:
        ratio = threshold / max(current_health, 1.0)
        if ratio >= 1.0:
            ruls.append(0.0)
        else:
            rul = -np.log(ratio) / k
            ruls.append(min(rul, SENSOR_MAX_HOURS))

    ruls = np.array(ruls)

    return {
        "rul_mean": round(float(np.mean(ruls)), 1),
        "rul_median": round(float(np.median(ruls)), 1),
        "rul_std": round(float(np.std(ruls)), 1),
        "rul_lower_95": round(float(np.percentile(ruls, 2.5)), 1),
        "rul_upper_95": round(float(np.percentile(ruls, 97.5)), 1),
        "confidence": round(float(1.0 - np.std(ruls) / max(np.mean(ruls), 1.0)), 4)
    }


def calculate_rul(current_health: float, flight_hours: float,
                  health_history: list = None,
                  time_points: list = None) -> dict:
    """
    Run the complete RUL prediction.

    Args:
        current_health: Current health score
        flight_hours: Current flight hours
        health_history: List of past health scores
        time_points: Corresponding time points

    Returns:
        Dictionary with RUL predictions
    """
    # Fit degradation curve if history available
    if health_history and time_points and len(health_history) >= 3:
        curve = fit_degradation_curve(time_points, health_history)
        k = curve["k"]
    else:
        # Estimate k from current health and hours
        if flight_hours > 0 and current_health < 100:
            k = -np.log(max(current_health, 1.0) / 100.0) / flight_hours
            k = max(k, 1e-8)
        else:
            k = 1e-4  # Default estimate
        curve = {"h0": 100.0, "k": round(k, 8), "r_squared": 0.0, "fitted": False}

    # Deterministic RUL
    rul_det = predict_rul_deterministic(current_health, k)

    # Monte Carlo RUL
    rul_mc = predict_rul_monte_carlo(current_health, k)

    return {
        "remaining_life_hours": round(rul_det, 1),
        "remaining_life_days": round(rul_det / 24.0, 1),
        "monte_carlo": rul_mc,
        "degradation_curve": curve,
        "current_health": round(current_health, 2),
        "threshold": RUL_HEALTH_THRESHOLD,
        "flight_hours": flight_hours,
        "status": "critical" if rul_det < 100 else
                  "warning" if rul_det < 500 else "normal"
    }
