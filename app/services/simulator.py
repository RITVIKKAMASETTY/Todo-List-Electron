"""
Sensor Simulator — Synthetic Data Generator (Threading version for Flask).

Uses Python's built-in threading instead of asyncio.
No external dependencies needed.
"""

import threading
import time
import numpy as np
from datetime import datetime
from app.config import (
    NOMINAL_OXYGEN, NOMINAL_TEMPERATURE, NOMINAL_PRESSURE,
    NOMINAL_FLOW, NOMINAL_HUMIDITY, NOMINAL_VOLTAGE,
    SIMULATION_INTERVAL, SIMULATION_TIME_ACCELERATION,
    SENSOR_OPERATING_TEMP
)


class FlightProfile:
    """Simulates aircraft flight phases."""

    PHASES = ["ground", "climb", "cruise", "descent", "ground"]
    PHASE_DURATIONS = [60, 120, 600, 120, 60]  # ticks per phase

    def __init__(self):
        self.phase_index = 0
        self.phase_tick = 0
        self.altitude = 0.0

    def get_phase(self):
        return self.PHASES[self.phase_index]

    def tick(self):
        phase = self.get_phase()
        duration = self.PHASE_DURATIONS[self.phase_index]
        progress = self.phase_tick / max(duration, 1)

        if phase == "ground":
            self.altitude = 0.0
            mods = dict(pressure=0.0, temp=0.0, flow=0.0)
        elif phase == "climb":
            self.altitude = 35000.0 * progress
            mods = dict(pressure=-5.0 * progress, temp=-20.0 * progress, flow=2.0 * progress)
        elif phase == "cruise":
            self.altitude = 35000.0
            mods = dict(
                pressure=-5.0 + np.random.normal(0, 0.1),
                temp=-20.0 + np.random.normal(0, 0.5),
                flow=2.0 + np.random.normal(0, 0.2)
            )
        elif phase == "descent":
            self.altitude = 35000.0 * (1.0 - progress)
            mods = dict(
                pressure=-5.0 * (1.0 - progress),
                temp=-20.0 * (1.0 - progress),
                flow=2.0 * (1.0 - progress)
            )
        else:
            mods = dict(pressure=0.0, temp=0.0, flow=0.0)

        self.phase_tick += 1
        if self.phase_tick >= duration:
            self.phase_tick = 0
            self.phase_index = (self.phase_index + 1) % len(self.PHASES)

        return {"phase": phase, "altitude": self.altitude, **mods}


