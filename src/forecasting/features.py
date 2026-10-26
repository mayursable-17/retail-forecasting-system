"""
Feature Engineering for Time Series Demand Forecasting.
Constructs lagged, rolling, and calendar features strictly without data leakage.
"""

from typing import List, Tuple
import pandas as pd
import numpy as np


def create_time_series_features(
    df_product_daily: pd.DataFrame,
    target_col: str = "quantity_sold",
    date_col: str = "sale_date"
) -> pd.DataFrame:
    """
    Construct strictly causal, non-leaking features for a single product time series.
    
    Parameters:
    - df_product_daily: DataFrame containing at least [date_col, target_col], sorted by date.
    
    Returns:
    - DataFrame with engineered feature columns and original target.
    """
    df = df_product_daily.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=date_col).reset_index(drop=True)

    # 1. Calendar Features (derived purely from the timestamp)
    df["dayofweek"] = df[date_col].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["day"] = df[date_col].dt.day
    df["month"] = df[date_col].dt.month
    df["weekofyear"] = df[date_col].dt.isocalendar().week.astype(int)

    # 2. Lag Features (strictly from past days)
    # lag_1 = yesterday's sales
    # lag_7 = sales exactly 1 week ago
    # lag_14 = sales 2 weeks ago
    # lag_28 = sales 4 weeks ago
    for lag in [1, 7, 14, 28]:
        df[f"lag_{lag}"] = df[target_col].shift(lag)

    # 3. Rolling Window Features (strictly shifted by 1 so today's target is excluded)
    shifted_target = df[target_col].shift(1)
    df["rolling_mean_7"] = shifted_target.rolling(window=7, min_periods=1).mean()
    df["rolling_std_7"] = shifted_target.rolling(window=7, min_periods=1).std().fillna(0.0)
    df["rolling_mean_14"] = shifted_target.rolling(window=14, min_periods=1).mean()
    df["rolling_mean_28"] = shifted_target.rolling(window=28, min_periods=1).mean()

    # Fill NaNs for early periods where lag_28 etc. don't yet exist
    # Use expanding mean of past values or 0
    expanding_mean = shifted_target.expanding(min_periods=1).mean().fillna(0.0)
    for col in ["lag_1", "lag_7", "lag_14", "lag_28"]:
        df[col] = df[col].fillna(expanding_mean)

    df["rolling_mean_7"] = df["rolling_mean_7"].fillna(expanding_mean)
    df["rolling_mean_14"] = df["rolling_mean_14"].fillna(expanding_mean)
    df["rolling_mean_28"] = df["rolling_mean_28"].fillna(expanding_mean)
    df["rolling_std_7"] = df["rolling_std_7"].fillna(0.0)

    return df


FEATURE_COLUMNS = [
    "dayofweek", "is_weekend", "day", "month", "weekofyear",
    "lag_1", "lag_7", "lag_14", "lag_28",
    "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "rolling_mean_28"
]
