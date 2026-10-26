"""
Page 4: Demand Forecasting Engine & Model Evaluation
Trains statistical and ML forecasting models with chronological validation.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop, render_metric_card
from src.forecasting.train import DemandModelTrainer
from src.forecasting.predict import generate_future_forecast
from src.analytics.charts import plot_forecast_vs_history
from src.config import ALLOWED_HORIZONS

st.set_page_config(page_title="Demand Forecasting - Retail System", page_icon="🔮", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("🔮 Machine Learning Demand Forecasting")
st.markdown("Forecast future retail product demand using chronological out-of-sample validation.")

sales_df = repo.get_daily_sales_df(shop_id=shop["shop_id"])

if sales_df.empty:
    st.warning("⚠️ No sales data found. Please load the sample dataset or upload sales data first.")
    st.page_link("pages/1_Upload_Data.py", label="➡️ Go to Upload Data", icon="📤")
    st.stop()
else:
    # Configuration Sidebar
    st.sidebar.markdown("### ⚙️ Forecast Parameters")
    horizon_days = st.sidebar.selectbox("Forecast Horizon (Days)", options=ALLOWED_HORIZONS, index=1)
    model_options = [
        "Best Model (Auto-select)",
        "XGBoost Regressor",
        "Random Forest Regressor",
        "Exponential Smoothing",
        "Moving Average (7-day)",
        "Seasonal Naive (7-day)",
        "Naive Baseline"
    ]
    selected_model_pref = st.sidebar.selectbox("Forecasting Algorithm", options=model_options, index=0)

    products_list = sales_df[["product_id", "product_name"]].drop_duplicates().sort_values(by="product_name")
    prod_options = {row["product_name"]: row["product_id"] for _, row in products_list.iterrows()}
    
    selected_prod_name = st.selectbox("Select Target Product to Forecast", list(prod_options.keys()))
    selected_pid = prod_options[selected_prod_name]

    # Forecast Run Action
    c_run, c_batch = st.columns([1, 2])
    with c_run:
        run_btn = st.button("🚀 Train & Generate Forecast", type="primary", use_container_width=True)
    with c_batch:
        batch_btn = st.button("⚡ Forecast All Store Products (Batch Run)", use_container_width=True)

    # Prepare trainer
    trainer = DemandModelTrainer(val_days=min(14, max(4, int(horizon_days * 0.7))))

    if run_btn:
        with st.spinner(f"Training models with chronological validation for {selected_prod_name}..."):
            prod_daily = sales_df[sales_df["product_id"] == selected_pid].sort_values(by="sale_date").reset_index(drop=True)
            
            # Train & evaluate
            train_res = trainer.train_and_evaluate(
                prod_daily,
                model_preference=selected_model_pref,
                target_col="quantity_sold"
            )
            
            # Generate future forecast
            forecast_df = generate_future_forecast(
                train_res,
                product_id=selected_pid,
                horizon_days=horizon_days
            )
            
            # Save run into database
            run_id = repo.save_forecast_run(
                shop_id=shop["shop_id"],
                model_name=train_res["selected_model_name"],
                horizon_days=horizon_days,
                validation_metrics=train_res["val_metrics"],
                config={"model_preference": selected_model_pref, "product_id": selected_pid},
                forecast_rows=forecast_df.to_dict(orient="records")
            )

            st.session_state["active_forecast_run_id"] = run_id
            st.session_state["latest_train_res"] = train_res
            st.session_state["latest_forecast_df"] = forecast_df
            st.session_state["forecast_prod_name"] = selected_prod_name
            st.session_state["forecast_prod_id"] = selected_pid

            st.success(f"Forecast successfully computed! Selected Model: **{train_res['selected_model_name']}** (Run ID: {run_id})")

    elif batch_btn:
        with st.spinner("Executing batch forecasting for all active store catalog products..."):
            all_forecast_rows = []
            batch_metrics = {"models_used": {}}
            latest_res_single = None

            for p_name, p_id in prod_options.items():
                p_daily = sales_df[sales_df["product_id"] == p_id].sort_values(by="sale_date").reset_index(drop=True)
                res = trainer.train_and_evaluate(p_daily, model_preference=selected_model_pref)
                f_df = generate_future_forecast(res, product_id=p_id, horizon_days=horizon_days)
                all_forecast_rows.extend(f_df.to_dict(orient="records"))
                m_used = res["selected_model_name"]
                batch_metrics["models_used"][m_used] = batch_metrics["models_used"].get(m_used, 0) + 1
                if p_id == selected_pid:
                    latest_res_single = res
                    st.session_state["latest_forecast_df"] = f_df

            # Save batch run
            run_id = repo.save_forecast_run(
                shop_id=shop["shop_id"],
                model_name=f"Batch Portfolio ({len(prod_options)} Products)",
                horizon_days=horizon_days,
                validation_metrics=batch_metrics,
                config={"model_preference": selected_model_pref, "batch": True},
                forecast_rows=all_forecast_rows
            )
            st.session_state["active_forecast_run_id"] = run_id
            st.session_state["latest_train_res"] = latest_res_single
            st.session_state["forecast_prod_name"] = selected_prod_name
            st.session_state["forecast_prod_id"] = selected_pid

            st.success(f"Batch run completed for {len(prod_options)} products! (Run ID: {run_id})")


    # Display Results
    train_res = st.session_state.get("latest_train_res")
    forecast_df = st.session_state.get("latest_forecast_df")
    curr_prod_name = st.session_state.get("forecast_prod_name", selected_prod_name)
    curr_prod_id = st.session_state.get("forecast_prod_id", selected_pid)

    if train_res is not None and forecast_df is not None:
        st.markdown("---")
        st.subheader(f"📊 Forecast Performance & Validation: {curr_prod_name}")
        st.caption(f"Selected Algorithm: **{train_res['selected_model_name']}** | Diagnostic Notes: *{train_res.get('data_notes', 'N/A')}*")

        # Metrics Row
        vm = train_res.get("val_metrics", {})
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card("MAE (Holdout)", f"{vm.get('mae', 0.0):.2f}", "Mean Absolute Error", border_color="#1E88E5")
        with m2:
            render_metric_card("RMSE", f"{vm.get('rmse', 0.0):.2f}", "Root Mean Squared Error", border_color="#FB8C00")
        with m3:
            render_metric_card("WAPE", f"{vm.get('wape_pct', 0.0):.1f}%", "Weighted Abs % Error", border_color="#43A047")
        with m4:
            bias = vm.get("bias_pct", 0.0)
            bias_label = "Neutral" if abs(bias) < 2 else ("Over-predicting" if bias > 0 else "Under-predicting")
            render_metric_card("Forecast Bias", f"{bias:+.1f}%", f"{bias_label}", border_color="#8E24AA")

        # Interactive Forecast Plot
        prod_daily = sales_df[sales_df["product_id"] == curr_prod_id].sort_values(by="sale_date").reset_index(drop=True)
        fig_fc = plot_forecast_vs_history(
            history_df=prod_daily,
            forecast_df=forecast_df,
            val_dates=train_res.get("val_dates"),
            val_preds=train_res.get("val_predictions"),
            product_name=curr_prod_name
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        # Candidate Models Comparison Table
        if "candidate_evaluations" in train_res and train_res["candidate_evaluations"]:
            with st.expander("🔬 Model Selection & Baseline Benchmark Comparison", expanded=False):
                evals = []
                for m_name, met in train_res["candidate_evaluations"].items():
                    evals.append({
                        "Algorithm / Baseline": m_name,
                        "MAE (Units)": met.get("mae"),
                        "RMSE (Units)": met.get("rmse"),
                        "WAPE (%)": f"{met.get('wape_pct'):.2f}%",
                        "Bias (%)": f"{met.get('bias_pct'):+.2f}%",
                        "Status": "Selected 🏆" if m_name == train_res["selected_model_name"] else "Evaluated"
                    })
                df_evals = pd.DataFrame(evals).sort_values(by="MAE (Units)")
                st.dataframe(df_evals, hide_index=True, use_container_width=True)

        # Future Demand Table
        st.subheader(f"📅 Daily Predicted Demand for Next {len(forecast_df)} Days")
        display_forecast = forecast_df.copy()
        display_forecast["forecast_date"] = pd.to_datetime(display_forecast["forecast_date"]).dt.strftime("%A, %b %d, %Y")
        display_forecast.columns = ["Forecast Date", "Product ID", "Predicted Units", "Lower Bound (90%)", "Upper Bound (90%)"]
        st.dataframe(display_forecast[["Forecast Date", "Predicted Units", "Lower Bound (90%)", "Upper Bound (90%)"]], hide_index=True, use_container_width=True)

        st.markdown("---")
        st.info("💡 **Ready to plan stock replenishment?** Send this forecast to the Inventory Optimization engine to calculate safety stock and reorder points.")
        st.page_link("pages/5_Inventory_Optimization.py", label="➡️ Proceed to Inventory Optimization", icon="📦")

    else:
        st.info("👆 Click **'Train & Generate Forecast'** to run out-of-sample machine learning demand evaluation.")
