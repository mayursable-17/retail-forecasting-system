"""
Statistical and Baseline Forecasting Models.
Provides Naive, Seasonal Naive, Moving Average, and Exponential Smoothing baselines.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd


class NaiveForecaster:
    """Carries the last observed demand value forward."""
    def __init__(self):
        self.last_value: float = 0.0

    def fit(self, series: pd.Series):
        if len(series) > 0:
            self.last_value = max(0.0, float(series.iloc[-1]))
        else:
            self.last_value = 0.0
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, self.last_value, dtype=float)


class SeasonalNaiveForecaster:
    """Repeats the last known seasonal cycle (default 7 days for weekly cycle)."""
    def __init__(self, season_length: int = 7):
        self.season_length = season_length
        self.seasonal_pattern: np.ndarray = np.zeros(season_length)

    def fit(self, series: pd.Series):
        vals = series.values[-self.season_length:]
        if len(vals) < self.season_length:
            # Pad with mean if series is shorter than season_length
            mean_val = float(series.mean()) if len(series) > 0 else 0.0
            pad_needed = self.season_length - len(vals)
            padded = np.concatenate([np.full(pad_needed, mean_val), vals])
            self.seasonal_pattern = np.maximum(padded, 0.0)
        else:
            self.seasonal_pattern = np.maximum(vals, 0.0)
        return self

    def predict(self, horizon: int) -> np.ndarray:
        repeats = int(np.ceil(horizon / self.season_length))
        tiled = np.tile(self.seasonal_pattern, repeats)
        return tiled[:horizon].astype(float)


class MovingAverageForecaster:
    """Forecasts using the unweighted average of the last k periods."""
    def __init__(self, window: int = 7):
        self.window = window
        self.mean_val: float = 0.0

    def fit(self, series: pd.Series):
        if len(series) == 0:
            self.mean_val = 0.0
        else:
            recent = series.iloc[-self.window:]
            self.mean_val = max(0.0, float(recent.mean()))
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, self.mean_val, dtype=float)


class ExponentialSmoothingForecaster:
    """Simple Exponential Smoothing (SES) with smoothing factor alpha."""
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.smoothed_level: float = 0.0

    def fit(self, series: pd.Series):
        if len(series) == 0:
            self.smoothed_level = 0.0
            return self

        level = float(series.iloc[0])
        for val in series.iloc[1:]:
            level = self.alpha * float(val) + (1.0 - self.alpha) * level
        self.smoothed_level = max(0.0, level)
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, self.smoothed_level, dtype=float)


class CrostonIntermittentForecaster:
    """
    Croston's Method for intermittent (slow-moving/sparse) demand.
    Separately estimates demand size when non-zero, and inter-arrival time between demands.
    """
    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha
        self.forecast_rate: float = 0.0

    def fit(self, series: pd.Series):
        vals = series.values
        non_zeros = np.where(vals > 0)[0]
        if len(non_zeros) == 0:
            self.forecast_rate = 0.0
            return self

        # Demand magnitudes and intervals
        magnitudes = vals[non_zeros]
        intervals = np.diff(np.insert(non_zeros, 0, -1))

        z = float(magnitudes[0])
        p = float(intervals[0])

        for mag, interv in zip(magnitudes[1:], intervals[1:]):
            z = self.alpha * float(mag) + (1.0 - self.alpha) * z
            p = self.alpha * float(interv) + (1.0 - self.alpha) * p

        self.forecast_rate = max(0.0, z / p) if p > 0 else 0.0
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, self.forecast_rate, dtype=float)