class SensorSimulator:
    """
    Synthetic sensor data generator using a background thread.

    Call start(callback) to begin. The callback receives each reading dict.
    Call stop() to shut down.
    """

    def __init__(self):
        self.flight_hours = 0.0
        self.thermal_cycles = 0
        self.tick_count = 0
        self.running = False
        self.flight_profile = FlightProfile()

        self.random_walk_drift = 0.0
        self.previous_pressure = NOMINAL_PRESSURE
        self.voltage_history = []
        self.sensor_temp = SENSOR_OPERATING_TEMP
        self.injected_faults = {}

        self._thread = None
        self._stop_event = threading.Event()
        self.on_reading = None

    def inject_fault(self, fault_type: str, severity: float = 0.5):
        self.injected_faults[fault_type] = severity

    def clear_faults(self):
        self.injected_faults = {}

    def generate_reading(self) -> dict:
        self.tick_count += 1
        flight = self.flight_profile.tick()

        # Advance simulated time
        self.flight_hours += SIMULATION_TIME_ACCELERATION / 3600.0
        if flight["phase"] == "ground" and self.flight_profile.phase_tick == 1:
            self.thermal_cycles += 1

        age_fraction = self.flight_hours / 5000.0

        oxygen = NOMINAL_OXYGEN + np.random.normal(0, 0.3) + flight.get("temp", 0) * 0.01
        temperature = NOMINAL_TEMPERATURE + flight.get("temp", 0) + np.random.normal(0, 1.0)
        pressure = NOMINAL_PRESSURE + flight.get("pressure", 0) + np.random.normal(0, 0.05)
        flow = NOMINAL_FLOW + flight.get("flow", 0) + np.random.normal(0, 0.1)
        humidity = max(0.0, NOMINAL_HUMIDITY + np.random.normal(0, 1.0))

        voltage_base = NOMINAL_VOLTAGE * (1.0 - 0.15 * age_fraction)

        drift = 0.001 * self.flight_hours + 0.05 * np.sin(0.01 * self.flight_hours)
        self.random_walk_drift += np.random.normal(0, 0.0005)
        oxygen -= drift + self.random_walk_drift

        noise_sigma = 0.02 * (1.0 + 2.0 * age_fraction)
        oxygen += np.random.normal(0, noise_sigma)

        voltage = voltage_base + np.random.normal(0, 0.005 * (1 + age_fraction))
        current = voltage / 100.0 * (1.0 + np.random.normal(0, 0.01))

        self.sensor_temp = SENSOR_OPERATING_TEMP + np.random.normal(0, 2.0)
        heater_temp = self.sensor_temp * (1.0 - 0.05 * age_fraction)

        vibration = 0.1 if flight["phase"] == "ground" else 0.5 + np.random.exponential(0.2)

        # Apply injected faults
        if "heater_failure" in self.injected_faults:
            heater_temp *= (1.0 - self.injected_faults["heater_failure"])
        if "pressure_leak" in self.injected_faults:
            pressure -= self.injected_faults["pressure_leak"] * 5.0
        if "sensor_crack" in self.injected_faults:
            voltage += np.random.normal(0, self.injected_faults["sensor_crack"] * 0.2)
        if "voltage_drop" in self.injected_faults:
            voltage *= (1.0 - self.injected_faults["voltage_drop"] * 0.5)
        if "wiring_fault" in self.injected_faults:
            current *= (1.0 - self.injected_faults["wiring_fault"] * 0.8)

        oxygen   = float(np.clip(oxygen, 0, 100))
        voltage  = float(np.clip(voltage, 0, 1.5))
        current  = float(np.clip(current, 0, 0.5))
        pressure = float(np.clip(pressure, 10, 50))
        flow     = float(np.clip(flow, 0, 30))
        humidity = float(np.clip(humidity, 0, 100))

        self.voltage_history.append(voltage)
        if len(self.voltage_history) > 100:
            self.voltage_history = self.voltage_history[-100:]

        reading = {
            "timestamp": datetime.utcnow().isoformat(),
            "oxygen":         round(oxygen, 2),
            "temperature":    round(temperature, 2),
            "pressure":       round(pressure, 2),
            "flow":           round(flow, 2),
            "humidity":       round(humidity, 2),
            "voltage":        round(voltage, 4),
            "current":        round(current, 4),
            "vibration":      round(vibration, 3),
            "heater_temp":    round(heater_temp, 2),
            "altitude":       round(flight["altitude"], 0),
            "flight_hours":   round(self.flight_hours, 2),
            "thermal_cycles": self.thermal_cycles,
            "flight_phase":   flight["phase"],
        }

        self.previous_pressure = pressure
        return reading

    def _run_loop(self):
        """Background thread loop."""
        while not self._stop_event.is_set():
            reading = self.generate_reading()
            if self.on_reading:
                try:
                    self.on_reading(reading)
                except Exception as e:
                    print(f"[Simulator] Callback error: {e}")
            self._stop_event.wait(SIMULATION_INTERVAL)

    def start(self, callback=None):
        """Start simulator in a daemon background thread."""
        self.on_reading = callback
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the simulator."""
        self.running = False
        self._stop_event.set()

    def get_status(self) -> dict:
        return {
            "running":        self.running,
            "tick_count":     self.tick_count,
            "flight_hours":   round(self.flight_hours, 2),
            "thermal_cycles": self.thermal_cycles,
            "current_phase":  self.flight_profile.get_phase(),
            "injected_faults": list(self.injected_faults.keys()),
            "time_acceleration": SIMULATION_TIME_ACCELERATION,
        }


_simulator = None

def get_simulator() -> SensorSimulator:
    global _simulator
    if _simulator is None:
        _simulator = SensorSimulator()
    return _simulator
