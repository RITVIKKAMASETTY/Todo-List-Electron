"""
Configuration and Physical Constants for the Digital Twin.

Contains all physical constants, sensor specifications, operating ranges,
and system configuration used across the models.
"""

import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "twin.db"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

# ─── Physical Constants ─────────────────────────────────────────────────────
R_GAS = 8.314          # Universal gas constant (J/(mol·K))
FARADAY = 96485.0      # Faraday constant (C/mol)
BOLTZMANN = 1.381e-23  # Boltzmann constant (J/K)
STEFAN_BOLTZMANN = 5.67e-8  # Stefan-Boltzmann constant (W/(m²·K⁴))

# ─── Nernst Equation Parameters ─────────────────────────────────────────────
NERNST_ELECTRONS = 4           # Electrons transferred in O2 reaction
REFERENCE_O2_PRESSURE = 0.2095 # Reference O2 partial pressure (atm, ambient air)

# ─── Zirconia Sensor Specifications ──────────────────────────────────────────
SENSOR_OPERATING_TEMP = 700.0    # Nominal operating temperature (°C)
SENSOR_OPERATING_TEMP_K = 973.15 # Nominal operating temperature (K)
SENSOR_MAX_HOURS = 5000.0        # Maximum rated life (hours)
SENSOR_HEATER_POWER = 8.0        # Heater power (W)
SENSOR_MASS = 0.015              # Sensor element mass (kg)
SENSOR_SPECIFIC_HEAT = 500.0     # Specific heat capacity (J/(kg·K))
SENSOR_SURFACE_AREA = 2.0e-4    # Surface area (m²)
SENSOR_EMISSIVITY = 0.85        # Emissivity for radiation

# ─── Sensor Operating Ranges ────────────────────────────────────────────────
OXYGEN_RANGE = (0.0, 100.0)         # Oxygen concentration (%)
TEMPERATURE_RANGE = (600.0, 800.0)  # Operating temp range (°C)
PRESSURE_RANGE = (20.0, 40.0)       # Pressure range (psi)
FLOW_RANGE = (5.0, 20.0)            # Flow rate range (L/min)
HUMIDITY_RANGE = (0.0, 50.0)        # Humidity range (%)
VOLTAGE_RANGE = (0.0, 1.2)          # Output voltage range (V)
CURRENT_RANGE = (0.0, 0.5)          # Output current range (A)
ALTITUDE_RANGE = (0, 50000)         # Altitude range (feet)

# ─── Nominal Sensor Values ──────────────────────────────────────────────────
NOMINAL_OXYGEN = 93.0       # OBOGS nominal oxygen output (%)
NOMINAL_TEMPERATURE = 700.0 # °C
NOMINAL_PRESSURE = 29.0     # psi
NOMINAL_FLOW = 11.0         # L/min
NOMINAL_HUMIDITY = 10.0     # %
NOMINAL_VOLTAGE = 0.82      # V
NOMINAL_CURRENT = 0.21      # A

# ─── Aging Model Parameters ─────────────────────────────────────────────────
AGING_ACTIVATION_ENERGY = 1.2e-19  # Activation energy (J) for Arrhenius
AGING_PRE_EXPONENTIAL = 1.0e-4     # Pre-exponential factor
AGING_SENSITIVITY_INITIAL = 1.0    # Initial sensitivity (normalized)
COFFIN_MANSON_C = 1.0e6            # Coffin-Manson constant
COFFIN_MANSON_N = 2.5              # Coffin-Manson exponent

# ─── Drift Model Parameters ─────────────────────────────────────────────────
DRIFT_LINEAR_RATE = 0.001      # Linear drift rate (%/hour)
DRIFT_SINUSOIDAL_AMP = 0.05   # Sinusoidal drift amplitude (%)
DRIFT_SINUSOIDAL_FREQ = 0.01  # Sinusoidal drift frequency (rad/hour)
DRIFT_QUADRATIC_RATE = 1e-7   # Quadratic drift coefficient

# ─── Noise Model Parameters ─────────────────────────────────────────────────
NOISE_WHITE_SIGMA = 0.02      # White noise std dev (%)
NOISE_FLICKER_BASE = 0.005    # 1/f noise base amplitude
NOISE_QUANTIZATION = 0.01     # Quantization step size
NOISE_EMI_PROBABILITY = 0.02  # Probability of EMI spike per reading
NOISE_EMI_AMPLITUDE = 0.5     # EMI spike amplitude

# ─── Fault Detection Thresholds ──────────────────────────────────────────────
FAULT_RESIDUAL_THRESHOLD = 2.0   # Residual threshold for anomaly (%)
FAULT_VOLTAGE_DROP_LIMIT = 0.6   # Minimum acceptable voltage (V)
FAULT_HEATER_TEMP_MIN = 600.0    # Minimum heater temp (°C) — failure if below
FAULT_PRESSURE_LEAK_RATE = 0.5   # Pressure drop rate threshold (psi/min)

# ─── Health Index Weights ────────────────────────────────────────────────────
HEALTH_WEIGHT_DRIFT = 0.25
HEALTH_WEIGHT_NOISE = 0.15
HEALTH_WEIGHT_FAULT = 0.25
HEALTH_WEIGHT_SENSITIVITY = 0.20
HEALTH_WEIGHT_AGE = 0.15

# ─── Alert Thresholds ───────────────────────────────────────────────────────
ALERT_HEALTH_WARNING = 75.0       # Health score below this → warning
ALERT_HEALTH_CRITICAL = 50.0      # Health score below this → critical
ALERT_DRIFT_WARNING = 1.5         # Drift above this → warning (%)
ALERT_DRIFT_CRITICAL = 3.0        # Drift above this → critical (%)
ALERT_RUL_WARNING = 500           # RUL below this → warning (hours)
ALERT_RUL_CRITICAL = 100          # RUL below this → critical (hours)
ALERT_OXYGEN_LOW = 85.0           # Oxygen below this → critical (%)
ALERT_DEDUP_WINDOW = 300          # Don't repeat same alert within N seconds

# ─── Kalman Filter Parameters ───────────────────────────────────────────────
KALMAN_PROCESS_NOISE = 0.01       # Process noise covariance
KALMAN_MEASUREMENT_NOISE = 0.1    # Measurement noise covariance

# ─── RUL Parameters ─────────────────────────────────────────────────────────
RUL_HEALTH_THRESHOLD = 60.0       # Replacement threshold (%)
RUL_MONTE_CARLO_SIMS = 100        # Number of Monte Carlo simulations

# ─── Simulation Settings ────────────────────────────────────────────────────
SIMULATION_INTERVAL = 1.0         # Seconds between readings
SIMULATION_TIME_ACCELERATION = 10 # 1 real second = N simulated hours
SIMULATION_INITIAL_FLIGHT_HOURS = 0

# ─── Server Settings ────────────────────────────────────────────────────────
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
