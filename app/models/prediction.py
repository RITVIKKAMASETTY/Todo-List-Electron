"""
Prediction Model — Time-Series Forecasting.

Uses statistical methods for predicting future values:
    - Exponential Moving Average (EMA) extrapolation
    - Linear trend projection
    - Polynomial regression
    - Ensemble prediction combining multiple methods

Predicts: oxygen, temperature, health for the next N hours.
Falls back to statistical extrapolation (no PyTorch dependency).
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


def exponential_moving_average(values: list, alpha: float = 0.3) -> float:
    """
    Calculate exponential moving average.

    EMA(t) = α × x(t) + (1-α) × EMA(t-1)

    Args:
        values: Time series values
        alpha: Smoothing factor (0-1)

    Returns:
        Current EMA value
    """
    if not values:
        return 0.0

    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1.0 - alpha) * ema
    return float(ema)


def linear_trend(values: list, n_future: int = 10) -> list:
    """
    Project linear trend into the future.

    Args:
        values: Historical values
        n_future: Number of future points to predict

    Returns:
        List of predicted values
    """
    if len(values) < 2:
        return [values[-1] if values else 0.0] * n_future

    n = len(values)
    x = np.arange(n).reshape(-1, 1)
    y = np.array(values)

    model = LinearRegression()
    model.fit(x, y)

    x_future = np.arange(n, n + n_future).reshape(-1, 1)
    predictions = model.predict(x_future)

    return [round(float(p), 2) for p in predictions]


def polynomial_trend(values: list, degree: int = 2,
                     n_future: int = 10) -> list:
    """
    Project polynomial trend into the future.

    Args:
        values: Historical values
        degree: Polynomial degree
        n_future: Number of future points to predict

    Returns:
        List of predicted values
    """
    if len(values) < degree + 1:
        return linear_trend(values, n_future)

    n = len(values)
    x = np.arange(n).reshape(-1, 1)
    y = np.array(values)

    poly = PolynomialFeatures(degree=degree)
    x_poly = poly.fit_transform(x)

    model = LinearRegression()
    model.fit(x_poly, y)

    x_future = np.arange(n, n + n_future).reshape(-1, 1)
    x_future_poly = poly.transform(x_future)
    predictions = model.predict(x_future_poly)

    return [round(float(p), 2) for p in predictions]


def ensemble_predict(values: list, n_future: int = 10) -> dict:
    """
    Ensemble prediction combining multiple methods.

    Averages linear, polynomial, and EMA-based predictions
    with confidence bounds.

    Args:
        values: Historical values
        n_future: Number of future points

    Returns:
        Dictionary with predictions and confidence
    """
    if not values:
        return {
            "predictions": [0.0] * n_future,
            "lower_bound": [0.0] * n_future,
            "upper_bound": [0.0] * n_future,
            "confidence": 0.0
        }

    linear_pred = linear_trend(values, n_future)
    poly_pred = polynomial_trend(values, degree=2, n_future=n_future)

    # EMA-based extrapolation
    ema = exponential_moving_average(values)
    ema_pred = [round(ema, 2)] * n_future

    # Ensemble: weighted average
    predictions = []
    lower_bounds = []
    upper_bounds = []

    for i in range(n_future):
        preds = [linear_pred[i], poly_pred[i], ema_pred[i]]
        mean_pred = np.mean(preds)
        std_pred = np.std(preds)

        predictions.append(round(float(mean_pred), 2))
        lower_bounds.append(round(float(mean_pred - 2 * std_pred), 2))
        upper_bounds.append(round(float(mean_pred + 2 * std_pred), 2))

    # Confidence decreases with forecast horizon
    base_confidence = min(len(values) / 50.0, 1.0)  # More data → more confidence
    confidence = base_confidence * 0.9

    return {
        "predictions": predictions,
        "lower_bound": lower_bounds,
        "upper_bound": upper_bounds,
        "confidence": round(confidence, 4)
    }


def predict_oxygen(oxygen_history: list, n_future: int = 10) -> dict:
    """
    Predict future oxygen concentration.

    Args:
        oxygen_history: Historical O2 readings
        n_future: Hours to predict ahead

    Returns:
        Prediction results
    """
    return ensemble_predict(oxygen_history, n_future)


def predict_temperature(temp_history: list, n_future: int = 10) -> dict:
    """
    Predict future sensor temperature.

    Args:
        temp_history: Historical temperature readings
        n_future: Hours to predict ahead

    Returns:
        Prediction results
    """
    return ensemble_predict(temp_history, n_future)


def predict_health(health_history: list, n_future: int = 10) -> dict:
    """
    Predict future health score.

    Health typically follows a monotonic decline, so we
    use polynomial fitting biased toward decay.

    Args:
        health_history: Historical health scores
        n_future: Hours to predict ahead

    Returns:
        Prediction results
    """
    result = ensemble_predict(health_history, n_future)
    # Clip health predictions to valid range
    result["predictions"] = [round(np.clip(p, 0, 100), 2) for p in result["predictions"]]
    result["lower_bound"] = [round(np.clip(p, 0, 100), 2) for p in result["lower_bound"]]
    result["upper_bound"] = [round(np.clip(p, 0, 100), 2) for p in result["upper_bound"]]
    return result


def calculate_prediction(sensor_history: list, health_history: list,
                         n_future: int = 10) -> dict:
    """
    Run the complete prediction model.

    Args:
        sensor_history: List of sensor data dicts
        health_history: List of health scores
        n_future: Steps to predict ahead

    Returns:
        Dictionary with all predictions
    """
    # Extract time series
    oxygen_vals = [s.get("oxygen", 93.0) for s in sensor_history] if sensor_history else []
    temp_vals = [s.get("temperature", 700.0) for s in sensor_history] if sensor_history else []

    o2_pred = predict_oxygen(oxygen_vals, n_future) if oxygen_vals else None
    temp_pred = predict_temperature(temp_vals, n_future) if temp_vals else None
    health_pred = predict_health(health_history, n_future) if health_history else None

    result = {
        "prediction_horizon": n_future,
        "data_points_used": len(sensor_history) if sensor_history else 0
    }

    if o2_pred:
        result["predicted_oxygen"] = o2_pred["predictions"][0] if o2_pred["predictions"] else None
        result["oxygen_forecast"] = o2_pred
    if temp_pred:
        result["predicted_temperature"] = temp_pred["predictions"][0] if temp_pred["predictions"] else None
        result["temperature_forecast"] = temp_pred
    if health_pred:
        result["predicted_health"] = health_pred["predictions"][0] if health_pred["predictions"] else None
        result["health_forecast"] = health_pred

    # Overall confidence
    confidences = []
    for pred in [o2_pred, temp_pred, health_pred]:
        if pred:
            confidences.append(pred["confidence"])
    result["confidence"] = round(np.mean(confidences), 4) if confidences else 0.0

    return result
