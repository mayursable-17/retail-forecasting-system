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

        # Mode parameters pre-filled from persisted shop defaults
        cur_review = int(shop.get("default_review_period_days", 7) or 7)
        cur_method = str(shop.get("default_safety_stock_method", "variability") or "variability")
        cur_sl = float(shop.get("default_service_level", 0.95) or 0.95)
        cur_buf = float(shop.get("default_replenishment_buffer_pct", 0.20) or 0.20)

        if is_mode_b:
            st.markdown("#### ⚙️ Workflow B Parameters (Periodic Review & Safety Stock)")
            p1, p2, p3 = st.columns(3)
            with p1:
                review_period = st.number_input("Store Review Period (Days)", min_value=1, max_value=30, value=cur_review,
                                                help="How often the shopkeeper places replenishment orders (e.g., weekly = 7 days).")
            with p2:
                method_opts = ["variability", "buffer"]
                idx_m = method_opts.index(cur_method) if cur_method in method_opts else 0
                ss_method = st.selectbox(
                    "Safety Stock Calculation Method",
                    options=method_opts,
                    index=idx_m,
                    format_func=lambda x: "Normal Variability (z * sigma * sqrt(L))" if x == "variability" else "Configurable Fixed Buffer (%)"
                )
            with p3:
                if ss_method == "variability":
                    sl_opts = [0.80, 0.85, 0.90, 0.95, 0.98, 0.99]
                    idx_sl = sl_opts.index(cur_sl) if cur_sl in sl_opts else 3
                    service_level = st.selectbox(
                        "Target Cycle Service Level",
                        options=sl_opts,
                        index=idx_sl,
                        format_func=lambda sl: f"{int(sl*100)}% (z = {SERVICE_LEVEL_Z_MAP.get(sl, 1.65)})"
                    )
                    buffer_pct = cur_buf
                else:
                    buffer_pct = st.slider("Replenishment Buffer %", min_value=5, max_value=50, value=int(cur_buf * 100)) / 100.0
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
                buffer_pct = st.slider("Replenishment Buffer %", min_value=5, max_value=40, value=int(cur_buf * 100)) / 100.0

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
                st.rerun()

        # Display stored recommendations
        recs_df = repo.get_recommendations_df(latest_run["run_id"])

        if not recs_df.empty:
            cur = shop["currency_symbol"]
            st.markdown("---")
            st.subheader("📋 Reorder & Stock Health Overview")

            # Status distribution cards
            status_counts = recs_df["risk_status"].value_counts().to_dict()
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1:
                render_metric_card("Stock Risk", f"{status_counts.get('Stock Risk', 0)}", "Depleted / imminent stockout", border_color="#E53935", icon="🚨")
            with sc2:
                render_metric_card("Reorder Review", f"{status_counts.get('Reorder Review', 0)}", "At or below Reorder Point", border_color="#FB8C00", icon="⚠️")
            with sc3:
                render_metric_card("Adequate Stock", f"{status_counts.get('Adequate Stock', 0)}", "Healthy buffer above ROP", border_color="#43A047", icon="✅")
            with sc4:
                render_metric_card("Potential Excess", f"{status_counts.get('Potential Excess Stock', 0)}", "Surplus stock risk", border_color="#8E24AA", icon="📦")
            with sc5:
                render_metric_card("Info Needed", f"{status_counts.get('Insufficient Inventory Information', 0)}", "Stock counts unknown", border_color="#757575", icon="❓")

            # Purchase Order Financial Overview
            po_items = recs_df[recs_df["suggested_qty"] > 0]
            total_po_units = float(po_items["suggested_qty"].sum())
            total_po_val = float((po_items["suggested_qty"] * po_items.get("unit_price", 0.0)).sum())

            f_po1, f_po2, f_po3 = st.columns(3)
            with f_po1:
                st.metric("Total Items to Order", f"{len(po_items)} SKU(s)")
            with f_po2:
                st.metric("Total Order Volume", f"{total_po_units:,.1f} Units")
            with f_po3:
                st.metric("Estimated PO Investment", f"{cur}{total_po_val:,.2f}")

            # Risk Chart
            st.plotly_chart(plot_inventory_risk_pie(recs_df), use_container_width=True)

            # Interactive Table with editable order quantities and interactive filters
            st.markdown("---")
            st.subheader("📝 Review & Edit Purchase Order Quantities")
            st.caption("You can modify suggested order quantities directly in the grid below, then click **Save Overrides** to persist.")

            # Filter options
            filt_col1, filt_col2 = st.columns([1, 1])
            with filt_col1:
                all_statuses = ["All Statuses"] + sorted(recs_df["risk_status"].unique())
                sel_status = st.selectbox("Filter by Stock Status", all_statuses)
            with filt_col2:
                all_cats = ["All Categories"] + sorted(recs_df["category"].unique())
                sel_cat = st.selectbox("Filter by Category", all_cats)

            # Apply view filter
            view_recs = recs_df.copy()
            if sel_status != "All Statuses":
                view_recs = view_recs[view_recs["risk_status"] == sel_status]
            if sel_cat != "All Categories":
                view_recs = view_recs[view_recs["category"] == sel_cat]

            view_recs["suggested_qty"] = view_recs["suggested_qty"].round(1)
            for c in ["reorder_point", "current_stock", "inventory_position", "safety_stock", "order_up_to_target"]:
                if c in view_recs.columns:
                    view_recs[c] = view_recs[c].fillna("-")

            cols_order = [
                "product_id", "product_name", "category", "risk_status",
                "current_stock", "inventory_position", "reorder_point",
                "safety_stock", "order_up_to_target", "suggested_qty", "explanation"
            ]
            existing_cols = [c for c in cols_order if c in view_recs.columns]

            edited_recs = st.data_editor(
                view_recs[existing_cols],
                key="recs_data_editor",
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

            # Interactive Actions Row
            act1, act2, act3 = st.columns([2, 2, 1])
            with act1:
                if st.button("💾 Save Order Overrides to Database", type="primary", use_container_width=True):
                    overrides = {}
                    for _, row in edited_recs.iterrows():
                        overrides[str(row["product_id"])] = float(row["suggested_qty"])
                    saved_count = repo.update_recommendations_overrides(latest_run["run_id"], overrides)
                    st.success(f"Successfully saved {saved_count} custom order quantities to database!")
                    st.rerun()

            with act2:
                # Direct PO Export CSV
                po_export = recs_df[recs_df["suggested_qty"] > 0][[
                    "product_id", "product_name", "category", "suggested_qty", "unit_price", "explanation"
                ]].copy()
                po_export["total_line_cost"] = (po_export["suggested_qty"] * po_export["unit_price"]).round(2)
                st.download_button(
                    label="📥 Download Confirmed PO (CSV)",
                    data=po_export.to_csv(index=False).encode("utf-8"),
                    file_name=f"Purchase_Order_Run_{latest_run['run_id']}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with act3:
                st.page_link("pages/7_Reports.py", label="Full Reports", icon="📑")

        else:
            st.info("👆 Click **'Calculate Replenishment Recommendations'** to run the inventory optimization engine.")
