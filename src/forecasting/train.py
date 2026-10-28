"""
Model Training and Chronological Validation Pipeline.
Implements out-of-sample evaluation, baseline comparisons, and automatic best-model selection.
"""

from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from src.forecasting.baseline import (
    NaiveForecaster, SeasonalNaiveForecaster,
    MovingAverageForecaster, ExponentialSmoothingForecaster, CrostonIntermittentForecaster
)
from src.forecasting.features import create_time_series_features, FEATURE_COLUMNS
from src.forecasting.evaluate import evaluate_forecast


class NumpyRidgeRegressor:
    """
    Lightweight, robust L2-regularized Ridge Autoregressive Regressor implemented in pure NumPy.
    Zero external ML dependencies required; fits in milliseconds and guarantees non-negative predictions.
    """
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.weights = None
        self.bias = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n, p = X.shape
        X_b = np.column_stack([np.ones(n), X])
        reg = self.alpha * np.eye(p + 1)
        reg[0, 0] = 0.0
        try:
            w = np.linalg.solve(X_b.T @ X_b + reg, X_b.T @ y)
        except np.linalg.LinAlgError:
            w, _, _, _ = np.linalg.lstsq(X_b, y, rcond=None)
        self.bias = float(w[0])
        self.weights = w[1:]
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        preds = self.bias + X @ self.weights
        return np.maximum(preds, 0.0)


