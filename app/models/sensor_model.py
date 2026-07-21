"""
Sensor Model — Electrical and Response Characteristics.

Models the electrical behavior of the zirconia oxygen sensor:
    - Impedance model (bulk + electrode + grain boundary resistance)
    - Sensitivity curve: S(T) = S₀ × exp(-Ea / (kT))
    - Response time model (first-order lag): τ × dy/dt + y = x
    - Signal conditioning (filtering, amplification)
"""

import numpy as np
from app.config import BOLTZMANN, SENSOR_OPERATING_TEMP_K


def impedance_model(temperature_c: float, aging_factor: float = 0.0) -> dict:
    """
    Calculate the sensor impedance components.

    Z_total = R_bulk + R_electrode + R_grain_boundary

    Impedance increases with aging due to electrode sintering
    and grain boundary degradation.

    Args:
        temperature_c: Sensor temperature (°C)
        aging_factor: Aging degradation factor (0 = new, 1 = end of life)

    Returns:
        Dictionary with impedance components (Ω)
    """
    temperature_k = temperature_c + 273.15

    # Base resistances at operating temperature (Ω)
    # These follow Arrhenius-type temperature dependence
    ea_bulk = 0.9 * 1.602e-19       # ~0.9 eV activation energy
    ea_electrode = 1.1 * 1.602e-19  # ~1.1 eV
    ea_grain = 1.0 * 1.602e-19      # ~1.0 eV

    # Reference resistances at 700°C
    r_bulk_ref = 50.0      # Ω
    r_electrode_ref = 30.0 # Ω
    r_grain_ref = 20.0     # Ω

    # Temperature dependence: R(T) = R_ref × exp(Ea/k × (1/T - 1/T_ref))
    temp_factor = lambda ea: np.exp(
        (ea / BOLTZMANN) * (1.0 / temperature_k - 1.0 / SENSOR_OPERATING_TEMP_K)
    )

    r_bulk = r_bulk_ref * temp_factor(ea_bulk) * (1.0 + 0.3 * aging_factor)
    r_electrode = r_electrode_ref * temp_factor(ea_electrode) * (1.0 + 0.8 * aging_factor)
    r_grain = r_grain_ref * temp_factor(ea_grain) * (1.0 + 0.5 * aging_factor)

    return {
        "r_bulk": round(float(r_bulk), 2),
        "r_electrode": round(float(r_electrode), 2),
        "r_grain_boundary": round(float(r_grain), 2),
        "r_total": round(float(r_bulk + r_electrode + r_grain), 2)
    }


def sensitivity(temperature_c: float, aging_factor: float = 0.0,
                s0: float = 1.0) -> float:
    """
    Calculate sensor sensitivity as a function of temperature and aging.

    S(T) = S₀ × exp(-Ea / (k × T)) × (1 - aging_factor × degradation_rate)

    Sensitivity determines how accurately the sensor responds to
    changes in oxygen concentration.

    Args:
        temperature_c: Sensor temperature (°C)
        aging_factor: Aging factor (0-1)
        s0: Initial sensitivity (normalized)

    Returns:
        Sensitivity (0-1, normalized)
    """
    temperature_k = temperature_c + 273.15
    ea_sensitivity = 0.5 * 1.602e-19  # ~0.5 eV

    # Temperature dependence of sensitivity
    temp_effect = np.exp(
        -(ea_sensitivity / BOLTZMANN) *
        (1.0 / temperature_k - 1.0 / SENSOR_OPERATING_TEMP_K)
    )

    # Aging effect on sensitivity
    age_effect = 1.0 - 0.4 * aging_factor  # Up to 40% sensitivity loss

    s = s0 * float(temp_effect) * max(age_effect, 0.1)
    return float(np.clip(s, 0.0, 1.5))


def response_time(temperature_c: float, aging_factor: float = 0.0) -> float:
    """
    Calculate the sensor response time (time constant τ).

    Response time increases at lower temperatures and with aging.
    Typical: 1-5 seconds for a healthy sensor at operating temperature.

    Args:
        temperature_c: Sensor temperature (°C)
        aging_factor: Aging factor (0-1)

    Returns:
        Response time constant τ (seconds)
    """
    # Base response time at operating temperature
    tau_base = 2.0  # seconds

    # Temperature effect: slower response at lower temperatures
    temp_ratio = SENSOR_OPERATING_TEMP / max(temperature_c, 100.0)
    tau = tau_base * temp_ratio ** 2

    # Aging effect: response slows with aging
    tau *= (1.0 + 2.0 * aging_factor)

    return float(np.clip(tau, 0.5, 30.0))


def first_order_lag(current_output: float, true_input: float,
                    tau: float, dt: float = 1.0) -> float:
    """
    Apply first-order lag (low-pass filter) to sensor response.

    τ × dy/dt + y = x  →  y_new = y_old + (x - y_old) × dt / (τ + dt)

    This models the sensor's inability to instantly respond to
    changes in oxygen concentration.

    Args:
        current_output: Current sensor output
        true_input: True input value
        tau: Time constant (seconds)
        dt: Time step (seconds)

    Returns:
        Filtered sensor output
    """
    alpha = dt / (tau + dt)
    return current_output + alpha * (true_input - current_output)


def apply_sensitivity(ideal_voltage: float, sensitivity_value: float,
                      reference_voltage: float = 0.0) -> float:
    """
    Apply sensitivity factor to the ideal voltage.

    A sensitivity of 1.0 means perfect response.
    Lower sensitivity means the sensor under-reports changes.

    Args:
        ideal_voltage: Ideal Nernst voltage (V)
        sensitivity_value: Current sensitivity (0-1)
        reference_voltage: Baseline voltage at reference conditions

    Returns:
        Sensitivity-adjusted voltage (V)
    """
    delta_v = ideal_voltage - reference_voltage
    return reference_voltage + delta_v * sensitivity_value


def calculate_sensor_model(sensor_data: dict, aging_factor: float = 0.0,
                           current_output: float = None) -> dict:
    """
    Run the complete sensor model.

    Args:
        sensor_data: Dictionary with temperature, voltage, etc.
        aging_factor: Current aging factor (0-1)
        current_output: Previous output for lag calculation

    Returns:
        Dictionary with sensor model results
    """
    temperature = sensor_data.get("heater_temp", 700.0)
    voltage = sensor_data.get("voltage", 0.82)

    imp = impedance_model(temperature, aging_factor)
    sens = sensitivity(temperature, aging_factor)
    tau = response_time(temperature, aging_factor)

    # Apply first-order lag if previous output available
    if current_output is not None:
        lagged_voltage = first_order_lag(current_output, voltage, tau)
    else:
        lagged_voltage = voltage

    return {
        "impedance": imp,
        "sensitivity": round(sens, 4),
        "response_time": round(tau, 2),
        "lagged_voltage": round(lagged_voltage, 6),
        "adjusted_voltage": round(apply_sensitivity(voltage, sens), 6)
    }
