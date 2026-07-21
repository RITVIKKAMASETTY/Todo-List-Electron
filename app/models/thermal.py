"""
Thermal Model — Heat Balance for Zirconia Sensor Element.

Models the sensor's operating temperature using a lumped-parameter
approach considering:
    - Heater power input
    - Convective heat loss to air
    - Radiative heat loss
    - Thermal mass of the sensor element

    dT/dt = (Q_heater - Q_conv - Q_rad) / (m × Cp)

The sensor must maintain ~700°C for proper operation.
Temperature deviations affect voltage accuracy via the Nernst equation.
"""

import numpy as np
from app.config import (
    SENSOR_OPERATING_TEMP, SENSOR_HEATER_POWER, SENSOR_MASS,
    SENSOR_SPECIFIC_HEAT, SENSOR_SURFACE_AREA, SENSOR_EMISSIVITY,
    STEFAN_BOLTZMANN
)


def convective_heat_loss(sensor_temp_c: float, air_temp_c: float,
                         flow_rate: float, h_base: float = 50.0) -> float:
    """
    Calculate convective heat loss from sensor to surrounding air.

    Q_conv = h × A × (T_sensor - T_air)

    The heat transfer coefficient h scales with airflow rate.

    Args:
        sensor_temp_c: Sensor temperature (°C)
        air_temp_c: Ambient air temperature (°C)
        flow_rate: Air flow rate (L/min)
        h_base: Base convective heat transfer coefficient (W/(m²·K))

    Returns:
        Convective heat loss (W)
    """
    # h increases with flow rate (forced convection)
    h = h_base * (1.0 + 0.1 * flow_rate)
    q_conv = h * SENSOR_SURFACE_AREA * (sensor_temp_c - air_temp_c)
    return float(q_conv)


def radiative_heat_loss(sensor_temp_c: float, ambient_temp_c: float = 25.0) -> float:
    """
    Calculate radiative heat loss using Stefan-Boltzmann law.

    Q_rad = ε × σ × A × (T_sensor⁴ - T_ambient⁴)

    Args:
        sensor_temp_c: Sensor temperature (°C)
        ambient_temp_c: Ambient temperature (°C)

    Returns:
        Radiative heat loss (W)
    """
    t_sensor_k = sensor_temp_c + 273.15
    t_ambient_k = ambient_temp_c + 273.15

    q_rad = (SENSOR_EMISSIVITY * STEFAN_BOLTZMANN * SENSOR_SURFACE_AREA *
             (t_sensor_k**4 - t_ambient_k**4))
    return float(q_rad)


def heater_power(target_temp: float = SENSOR_OPERATING_TEMP,
                 current_temp: float = 700.0,
                 max_power: float = SENSOR_HEATER_POWER,
                 heater_efficiency: float = 1.0) -> float:
    """
    Simple PID-like heater power model.

    The heater adjusts power to maintain the target operating temperature.
    Efficiency degrades with sensor aging.

    Args:
        target_temp: Target temperature (°C)
        current_temp: Current sensor temperature (°C)
        max_power: Maximum heater power (W)
        heater_efficiency: Heater efficiency (0-1), decreases with aging

    Returns:
        Applied heater power (W)
    """
    error = target_temp - current_temp
    # Proportional control: full power if >50°C below target
    power_fraction = np.clip(error / 50.0, 0.0, 1.0)
    return float(max_power * power_fraction * heater_efficiency)


def temperature_rate_of_change(sensor_temp_c: float, air_temp_c: float,
                               flow_rate: float, heater_eff: float = 1.0,
                               ambient_temp_c: float = 25.0) -> float:
    """
    Calculate the rate of temperature change (dT/dt).

    dT/dt = (Q_heater - Q_conv - Q_rad) / (m × Cp)

    Args:
        sensor_temp_c: Current sensor temperature (°C)
        air_temp_c: Air temperature near sensor (°C)
        flow_rate: Air flow rate (L/min)
        heater_eff: Heater efficiency factor (0-1)
        ambient_temp_c: Ambient temperature for radiation (°C)

    Returns:
        Temperature change rate (°C/s)
    """
    q_heater = heater_power(
        target_temp=SENSOR_OPERATING_TEMP,
        current_temp=sensor_temp_c,
        heater_efficiency=heater_eff
    )
    q_conv = convective_heat_loss(sensor_temp_c, air_temp_c, flow_rate)
    q_rad = radiative_heat_loss(sensor_temp_c, ambient_temp_c)

    thermal_mass = SENSOR_MASS * SENSOR_SPECIFIC_HEAT  # J/K

    dt_dt = (q_heater - q_conv - q_rad) / thermal_mass
    return float(dt_dt)


def estimate_sensor_temperature(current_temp_c: float, air_temp_c: float,
                                flow_rate: float, dt: float = 1.0,
                                heater_eff: float = 1.0) -> float:
    """
    Estimate the sensor temperature after one time step using Euler integration.

    T_new = T_current + dT/dt × dt

    Args:
        current_temp_c: Current sensor temperature (°C)
        air_temp_c: Air temperature (°C)
        flow_rate: Air flow rate (L/min)
        dt: Time step (seconds)
        heater_eff: Heater efficiency (0-1)

    Returns:
        New sensor temperature (°C)
    """
    rate = temperature_rate_of_change(
        sensor_temp_c=current_temp_c,
        air_temp_c=air_temp_c,
        flow_rate=flow_rate,
        heater_eff=heater_eff
    )
    new_temp = current_temp_c + rate * dt
    return float(np.clip(new_temp, 0.0, 1000.0))


def thermal_time_constant() -> float:
    """
    Calculate the thermal time constant of the sensor element.

    τ = m × Cp / (h × A)

    Returns:
        Time constant in seconds
    """
    h_nominal = 50.0  # Nominal heat transfer coefficient
    tau = (SENSOR_MASS * SENSOR_SPECIFIC_HEAT) / (h_nominal * SENSOR_SURFACE_AREA)
    return float(tau)


def calculate_thermal(sensor_data: dict, current_sensor_temp: float = 700.0,
                      heater_eff: float = 1.0) -> dict:
    """
    Run the complete thermal model on a sensor reading.

    Args:
        sensor_data: Dictionary with temperature, flow, etc.
        current_sensor_temp: Current sensor element temperature (°C)
        heater_eff: Heater efficiency (0-1)

    Returns:
        Dictionary with thermal analysis results
    """
    air_temp = sensor_data.get("temperature", 700.0)
    flow = sensor_data.get("flow", 11.0)

    q_heater = heater_power(
        current_temp=current_sensor_temp,
        heater_efficiency=heater_eff
    )
    q_conv = convective_heat_loss(current_sensor_temp, air_temp, flow)
    q_rad = radiative_heat_loss(current_sensor_temp)
    new_temp = estimate_sensor_temperature(
        current_sensor_temp, air_temp, flow,
        heater_eff=heater_eff
    )
    dt_dt = temperature_rate_of_change(
        current_sensor_temp, air_temp, flow,
        heater_eff=heater_eff
    )

    return {
        "sensor_temperature": round(new_temp, 2),
        "heater_power": round(q_heater, 4),
        "convective_loss": round(q_conv, 4),
        "radiative_loss": round(q_rad, 4),
        "temperature_rate": round(dt_dt, 4),
        "thermal_equilibrium": abs(dt_dt) < 0.01,
        "time_constant": round(thermal_time_constant(), 2)
    }
