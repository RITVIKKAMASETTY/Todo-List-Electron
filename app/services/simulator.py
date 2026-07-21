"""
Sensor Simulator — Synthetic Data Generator for OBOGS Oxygen Sensor.

Generates realistic flight profiles and sensor readings:
    - Ground → Climb → Cruise → Descent → Ground cycle
    - Environmental variations (temperature, pressure, humidity)
    - Sensor aging over simulated flight hours
    - Fault injection capabilities

Each tick produces one complete sensor reading that flows
through the entire model pipeline.
"""

import numpy as np
import asyncio
from datetime import datetime
from app.config import (
    NOMINAL_OXYGEN, NOMINAL_TEMPERATURE, NOMINAL_PRESSURE,
    NOMINAL_FLOW, NOMINAL_HUMIDITY, NOMINAL_VOLTAGE, NOMINAL_CURRENT,
    SIMULATION_INTERVAL, SIMULATION_TIME_ACCELERATION,
    SENSOR_OPERATING_TEMP
)


class FlightProfile:
    """Simulates aircraft flight phases for realistic data generation."""

    PHASES = ["ground", "climb", "cruise", "descent", "ground"]
    PHASE_DURATIONS = [60, 120, 600, 120, 60]  # ticks per phase

    def __init__(self):
        self.phase_index = 0
        self.phase_tick = 0
        self.altitude = 0.0  # feet

    def get_phase(self) -> str:
        return self.PHASES[self.phase_index]

    def tick(self) -> dict:
        """Advance one tick and return flight conditions."""
        phase = self.get_phase()
        duration = self.PHASE_DURATIONS[self.phase_index]
        progress = self.phase_tick / max(duration, 1)

        if phase == "ground":
            self.altitude = 0.0
            pressure_mod = 0.0
            temp_mod = 0.0
            flow_mod = 0.0
        elif phase == "climb":
            self.altitude = 35000.0 * progress
            pressure_mod = -5.0 * progress
            temp_mod = -20.0 * progress
            flow_mod = 2.0 * progress
        elif phase == "cruise":
            self.altitude = 35000.0
            pressure_mod = -5.0 + np.random.normal(0, 0.1)
            temp_mod = -20.0 + np.random.normal(0, 0.5)
            flow_mod = 2.0 + np.random.normal(0, 0.2)
        elif phase == "descent":
            self.altitude = 35000.0 * (1.0 - progress)
            pressure_mod = -5.0 * (1.0 - progress)
            temp_mod = -20.0 * (1.0 - progress)
            flow_mod = 2.0 * (1.0 - progress)
        else:
            pressure_mod = 0.0
            temp_mod = 0.0
            flow_mod = 0.0

        self.phase_tick += 1
        if self.phase_tick >= duration:
            self.phase_tick = 0
            self.phase_index = (self.phase_index + 1) % len(self.PHASES)

        return {
            "phase": phase,
            "altitude": self.altitude,
            "pressure_mod": pressure_mod,
            "temp_mod": temp_mod,
            "flow_mod": flow_mod
        }


