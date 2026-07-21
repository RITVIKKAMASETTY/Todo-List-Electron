"""
State Estimation — Extended Kalman Filter for True Oxygen Estimation.

Fuses noisy sensor measurements with physics model predictions
to estimate the true system state.

State vector: x = [O2_true, T_sensor, drift, sensitivity]

The EKF provides:
    - Best estimate of true oxygen concentration
    - Confidence intervals on estimates
    - Residual monitoring for fault detection
"""

import numpy as np
from app.config import KALMAN_PROCESS_NOISE, KALMAN_MEASUREMENT_NOISE


class ExtendedKalmanFilter:
    """
    Extended Kalman Filter for oxygen sensor state estimation.

    State: [O2_true, T_sensor, drift, sensitivity]
    Measurement: [measured_O2, measured_temp]
    """

    def __init__(self):
        # State vector: [O2_true, T_sensor, drift, sensitivity]
        self.x = np.array([93.0, 700.0, 0.0, 1.0])

        # State covariance matrix
        self.P = np.eye(4) * np.array([1.0, 10.0, 0.01, 0.01])

        # Process noise covariance
        self.Q = np.eye(4) * np.array([
            KALMAN_PROCESS_NOISE,       # O2 process noise
            KALMAN_PROCESS_NOISE * 5,   # Temperature process noise
            KALMAN_PROCESS_NOISE * 0.1, # Drift process noise
            KALMAN_PROCESS_NOISE * 0.01 # Sensitivity process noise
        ])

        # Measurement noise covariance
        self.R = np.eye(2) * np.array([
            KALMAN_MEASUREMENT_NOISE,       # O2 measurement noise
            KALMAN_MEASUREMENT_NOISE * 2    # Temperature measurement noise
        ])

        # Measurement matrix (maps state to measurements)
        # measured_O2 = O2_true × sensitivity + drift
        # measured_temp = T_sensor
        self.H = np.array([
            [1.0, 0.0, 1.0, 0.0],  # O2_measured = O2_true + drift (simplified)
            [0.0, 1.0, 0.0, 0.0]   # T_measured = T_sensor
        ])

    def predict(self, dt: float = 1.0):
        """
        Prediction step: propagate state forward.

        State transition model:
            O2_true(t+1) = O2_true(t)  (assumed slowly varying)
            T_sensor(t+1) = T_sensor(t) (thermal model handles this)
            drift(t+1) = drift(t) + small increase
            sensitivity(t+1) = sensitivity(t) - small decrease

        Args:
            dt: Time step (seconds)
        """
        # State transition matrix (near-identity for slow dynamics)
        F = np.eye(4)
        F[2, 2] = 1.0 + 1e-6 * dt   # Drift slowly increases
        F[3, 3] = 1.0 - 1e-7 * dt   # Sensitivity slowly decreases

        # Predict state
        self.x = F @ self.x

        # Predict covariance
        self.P = F @ self.P @ F.T + self.Q * dt

    def update(self, measurement: np.ndarray):
        """
        Update step: incorporate new measurement.

        Args:
            measurement: [measured_O2, measured_temp]
        """
        # Innovation (measurement residual)
        z = measurement
        y = z - self.H @ self.x

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update state
        self.x = self.x + K @ y

        # Update covariance
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P

        # Ensure sensitivity stays in bounds
        self.x[3] = np.clip(self.x[3], 0.1, 1.5)
        # Ensure O2 stays in bounds
        self.x[0] = np.clip(self.x[0], 0.0, 100.0)

    def get_state(self) -> dict:
        """
        Get the current state estimate with uncertainties.

        Returns:
            Dictionary with estimated state and confidence
        """
        # Standard deviations from covariance diagonal
        std = np.sqrt(np.diag(self.P))

        return {
            "estimated_oxygen": round(float(self.x[0]), 2),
            "estimated_temperature": round(float(self.x[1]), 2),
            "estimated_drift": round(float(self.x[2]), 4),
            "estimated_sensitivity": round(float(self.x[3]), 4),
            "oxygen_uncertainty": round(float(std[0]), 4),
            "temperature_uncertainty": round(float(std[1]), 4),
            "drift_uncertainty": round(float(std[2]), 4),
            "sensitivity_uncertainty": round(float(std[3]), 4),
            "confidence": round(float(1.0 - np.mean(std[:2]) / 10.0), 4)
        }

    def step(self, measured_o2: float, measured_temp: float,
             dt: float = 1.0) -> dict:
        """
        Run one complete predict-update cycle.

        Args:
            measured_o2: Measured oxygen concentration (%)
            measured_temp: Measured temperature (°C)
            dt: Time step (seconds)

        Returns:
            Dictionary with state estimates
        """
        self.predict(dt)
        self.update(np.array([measured_o2, measured_temp]))
        return self.get_state()


# Module-level instance for persistent state across API calls
_ekf_instance = None


def get_ekf() -> ExtendedKalmanFilter:
    """Get or create the singleton EKF instance."""
    global _ekf_instance
    if _ekf_instance is None:
        _ekf_instance = ExtendedKalmanFilter()
    return _ekf_instance


def reset_ekf():
    """Reset the EKF to initial state."""
    global _ekf_instance
    _ekf_instance = ExtendedKalmanFilter()


def calculate_state_estimation(sensor_data: dict) -> dict:
    """
    Run state estimation on a sensor reading.

    Args:
        sensor_data: Dictionary with oxygen, temperature readings

    Returns:
        Dictionary with estimated true state
    """
    ekf = get_ekf()
    measured_o2 = sensor_data.get("oxygen", 93.0)
    measured_temp = sensor_data.get("heater_temp", 700.0)

    result = ekf.step(measured_o2, measured_temp)
    return result
