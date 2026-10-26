"""
Forecast Evaluation Metrics.
Calculates MAE, RMSE, WAPE (Weighted Absolute Percentage Error), and Forecast Bias.
Safely handles zero-actual demand values.
"""

from typing import Dict, Any, Union
import numpy as np
import pandas as pd


def calculate_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error: (1/n) * sum(|y - y_hat|)"""
    if len(actual) == 0:
        return 0.0
    return float(np.mean(np.abs(actual - predicted)))


def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error: sqrt((1/n) * sum((y - y_hat)^2))"""
    if len(actual) == 0:
        return 0.0
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def calculate_wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Weighted Absolute Percentage Error (WAPE):
    (sum(|actual - predicted|) / sum(actual)) * 100%
    Robust against intermittent zeros that break standard MAPE.
    """
    sum_actual = float(np.sum(actual))
    if sum_actual == 0.0:
        # If actual demand was all zero, return 0.0 if predictions were also 0, else 100.0
        sum_pred = float(np.sum(predicted))
        return 0.0 if sum_pred == 0.0 else 100.0
    sum_abs_err = float(np.sum(np.abs(actual - predicted)))
    return (sum_abs_err / sum_actual) * 100.0


def calculate_bias(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Forecast Bias Percentage:
    (sum(predicted - actual) / sum(actual)) * 100%
    Positive value indicates over-forecasting, negative indicates under-forecasting.
    """
    sum_actual = float(np.sum(actual))
    if sum_actual == 0.0:
        return 0.0
    sum_diff = float(np.sum(predicted - actual))
    return (sum_diff / sum_actual) * 100.0


def evaluate_forecast(
    actual: Union[pd.Series, np.ndarray, list],
    predicted: Union[pd.Series, np.ndarray, list]
) -> Dict[str, float]:
    """
    Compute comprehensive evaluation suite.
    
    Returns:
    - dict with keys: mae, rmse, wape_pct, bias_pct, count
    """
    act = np.asarray(actual, dtype=float)
    pred = np.asarray(predicted, dtype=float)

    if len(act) != len(pred):
        raise ValueError(f"Actual ({len(act)}) and predicted ({len(pred)}) lengths do not match.")

    # Remove any NaN pairs
    valid_mask = ~np.isnan(act) & ~np.isnan(pred)
    act = act[valid_mask]
    pred = pred[valid_mask]

    # Non-negative physical constraint
    pred = np.maximum(pred, 0.0)

    if len(act) == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "wape_pct": 0.0,
            "bias_pct": 0.0,
            "count": 0
        }

    return {
        "mae": round(calculate_mae(act, pred), 3),
        "rmse": round(calculate_rmse(act, pred), 3),
        "wape_pct": round(calculate_wape(act, pred), 2),
        "bias_pct": round(calculate_bias(act, pred), 2),
        "count": int(len(act))
    }