class SensorSimulator:
    """
    Generates synthetic sensor data for the digital twin.

    Simulates a zirconia oxygen sensor operating in an OBOGS system
    with realistic aging, drift, noise, and environmental effects.
    """

    def __init__(self):
        self.flight_hours = 0.0
        self.thermal_cycles = 0
        self.tick_count = 0
        self.running = False
        self.flight_profile = FlightProfile()

        # State tracking
        self.random_walk_drift = 0.0
        self.previous_pressure = NOMINAL_PRESSURE
        self.voltage_history = []
        self.sensor_temp = SENSOR_OPERATING_TEMP

        # Injected faults
        self.injected_faults = {}

        # Callback for processing each reading
        self.on_reading = None

    def inject_fault(self, fault_type: str, severity: float = 0.5):
        """Inject a fault for testing."""
        self.injected_faults[fault_type] = severity

    def clear_faults(self):
        """Clear all injected faults."""
        self.injected_faults = {}

    def generate_reading(self) -> dict:
        """
        Generate one synthetic sensor reading.

        Returns:
            Dictionary with all sensor values
        """
        self.tick_count += 1

        # Advance flight profile
        flight = self.flight_profile.tick()

        # Advance simulated time
        self.flight_hours += SIMULATION_TIME_ACCELERATION / 3600.0
        if flight["phase"] == "ground" and self.flight_profile.phase_tick == 1:
            self.thermal_cycles += 1

        # ── Base sensor values with environmental effects ────────────
        oxygen = NOMINAL_OXYGEN + np.random.normal(0, 0.3) + flight.get("temp_mod", 0) * 0.01
        temperature = NOMINAL_TEMPERATURE + flight.get("temp_mod", 0) + np.random.normal(0, 1.0)
        pressure = NOMINAL_PRESSURE + flight.get("pressure_mod", 0) + np.random.normal(0, 0.05)
        flow = NOMINAL_FLOW + flight.get("flow_mod", 0) + np.random.normal(0, 0.1)
        humidity = NOMINAL_HUMIDITY + np.random.normal(0, 1.0)
        humidity = max(0, humidity)

        # ── Sensor aging effects ─────────────────────────────────────
        age_fraction = self.flight_hours / 5000.0  # Normalized age

        # Voltage degrades with aging
        voltage_base = NOMINAL_VOLTAGE * (1.0 - 0.15 * age_fraction)

        # Apply drift
        drift = 0.001 * self.flight_hours + 0.05 * np.sin(0.01 * self.flight_hours)
        self.random_walk_drift += np.random.normal(0, 0.0005)
        oxygen -= drift + self.random_walk_drift

        # Apply noise (increases with age)
        noise_sigma = 0.02 * (1.0 + 2.0 * age_fraction)
        oxygen += np.random.normal(0, noise_sigma)

        # Voltage noise
        voltage = voltage_base + np.random.normal(0, 0.005 * (1 + age_fraction))
        current = voltage / 100.0 * (1.0 + np.random.normal(0, 0.01))

        # Sensor heater temperature
        self.sensor_temp = SENSOR_OPERATING_TEMP + np.random.normal(0, 2.0)
        heater_temp = self.sensor_temp * (1.0 - 0.05 * age_fraction)

        # Vibration (higher during flight)
        vibration = 0.1 if flight["phase"] == "ground" else 0.5 + np.random.exponential(0.2)

        # ── Apply injected faults ────────────────────────────────────
        if "heater_failure" in self.injected_faults:
            sev = self.injected_faults["heater_failure"]
            heater_temp *= (1.0 - sev)

        if "pressure_leak" in self.injected_faults:
            sev = self.injected_faults["pressure_leak"]
            pressure -= sev * 5.0

        if "sensor_crack" in self.injected_faults:
            sev = self.injected_faults["sensor_crack"]
            voltage += np.random.normal(0, sev * 0.2)

        if "voltage_drop" in self.injected_faults:
            sev = self.injected_faults["voltage_drop"]
            voltage *= (1.0 - sev * 0.5)

        if "wiring_fault" in self.injected_faults:
            sev = self.injected_faults["wiring_fault"]
            current *= (1.0 - sev * 0.8)

        # ── Clamp to valid ranges ────────────────────────────────────
        oxygen = float(np.clip(oxygen, 0, 100))
        voltage = float(np.clip(voltage, 0, 1.5))
        current = float(np.clip(current, 0, 0.5))
        pressure = float(np.clip(pressure, 10, 50))
        flow = float(np.clip(flow, 0, 30))
        humidity = float(np.clip(humidity, 0, 100))

        # Track history
        self.voltage_history.append(voltage)
        if len(self.voltage_history) > 100:
            self.voltage_history = self.voltage_history[-100:]

        reading = {
            "timestamp": datetime.utcnow().isoformat(),
            "oxygen": round(oxygen, 2),
            "temperature": round(temperature, 2),
            "pressure": round(pressure, 2),
            "flow": round(flow, 2),
            "humidity": round(humidity, 2),
            "voltage": round(voltage, 4),
            "current": round(current, 4),
            "vibration": round(vibration, 3),
            "heater_temp": round(heater_temp, 2),
            "altitude": round(flight["altitude"], 0),
            "flight_hours": round(self.flight_hours, 2),
            "thermal_cycles": self.thermal_cycles,
            "flight_phase": flight["phase"]
        }

        self.previous_pressure = pressure
        return reading

    async def start(self, callback=None):
        """
        Start the simulator as an async background task.

        Args:
            callback: Async function to call with each reading
        """
        self.running = True
        self.on_reading = callback

        while self.running:
            reading = self.generate_reading()

            if self.on_reading:
                await self.on_reading(reading)

            await asyncio.sleep(SIMULATION_INTERVAL)

    def stop(self):
        """Stop the simulator."""
        self.running = False

    def get_status(self) -> dict:
        """Get current simulator status."""
        return {
            "running": self.running,
            "tick_count": self.tick_count,
            "flight_hours": round(self.flight_hours, 2),
            "thermal_cycles": self.thermal_cycles,
            "current_phase": self.flight_profile.get_phase(),
            "injected_faults": list(self.injected_faults.keys()),
            "time_acceleration": SIMULATION_TIME_ACCELERATION
        }


# Module-level singleton
_simulator = None


def get_simulator() -> SensorSimulator:
    """Get or create the singleton simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = SensorSimulator()
    return _simulator
