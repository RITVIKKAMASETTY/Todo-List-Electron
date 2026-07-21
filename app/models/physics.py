"""
Physics Model — Nernst Equation for Zirconia Oxygen Sensor.

The Nernst equation describes the electromotive force (EMF) generated
by a zirconia oxygen sensor based on the oxygen partial pressure
difference across the solid electrolyte.

    E = (R × T) / (n × F) × ln(P_ref / P_O2)

Where:
    E   = EMF voltage (V)
    R   = Universal gas constant (8.314 J/(mol·K))
    T   = Absolute temperature (K)
    n   = Number of electrons (4 for O2)
    F   = Faraday constant (96485 C/mol)
    P_ref = Reference oxygen partial pressure (0.2095 atm for air)
    P_O2  = Measured oxygen partial pressure
"""

import numpy as np
from app.config import (
    R_GAS, FARADAY, NERNST_ELECTRONS, REFERENCE_O2_PRESSURE,
    NOMINAL_PRESSURE
)


def oxygen_to_partial_pressure(oxygen_percent: float, total_pressure_psi: float) -> float:
    """
    Convert oxygen percentage and total pressure to O2 partial pressure in atm.

    Args:
        oxygen_percent: Oxygen concentration (0-100%)
        total_pressure_psi: Total gas pressure in psi

    Returns:
        Oxygen partial pressure in atmospheres
    """
    total_pressure_atm = total_pressure_psi / 14.696  # psi to atm
    return (oxygen_percent / 100.0) * total_pressure_atm


def nernst_voltage(temperature_c: float, oxygen_percent: float,
                   total_pressure_psi: float = NOMINAL_PRESSURE) -> float:
    """
    Calculate the ideal Nernst EMF voltage.

    This is what a perfect sensor would output under the given conditions.

    Args:
        temperature_c: Sensor temperature in Celsius
        oxygen_percent: Oxygen concentration (0-100%)
        total_pressure_psi: Total pressure in psi

    Returns:
        Ideal EMF voltage (V)
    """
    temperature_k = temperature_c + 273.15
    p_o2 = oxygen_to_partial_pressure(oxygen_percent, total_pressure_psi)

    # Prevent log(0) or log(negative)
    p_o2 = max(p_o2, 1e-10)

    # Nernst equation: E = (RT / nF) × ln(P_ref / P_O2)
    emf = (R_GAS * temperature_k) / (NERNST_ELECTRONS * FARADAY) * \
          np.log(REFERENCE_O2_PRESSURE / p_o2)

    return float(emf)


def voltage_to_oxygen(voltage: float, temperature_c: float,
                      total_pressure_psi: float = NOMINAL_PRESSURE) -> float:
    """
    Inverse Nernst: convert measured voltage back to oxygen percentage.

    Args:
        voltage: Measured sensor voltage (V)
        temperature_c: Sensor temperature (°C)
        total_pressure_psi: Total pressure (psi)

    Returns:
        Estimated oxygen percentage (0-100%)
    """
    temperature_k = temperature_c + 273.15
    total_pressure_atm = total_pressure_psi / 14.696

    # Rearrange Nernst: P_O2 = P_ref × exp(-nFE / RT)
    exponent = -(NERNST_ELECTRONS * FARADAY * voltage) / (R_GAS * temperature_k)
    p_o2 = REFERENCE_O2_PRESSURE * np.exp(exponent)

    oxygen_percent = (p_o2 / total_pressure_atm) * 100.0
    return float(np.clip(oxygen_percent, 0.0, 100.0))


def ideal_current(voltage: float, internal_resistance: float = 100.0) -> float:
    """
    Calculate the ideal sensor current based on voltage and internal resistance.

    Args:
        voltage: Sensor EMF voltage (V)
        internal_resistance: Sensor internal resistance (Ω)

    Returns:
        Current (A)
    """
    return voltage / internal_resistance


def pressure_compensation(voltage: float, actual_pressure_psi: float,
                          reference_pressure_psi: float = NOMINAL_PRESSURE) -> float:
    """
    Compensate voltage reading for pressure differences from nominal.

    Args:
        voltage: Raw measured voltage (V)
        actual_pressure_psi: Actual measured pressure (psi)
        reference_pressure_psi: Reference/nominal pressure (psi)

    Returns:
        Pressure-compensated voltage (V)
    """
    pressure_ratio = actual_pressure_psi / reference_pressure_psi
    # Higher pressure → lower voltage for same O2 concentration
    compensation_factor = 1.0 + 0.02 * (1.0 - pressure_ratio)
    return voltage * compensation_factor


def altitude_to_pressure(altitude_ft: float) -> float:
    """
    Estimate atmospheric pressure from altitude using barometric formula.

    Args:
        altitude_ft: Altitude in feet

    Returns:
        Estimated pressure in psi
    """
    altitude_m = altitude_ft * 0.3048
    # Barometric formula: P = P0 × (1 - L×h/T0)^(gM/RL)
    p_atm = 1.01325e5 * (1 - 2.25577e-5 * altitude_m) ** 5.25588
    return float(p_atm / 6894.76)  # Pa to psi


def calculate_physics(sensor_data: dict) -> dict:
    """
    Run the complete physics model on a sensor reading.

    Args:
        sensor_data: Dictionary with oxygen, temperature, pressure, etc.

    Returns:
        Dictionary with ideal voltage, estimated O2, compensated values
    """
    temperature = sensor_data.get("temperature", 700.0)
    oxygen = sensor_data.get("oxygen", 93.0)
    pressure = sensor_data.get("pressure", 29.0)
    measured_voltage = sensor_data.get("voltage", 0.82)

    ideal_v = nernst_voltage(temperature, oxygen, pressure)
    estimated_o2 = voltage_to_oxygen(measured_voltage, temperature, pressure)
    compensated_v = pressure_compensation(measured_voltage, pressure)
    residual = measured_voltage - ideal_v

    return {
        "ideal_voltage": round(ideal_v, 6),
        "estimated_oxygen": round(estimated_o2, 2),
        "compensated_voltage": round(compensated_v, 6),
        "residual": round(residual, 6),
        "voltage_error_percent": round(abs(residual / ideal_v) * 100, 2) if ideal_v != 0 else 0.0
    }
