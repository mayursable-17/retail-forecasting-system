"""
Multi-step Future Demand Forecasting Engine.
Supports recursive auto-regressive multi-step forecasting for ML models
and direct forecasting for statistical baselines.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from src.forecasting.features import FEATURE_COLUMNS


def generate_future_forecast(
    model_result: Dict[str, Any],
    product_id: str,
    horizon_days: int = 15,
    last_date: Optional[datetime.date] = None
) -> pd.DataFrame:
    """
    Generate future demand predictions for a specified horizon.
    
    Parameters:
    - model_result: Dictionary returned from DemandModelTrainer.train_and_evaluate()
    - product_id: Product ID string
    - horizon_days: 7, 15, or 30 days
    - last_date: Date of the last known historical record
    
    Returns:
    - DataFrame with [forecast_date, product_id, predicted_demand, lower_bound, upper_bound]
    """
    model_obj = model_result["model_object"]
    model_type = model_result.get("model_type", "baseline")
    model_name = model_result.get("selected_model_name", "Baseline")
    feat_df = model_result["features_df"].copy()

    if last_date is None:
        last_date = pd.to_datetime(feat_df["sale_date"].iloc[-1]).date()
    else:
        last_date = pd.to_datetime(last_date).date()

    future_dates = [last_date + timedelta(days=i) for i in range(1, horizon_days + 1)]

    # Calculate residual standard deviation from validation set for uncertainty bounds
    val_actuals = np.array(model_result.get("val_actuals", []))
    val_preds = np.array(model_result.get("val_predictions", []))
    if len(val_actuals) > 1 and len(val_preds) > 1:
        residual_std = float(np.std(val_actuals - val_preds))
        if residual_std == 0:
            residual_std = float(np.std(feat_df["quantity_sold"])) if len(feat_df) > 1 else 1.0
    else:
        residual_std = float(np.std(feat_df["quantity_sold"])) if len(feat_df) > 1 else 1.0

    predictions = []

    if model_type == "baseline":
        # Direct forecasting using baseline model method
        preds = model_obj.predict(horizon_days)
        predictions = [max(0.0, float(p)) for p in preds]

    elif model_type == "ml":
        # Recursive multi-step forecasting
        current_history = feat_df[["sale_date", "quantity_sold"]].copy()
        current_history["sale_date"] = pd.to_datetime(current_history["sale_date"])

        for fut_dt in future_dates:
            dt_ts = pd.to_datetime(fut_dt)

            # Build single feature row for dt_ts
            sales_series = current_history["quantity_sold"]

            # Lags
            lag_1 = sales_series.iloc[-1] if len(sales_series) >= 1 else 0.0
            lag_7 = sales_series.iloc[-7] if len(sales_series) >= 7 else lag_1
            lag_14 = sales_series.iloc[-14] if len(sales_series) >= 14 else lag_7
            lag_28 = sales_series.iloc[-28] if len(sales_series) >= 28 else lag_14

            # Rolling stats
            roll_7 = sales_series.iloc[-7:].mean() if len(sales_series) >= 7 else sales_series.mean()
            roll_14 = sales_series.iloc[-14:].mean() if len(sales_series) >= 14 else sales_series.mean()
            roll_28 = sales_series.iloc[-28:].mean() if len(sales_series) >= 28 else sales_series.mean()
            std_7 = sales_series.iloc[-7:].std() if len(sales_series) >= 7 else 0.0
            if pd.isna(std_7):
                std_7 = 0.0

            row_feats = {
                "dayofweek": dt_ts.dayofweek,
                "is_weekend": 1 if dt_ts.dayofweek in [5, 6] else 0,
                "day": dt_ts.day,
                "month": dt_ts.month,
                "weekofyear": int(dt_ts.isocalendar().week),
                "lag_1": lag_1,
                "lag_7": lag_7,
                "lag_14": lag_14,
                "lag_28": lag_28,
                "rolling_mean_7": roll_7,
                "rolling_std_7": std_7,
                "rolling_mean_14": roll_14,
                "rolling_mean_28": roll_28
            }

            feat_vec = np.array([[row_feats[c] for c in FEATURE_COLUMNS]])
            next_pred = float(model_obj.predict(feat_vec)[0])
            next_pred = max(0.0, next_pred)
            predictions.append(next_pred)

            # Append to recursive history
            new_row = pd.DataFrame([{"sale_date": dt_ts, "quantity_sold": next_pred}])
            current_history = pd.concat([current_history, new_row], ignore_index=True)

    # Calculate 90% confidence bounds (z ~ 1.645)
    z = 1.645
    results = []
    for dt, pred in zip(future_dates, predictions):
        lower = max(0.0, round(pred - z * residual_std, 2))
        upper = round(pred + z * residual_std, 2)
        results.append({
            "forecast_date": dt,
            "product_id": str(product_id),
            "predicted_demand": round(pred, 2),
            "lower_bound": lower,
            "upper_bound": upper
        })

    return pd.DataFrame(results)
