"""
Aging Model — Sensor Degradation Over Time.

Models how the zirconia oxygen sensor degrades through:
    - Arrhenius-based chemical degradation: k = A × exp(-Ea / (R × T))
    - Sensitivity decay: S(t) = S₀ × exp(-k × t)
    - Electrode sintering (grain growth)
    - Thermal cycling fatigue (Coffin-Manson): N_f = C × (ΔT)^(-n)

The aging model tracks flight hours and thermal cycles to
estimate the cumulative degradation of the sensor.
"""

import numpy as np
from app.config import (
    R_GAS, SENSOR_MAX_HOURS, AGING_ACTIVATION_ENERGY,
    AGING_PRE_EXPONENTIAL, AGING_SENSITIVITY_INITIAL,
    COFFIN_MANSON_C, COFFIN_MANSON_N, BOLTZMANN
)


def arrhenius_rate(temperature_c: float) -> float:
    """
    Calculate the Arrhenius degradation rate constant.

    k = A × exp(-Ea / (k_B × T))

    Higher temperature → faster degradation.

    Args:
        temperature_c: Operating temperature (°C)

    Returns:
        Degradation rate constant (1/hour)
    """
    temperature_k = temperature_c + 273.15
    k = AGING_PRE_EXPONENTIAL * np.exp(
        -AGING_ACTIVATION_ENERGY / (BOLTZMANN * temperature_k)
    )
    return float(k)


def sensitivity_decay(flight_hours: float, temperature_c: float = 700.0,
                      s0: float = AGING_SENSITIVITY_INITIAL) -> float:
    """
    Calculate sensitivity decay due to aging.

    S(t) = S₀ × exp(-k × t)

    Args:
        flight_hours: Total operating hours
        temperature_c: Average operating temperature (°C)
        s0: Initial sensitivity

    Returns:
        Current sensitivity (normalized, 0-1)
    """
    k = arrhenius_rate(temperature_c)
    s = s0 * np.exp(-k * flight_hours)
    return float(np.clip(s, 0.1, 1.0))


def electrode_sintering(flight_hours: float, temperature_c: float = 700.0) -> float:
    """
    Model electrode grain growth (sintering).

    Grain size increases with time and temperature, reducing
    the triple-phase boundary (TPB) length where reactions occur.

    grain_size(t) = grain_size_0 × (1 + α × t^(1/n))

    Args:
        flight_hours: Total operating hours
        temperature_c: Operating temperature (°C)

    Returns:
        Electrode degradation factor (0 = no degradation, 1 = max)
    """
    temperature_k = temperature_c + 273.15
    # Grain growth rate depends on temperature
    growth_rate = 1e-4 * np.exp(-0.8 * 1.602e-19 / (BOLTZMANN * temperature_k))
    # Parabolic growth law: d² - d₀² = K × t
    relative_growth = growth_rate * flight_hours
    degradation = 1.0 - np.exp(-relative_growth)
    return float(np.clip(degradation, 0.0, 0.8))


def thermal_cycle_fatigue(thermal_cycles: int,
                          delta_t: float = 675.0) -> float:
    """
    Calculate thermal cycling fatigue using Coffin-Manson relation.

    N_f = C × (ΔT)^(-n)

    The sensor cracks or delaminates after N_f cycles.

    Args:
        thermal_cycles: Number of thermal cycles experienced
        delta_t: Temperature swing per cycle (°C), default ~675°C (25→700)

    Returns:
        Fatigue damage fraction (0 = no damage, 1 = failure)
    """
    # Cycles to failure
    n_f = COFFIN_MANSON_C * (delta_t ** (-COFFIN_MANSON_N))
    n_f = max(n_f, 1.0)

    # Cumulative damage (Miner's rule)
    damage = thermal_cycles / n_f
    return float(np.clip(damage, 0.0, 1.0))


def aging_factor(flight_hours: float, thermal_cycles: int,
                 temperature_c: float = 700.0,
                 humidity: float = 10.0) -> float:
    """
    Calculate the overall aging factor combining all degradation mechanisms.

    Args:
        flight_hours: Total operating hours
        thermal_cycles: Number of thermal cycles
        temperature_c: Average operating temperature (°C)
        humidity: Average humidity (%)

    Returns:
        Overall aging factor (0 = new, 1 = end of life)
    """
    # Time-based aging (normalized to max hours)
    time_aging = 1.0 - np.exp(-2.0 * flight_hours / SENSOR_MAX_HOURS)

    # Thermal cycling damage
    cycle_damage = thermal_cycle_fatigue(thermal_cycles)

    # Electrode degradation
    electrode_deg = electrode_sintering(flight_hours, temperature_c)

    # Humidity accelerates aging (poisoning)
    humidity_factor = 1.0 + 0.005 * max(humidity - 20.0, 0.0)

    # Combine: weighted average
    aging = (0.4 * time_aging + 0.3 * cycle_damage + 0.3 * electrode_deg) * humidity_factor

    return float(np.clip(aging, 0.0, 1.0))


def heater_degradation(flight_hours: float, thermal_cycles: int) -> float:
    """
    Model heater element degradation.

    Heater resistance increases over time, reducing heating efficiency.

    Args:
        flight_hours: Total operating hours
        thermal_cycles: Number of thermal cycles

    Returns:
        Heater efficiency (1.0 = new, 0.0 = failed)
    """
    # Gradual efficiency loss
    time_factor = np.exp(-0.5 * flight_hours / SENSOR_MAX_HOURS)
    cycle_factor = np.exp(-0.001 * thermal_cycles)

    efficiency = time_factor * cycle_factor
    return float(np.clip(efficiency, 0.0, 1.0))


def calculate_aging(sensor_data: dict) -> dict:
    """
    Run the complete aging model.

    Args:
        sensor_data: Dictionary with flight_hours, thermal_cycles, temperature, humidity

    Returns:
        Dictionary with aging analysis results
    """
    hours = sensor_data.get("flight_hours", 0.0)
    cycles = sensor_data.get("thermal_cycles", 0)
    temp = sensor_data.get("heater_temp", 700.0)
    humid = sensor_data.get("humidity", 10.0)

    af = aging_factor(hours, cycles, temp, humid)
    sens = sensitivity_decay(hours, temp)
    electrode = electrode_sintering(hours, temp)
    fatigue = thermal_cycle_fatigue(cycles)
    heater_eff = heater_degradation(hours, cycles)

    return {
        "aging_factor": round(af, 4),
        "sensitivity": round(sens, 4),
        "electrode_degradation": round(electrode, 4),
        "thermal_fatigue": round(fatigue, 4),
        "heater_efficiency": round(heater_eff, 4),
        "estimated_life_fraction": round(1.0 - af, 4),
        "flight_hours": hours,
        "thermal_cycles": cycles
    }