def chronological_split(
    df: pd.DataFrame,
    val_days: int = 14,
    date_col: str = "sale_date"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split time series strictly chronologically into train and validation sets.
    Never shuffles data.
    """
    df_sorted = df.sort_values(by=date_col).reset_index(drop=True)
    n = len(df_sorted)

    if n <= val_days + 3:
        # If very few points, use at least 3 points for validation if n >= 7
        actual_val_days = max(1, min(val_days, int(n * 0.2)))
    else:
        actual_val_days = val_days

    split_idx = n - actual_val_days
    train_df = df_sorted.iloc[:split_idx].copy()
    val_df = df_sorted.iloc[split_idx:].copy()

    return train_df, val_df


class DemandModelTrainer:
    """Trains and compares forecasting models for a product time series."""

    def __init__(self, val_days: int = 14):
        self.val_days = val_days

    def train_and_evaluate(
        self,
        df_product_daily: pd.DataFrame,
        model_preference: str = "Best Model (Auto-select)",
        target_col: str = "quantity_sold"
    ) -> Dict[str, Any]:
        """
        Train models with chronological out-of-sample validation.
        
        Returns:
        - dict with {
            'selected_model_name': str,
            'model_object': fitted model or forecaster,
            'features_df': pd.DataFrame,
            'train_metrics': dict,
            'val_metrics': dict,
            'val_actuals': list,
            'val_predictions': list,
            'val_dates': list,
            'candidate_evaluations': dict,
            'data_notes': str
          }
        """
        n_obs = len(df_product_daily)
        non_zero_days = (df_product_daily[target_col] > 0).sum()

        data_notes = []

        # Sparse or insufficient data handling
        if n_obs < 10 or non_zero_days < 3:
            data_notes.append("Limited historical observations; using Moving Average fallback.")
            forecaster = MovingAverageForecaster(window=min(7, max(1, n_obs)))
            forecaster.fit(df_product_daily[target_col])
            
            # Simple in-sample sanity
            preds = forecaster.predict(n_obs)
            metrics = evaluate_forecast(df_product_daily[target_col].values, preds)

            return {
                "selected_model_name": "Moving Average (Sparse Fallback)",
                "model_type": "baseline",
                "model_object": forecaster,
                "features_df": df_product_daily,
                "val_metrics": metrics,
                "val_actuals": df_product_daily[target_col].tolist(),
                "val_predictions": preds.tolist(),
                "val_dates": pd.to_datetime(df_product_daily["sale_date"]).dt.strftime("%Y-%m-%d").tolist(),
                "candidate_evaluations": {"Moving Average": metrics},
                "data_notes": "; ".join(data_notes)
            }

        # Check for highly intermittent demand
        zero_ratio = (n_obs - non_zero_days) / n_obs
        if zero_ratio > 0.65:
            data_notes.append("High demand intermittency detected (>65% zero-sales days).")

        # Feature engineering
        feat_df = create_time_series_features(df_product_daily, target_col=target_col)
        train_feat, val_feat = chronological_split(feat_df, val_days=self.val_days)

        val_horizon = len(val_feat)
        val_actual = val_feat[target_col].values
        val_dates = pd.to_datetime(val_feat["sale_date"]).dt.strftime("%Y-%m-%d").tolist()

        # Candidates to evaluate
        candidates = {}

        # 1. Naive Baseline
        naive = NaiveForecaster().fit(train_feat[target_col])
        pred_naive = naive.predict(val_horizon)
        candidates["Naive Baseline"] = {
            "model": naive,
            "type": "baseline",
            "preds": pred_naive,
            "metrics": evaluate_forecast(val_actual, pred_naive)
        }

        # 2. Seasonal Naive (7-day)
        snaive = SeasonalNaiveForecaster(season_length=7).fit(train_feat[target_col])
        pred_snaive = snaive.predict(val_horizon)
        candidates["Seasonal Naive (7-day)"] = {
            "model": snaive,
            "type": "baseline",
            "preds": pred_snaive,
            "metrics": evaluate_forecast(val_actual, pred_snaive)
        }

        # 3. Moving Average (7-day)
        ma = MovingAverageForecaster(window=7).fit(train_feat[target_col])
        pred_ma = ma.predict(val_horizon)
        candidates["Moving Average (7-day)"] = {
            "model": ma,
            "type": "baseline",
            "preds": pred_ma,
            "metrics": evaluate_forecast(val_actual, pred_ma)
        }

        # 4. Exponential Smoothing
        es = ExponentialSmoothingForecaster(alpha=0.3).fit(train_feat[target_col])
        pred_es = es.predict(val_horizon)
        candidates["Exponential Smoothing"] = {
            "model": es,
            "type": "baseline",
            "preds": pred_es,
            "metrics": evaluate_forecast(val_actual, pred_es)
        }

        # 5. ML Models (Ridge ML / XGBoost / Random Forest) if sufficient training data (>= 21 days)
        if len(train_feat) >= 21:
            X_train = train_feat[FEATURE_COLUMNS].values
            y_train = train_feat[target_col].values
            X_val = val_feat[FEATURE_COLUMNS].values

            # Pure NumPy Ridge ML Regressor (always available, ultra-lightweight)
            try:
                ridge_model = NumpyRidgeRegressor(alpha=1.0)
                ridge_model.fit(X_train, y_train)
                pred_ridge = ridge_model.predict(X_val)
                candidates["Ridge Autoregressive ML"] = {
                    "model": ridge_model,
                    "type": "ml",
                    "preds": pred_ridge,
                    "metrics": evaluate_forecast(val_actual, pred_ridge)
                }
            except Exception as e:
                data_notes.append(f"Ridge ML fitting failed ({str(e)}), skipped.")

            # XGBoost (if available)
            if HAS_XGBOOST:
                try:
                    xgb_model = xgb.XGBRegressor(
                        n_estimators=50,
                        max_depth=3,
                        learning_rate=0.08,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        n_jobs=1
                    )
                    xgb_model.fit(X_train, y_train)
                    pred_xgb = np.maximum(xgb_model.predict(X_val), 0.0)
                    candidates["XGBoost Regressor"] = {
                        "model": xgb_model,
                        "type": "ml",
                        "preds": pred_xgb,
                        "metrics": evaluate_forecast(val_actual, pred_xgb)
                    }
                except Exception as e:
                    data_notes.append(f"XGBoost fitting failed ({str(e)}), skipped.")

            # Random Forest Regressor (if available)
            if HAS_SKLEARN:
                try:
                    rf_model = RandomForestRegressor(
                        n_estimators=50,
                        max_depth=4,
                        min_samples_split=3,
                        random_state=42,
                        n_jobs=1
                    )
                    rf_model.fit(X_train, y_train)
                    pred_rf = np.maximum(rf_model.predict(X_val), 0.0)
                    candidates["Random Forest Regressor"] = {
                        "model": rf_model,
                        "type": "ml",
                        "preds": pred_rf,
                        "metrics": evaluate_forecast(val_actual, pred_rf)
                    }
                except Exception as e:
                    data_notes.append(f"Random Forest fitting failed ({str(e)}), skipped.")

        # Selection logic
        if model_preference != "Best Model (Auto-select)" and model_preference in candidates:
            chosen_name = model_preference
        else:
            # Select model with lowest validation WAPE, then lowest MAE
            chosen_name = min(
                candidates.keys(),
                key=lambda k: (candidates[k]["metrics"]["wape_pct"], candidates[k]["metrics"]["mae"])
            )

        chosen_entry = candidates[chosen_name]

        # Retrain ML model on FULL dataset if an ML model was chosen
        final_model = chosen_entry["model"]
        if chosen_entry["type"] == "ml":
            X_full = feat_df[FEATURE_COLUMNS].values
            y_full = feat_df[target_col].values
            if chosen_name == "Ridge Autoregressive ML":
                final_model = NumpyRidgeRegressor(alpha=1.0)
                final_model.fit(X_full, y_full)
            elif chosen_name == "XGBoost Regressor" and HAS_XGBOOST:
                final_model = xgb.XGBRegressor(
                    n_estimators=50,
                    max_depth=3,
                    learning_rate=0.08,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=1
                )
                final_model.fit(X_full, y_full)
            elif chosen_name == "Random Forest Regressor" and HAS_SKLEARN:
                final_model = RandomForestRegressor(
                    n_estimators=50,
                    max_depth=4,
                    min_samples_split=3,
                    random_state=42,
                    n_jobs=1
                )
                final_model.fit(X_full, y_full)
        else:
            # Retrain baseline model preserving configured parameters on full series
            final_model = final_model.fit(feat_df[target_col])

        candidate_summaries = {k: v["metrics"] for k, v in candidates.items()}

        return {
            "selected_model_name": chosen_name,
            "model_type": chosen_entry["type"],
            "model_object": final_model,
            "features_df": feat_df,
            "val_metrics": chosen_entry["metrics"],
            "val_actuals": val_actual.tolist(),
            "val_predictions": chosen_entry["preds"].tolist(),
            "val_dates": val_dates,
            "candidate_evaluations": candidate_summaries,
            "data_notes": "; ".join(data_notes) if data_notes else "Standard validation completed without anomalies."
        }
