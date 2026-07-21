"""
Calculations Pipeline — Model Orchestrator (Synchronous).

Chains all models in sequence. No async needed.
"""

from app.models.physics import calculate_physics
from app.models.thermal import calculate_thermal
from app.models.sensor_model import calculate_sensor_model
from app.models.aging import calculate_aging
from app.models.drift import calculate_drift
from app.models.noise import calculate_noise
from app.models.fault import calculate_fault
from app.models.state_estimation import calculate_state_estimation
from app.models.health import calculate_health
from app.models.rul import calculate_rul
from app.models.prediction import calculate_prediction


class DigitalTwinPipeline:
    def __init__(self):
        self.sensor_history = []
        self.health_history = []
        self.health_time_points = []
        self.voltage_history = []
        self.previous_pressure = None
        self.random_walk_state = 0.0
        self.previous_output = None
        self.tick_count = 0

    def process_reading(self, sensor_data: dict) -> dict:
        self.tick_count += 1

        self.voltage_history.append(sensor_data.get("voltage", 0.82))
        if len(self.voltage_history) > 100:
            self.voltage_history = self.voltage_history[-100:]

        physics      = calculate_physics(sensor_data)
        heater_temp  = sensor_data.get("heater_temp", 700.0)
        thermal      = calculate_thermal(sensor_data, current_sensor_temp=heater_temp)
        aging        = calculate_aging(sensor_data)
        sensor_model = calculate_sensor_model(
            sensor_data,
            aging_factor=aging["aging_factor"],
            current_output=self.previous_output
        )
        self.previous_output = sensor_model.get("lagged_voltage")

        drift = calculate_drift(sensor_data, self.random_walk_state)
        self.random_walk_state = drift.get("random_walk_state", 0.0)

        noise = calculate_noise(
            aging_factor=aging["aging_factor"],
            signal_level=sensor_data.get("voltage", 0.82)
        )
        state = calculate_state_estimation(sensor_data)
        fault = calculate_fault(
            sensor_data,
            ideal_voltage=physics["ideal_voltage"],
            previous_pressure=self.previous_pressure,
            voltage_history=self.voltage_history
        )
        self.previous_pressure = sensor_data.get("pressure", 29.0)

        health = calculate_health(
            drift=abs(drift.get("total_drift", 0.0)),
            noise_rms=noise.get("noise_rms", 0.0),
            fault_probability=fault.get("fault_probability", 0.0),
            sensitivity=aging.get("sensitivity", 1.0),
            aging_factor=aging.get("aging_factor", 0.0),
            health_history=self.health_history
        )

        self.health_history.append(health["health_score"])
        self.health_time_points.append(sensor_data.get("flight_hours", 0.0))
        if len(self.health_history) > 500:
            self.health_history = self.health_history[-500:]
            self.health_time_points = self.health_time_points[-500:]

        self.sensor_history.append(sensor_data)
        if len(self.sensor_history) > 200:
            self.sensor_history = self.sensor_history[-200:]

        rul = calculate_rul(
            current_health=health["health_score"],
            flight_hours=sensor_data.get("flight_hours", 0.0),
            health_history=self.health_history if len(self.health_history) >= 3 else None,
            time_points=self.health_time_points if len(self.health_time_points) >= 3 else None
        )

        prediction = None
        if self.tick_count % 10 == 0 and len(self.sensor_history) >= 10:
            prediction = calculate_prediction(
                sensor_history=self.sensor_history[-50:],
                health_history=self.health_history[-50:],
                n_future=10
            )

        return {
            "sensor_data":    sensor_data,
            "physics":        physics,
            "thermal":        thermal,
            "aging":          aging,
            "sensor_model":   sensor_model,
            "drift":          drift,
            "noise":          noise,
            "state_estimation": state,
            "fault":          fault,
            "health":         health,
            "rul":            rul,
            "prediction":     prediction,
            "tick":           self.tick_count,
        }

    def get_summary(self) -> dict:
        return {
            "tick_count":    self.tick_count,
            "data_points":   len(self.sensor_history),
            "health_points": len(self.health_history),
            "latest_health": self.health_history[-1] if self.health_history else None,
            "health_trend":  "stable" if len(self.health_history) < 2 else
                             ("degrading" if self.health_history[-1] < self.health_history[-2]
                              else "stable"),
        }


_pipeline = None

def get_pipeline() -> DigitalTwinPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = DigitalTwinPipeline()
    return _pipeline
