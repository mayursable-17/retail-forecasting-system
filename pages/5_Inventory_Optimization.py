"""
Page 5: Inventory Optimization & Reorder Recommendations Engine
Implements Mode A (Sales Only) and Mode B (Sales + Inventory) supply chain calculations.
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
from src.inventory.recommendations import generate_mode_a_recommendations, generate_mode_b_recommendations
from src.analytics.charts import plot_inventory_risk_pie
from src.config import SERVICE_LEVEL_Z_MAP, DEFAULT_SERVICE_LEVEL

st.set_page_config(page_title="Inventory Optimization - Retail System", page_icon="📦", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("📦 Inventory Optimization & Replenishment")
st.markdown("Calculate statistical safety stock, reorder points (ROP), order-up-to targets ($S$), and order quantities.")

# Verify prerequisites: do we have a forecast run?
latest_run = repo.get_latest_forecast_run(shop_id=shop["shop_id"])
if not latest_run:
    st.warning("⚠️ No demand forecasts found in the database. Please generate a forecast first.")
    st.page_link("pages/4_Demand_Forecasting.py", label="➡️ Go to Demand Forecasting", icon="🔮")
    st.stop()
else:
    forecast_results_df = repo.get_forecast_results_df(latest_run["run_id"])
    if forecast_results_df.empty:
        st.warning("⚠️ Forecast run contains no prediction rows. Please re-run forecasting.")
    else:
        # Check if inventory snapshots exist
        snapshots_df = repo.get_latest_inventory_snapshots(shop_id=shop["shop_id"])
        has_inventory_data = not snapshots_df.empty

        # Workflow Mode Selection
        st.markdown("### 🔀 Select Optimization Workflow")
        w_col1, w_col2 = st.columns(2)
        with w_col1:
            mode_choice = st.radio(
                "Workflow Mode",
                options=[
                    "Workflow B: Sales + Current Inventory (Full ROP & Safety Stock)",
                    "Workflow A: Sales Data Only (Estimated Gross Requirements)"
                ],
                index=0 if has_inventory_data else 1,
                help="Choose Workflow B if you have entered stock counts; otherwise use Workflow A for planning demand estimates."
            )

        is_mode_b = "Workflow B" in mode_choice

        # Mode parameters
        if is_mode_b:
            st.markdown("#### ⚙️ Workflow B Parameters (Periodic Review & Safety Stock)")
            p1, p2, p3 = st.columns(3)
            with p1:
                review_period = st.number_input("Store Review Period (Days)", min_value=1, max_value=30, value=7,
                                                help="How often the shopkeeper places replenishment orders (e.g., weekly = 7 days).")
            with p2:
                ss_method = st.selectbox("Safety Stock Calculation Method",
                                         options=["variability", "buffer"],
                                         format_func=lambda x: "Normal Variability (z * sigma * sqrt(L))" if x == "variability" else "Configurable Fixed Buffer (%)")
            with p3:
                if ss_method == "variability":
                    service_level = st.selectbox(
                        "Target Cycle Service Level",
                        options=[0.80, 0.85, 0.90, 0.95, 0.98, 0.99],
                        index=3,
                        format_func=lambda sl: f"{int(sl*100)}% (z = {SERVICE_LEVEL_Z_MAP[sl]})"
                    )
                    buffer_pct = 0.20
                else:
                    buffer_pct = st.slider("Replenishment Buffer %", min_value=5, max_value=50, value=20) / 100.0
                    service_level = 0.95

            if not has_inventory_data:
                st.warning("⚠️ No inventory snapshot found in database. Entering Mode B will estimate missing stock as 0. You can upload inventory or enter counts on the Product Management page.")
        else:
            st.markdown("#### ⚙️ Workflow A Parameters (Estimated Gross Requirements)")
            st.info(
                "ℹ️ **Workflow A Notice:** On-hand inventory and incoming purchase orders are unknown. "
                "The system estimates product demand over the planning period plus a safety buffer. "
                "These figures represent **estimated gross requirements**, NOT confirmed reorder purchase orders or stockout alerts."
            )
            p1, p2 = st.columns(2)
            with p1:
                planning_period = st.selectbox("Planning Horizon (Days)", options=[7, 15, 30], index=1)
            with p2:
                buffer_pct = st.slider("Replenishment Buffer %", min_value=5, max_value=40, value=15) / 100.0

        # Run Optimization Button
        if st.button("🚀 Calculate Replenishment Recommendations", type="primary", use_container_width=True):
            with st.spinner("Executing inventory supply chain optimization engine..."):
                if is_mode_b:
                    sales_daily_df = repo.get_daily_sales_df(shop_id=shop["shop_id"])
                    recs = generate_mode_b_recommendations(
                        forecast_results_df=forecast_results_df,
                        inventory_snapshots_df=snapshots_df,
                        historical_daily_sales_df=sales_daily_df,
                        review_period_days=review_period,
                        safety_stock_method=ss_method,
                        service_level=service_level,
                        buffer_percentage=buffer_pct
                    )
                else:
                    prods_df = repo.get_products_df(shop_id=shop["shop_id"])
                    recs = generate_mode_a_recommendations(
                        forecast_results_df=forecast_results_df,
                        products_df=prods_df,
                        planning_period_days=planning_period,
                        replenishment_buffer_pct=buffer_pct
                    )

                repo.save_recommendations(latest_run["run_id"], recs)
                st.session_state["cached_recs"] = recs
                st.success(f"Successfully calculated optimization for {len(recs)} catalog items!")

        # Display stored recommendations
        recs_df = repo.get_recommendations_df(latest_run["run_id"])

        if not recs_df.empty:
            st.markdown("---")
            st.subheader("📋 Reorder & Stock Health Recommendations")

            # Status distribution cards
            status_counts = recs_df["risk_status"].value_counts().to_dict()
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1:
                render_metric_card("Stock Risk", f"{status_counts.get('Stock Risk', 0)}", "Depleted or imminent stockout", border_color="#E53935")
            with sc2:
                render_metric_card("Reorder Review", f"{status_counts.get('Reorder Review', 0)}", "At or below Reorder Point", border_color="#FB8C00")
            with sc3:
                render_metric_card("Adequate Stock", f"{status_counts.get('Adequate Stock', 0)}", "Healthy buffer above ROP", border_color="#43A047")
            with sc4:
                render_metric_card("Potential Excess", f"{status_counts.get('Potential Excess Stock', 0)}", "Surplus stock risk", border_color="#8E24AA")
            with sc5:
                render_metric_card("Info Needed", f"{status_counts.get('Insufficient Inventory Information', 0)}", "Stock counts unknown", border_color="#757575")

            # Risk Chart
            st.plotly_chart(plot_inventory_risk_pie(recs_df), use_container_width=True)

            # Interactive Table with editable order quantities
            st.subheader("📝 Review & Edit Preliminary Order Quantities")
            st.caption("You can review the mathematical rationale and modify suggested orders before generating purchase orders or exporting.")

            # Format table for display
            display_recs = recs_df.copy()
            display_recs["suggested_qty"] = display_recs["suggested_qty"].round(1)
            if "reorder_point" in display_recs.columns:
                display_recs["reorder_point"] = display_recs["reorder_point"].fillna("-")
            if "current_stock" in display_recs.columns:
                display_recs["current_stock"] = display_recs["current_stock"].fillna("-")
            if "inventory_position" in display_recs.columns:
                display_recs["inventory_position"] = display_recs["inventory_position"].fillna("-")
            if "safety_stock" in display_recs.columns:
                display_recs["safety_stock"] = display_recs["safety_stock"].fillna("-")
            if "order_up_to_target" in display_recs.columns:
                display_recs["order_up_to_target"] = display_recs["order_up_to_target"].fillna("-")

            cols_order = [
                "product_id", "product_name", "category", "risk_status",
                "current_stock", "inventory_position", "reorder_point",
                "safety_stock", "order_up_to_target", "suggested_qty", "explanation"
            ]
            existing_cols = [c for c in cols_order if c in display_recs.columns]

            edited_recs = st.data_editor(
                display_recs[existing_cols],
                column_config={
                    "suggested_qty": st.column_config.NumberColumn(
                        "Suggested Order Qty",
                        help="Recommended preliminary replenishment order units. Editable.",
                        min_value=0.0,
                        step=1.0
                    ),
                    "risk_status": st.column_config.TextColumn("Risk Status"),
                    "explanation": st.column_config.TextColumn("Mathematical Explanation & Business Rules", width="large")
                },
                disabled=[c for c in existing_cols if c != "suggested_qty"],
                hide_index=True,
                use_container_width=True
            )

            st.markdown("---")
            st.page_link("pages/7_Reports.py", label="➡️ Proceed to Reports & Downloads", icon="📥")

        else:
            st.info("👆 Click **'Calculate Replenishment Recommendations'** to run the inventory optimization engine.")
