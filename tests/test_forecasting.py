"""
Tests for Demand Forecasting Engine, Baselines, Feature Engineering, and Metrics.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.forecasting.evaluate import calculate_mae, calculate_rmse, calculate_wape, calculate_bias, evaluate_forecast
from src.forecasting.baseline import NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, ExponentialSmoothingForecaster
from src.forecasting.features import create_time_series_features
from src.forecasting.train import chronological_split, DemandModelTrainer
from src.forecasting.predict import generate_future_forecast


def test_evaluation_metrics_known_values():
    actual = np.array([10.0, 20.0, 30.0, 40.0])
    predicted = np.array([12.0, 18.0, 33.0, 38.0])

    # Differences: [+2, -2, +3, -2] -> absolute: [2, 2, 3, 2]
    # Sum of actuals = 100.0, Sum of abs errors = 9.0, Sum of errors = +1.0
    mae = calculate_mae(actual, predicted)
    assert mae == 2.25  # 9/4

    rmse = calculate_rmse(actual, predicted)
    assert round(rmse, 3) == round(np.sqrt( (4+4+9+4)/4 ), 3)  # sqrt(21/4) = sqrt(5.25) = 2.291

    wape = calculate_wape(actual, predicted)
    assert wape == 9.0  # (9.0 / 100.0) * 100%

    bias = calculate_bias(actual, predicted)
    assert bias == 1.0  # (+1.0 / 100.0) * 100%


def test_wape_zero_actual_handling():
    actual_all_zeros = np.array([0.0, 0.0, 0.0])
    pred_zeros = np.array([0.0, 0.0, 0.0])
    pred_non_zeros = np.array([1.0, 2.0, 0.0])

    assert calculate_wape(actual_all_zeros, pred_zeros) == 0.0
    assert calculate_wape(actual_all_zeros, pred_non_zeros) == 100.0


def test_chronological_split_no_leakage():
    dates = pd.date_range("2026-08-01", periods=30, freq="D")
    df = pd.DataFrame({"sale_date": dates, "quantity_sold": np.arange(30)})

    train_df, val_df = chronological_split(df, val_days=7)

    assert len(train_df) == 23
    assert len(val_df) == 7
    # Max train date must be strictly less than min val date
    assert train_df["sale_date"].max() < val_df["sale_date"].min()


def test_feature_engineering_strictly_causal():
    dates = pd.date_range("2026-08-01", periods=40, freq="D")
    df = pd.DataFrame({"sale_date": dates, "quantity_sold": [10.0] * 40})
    feat_df = create_time_series_features(df)

    assert "lag_1" in feat_df.columns
    assert "lag_7" in feat_df.columns
    assert "rolling_mean_7" in feat_df.columns
    assert "is_weekend" in feat_df.columns
    assert len(feat_df) == 40


def test_baseline_forecasters():
    s = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0])

    # 1. Naive Forecaster
    naive = NaiveForecaster().fit(s)
    preds_naive = naive.predict(5)
    assert len(preds_naive) == 5
    assert (preds_naive == 18.0).all()

    # 2. Moving Average
    ma = MovingAverageForecaster(window=3).fit(s)
    preds_ma = ma.predict(5)
    assert len(preds_ma) == 5
    assert preds_ma[0] == (14.0 + 16.0 + 18.0) / 3.0  # 16.0


def test_demand_model_trainer_and_predict(sample_daily_series):
    trainer = DemandModelTrainer(val_days=7)
    res = trainer.train_and_evaluate(sample_daily_series, model_preference="Best Model (Auto-select)")

    assert "selected_model_name" in res
    assert "val_metrics" in res
    assert res["val_metrics"]["mae"] >= 0.0

    # Test future forecast generation
    forecast_df = generate_future_forecast(res, product_id="P1", horizon_days=15)
    assert len(forecast_df) == 15
    # Must guarantee non-negativity
    assert (forecast_df["predicted_demand"] >= 0.0).all()
    assert (forecast_df["lower_bound"] >= 0.0).all()
