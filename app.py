"""
Retail Sales Forecasting & Inventory Optimization System
Main Entry Point & Home Dashboard
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from datetime import datetime

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop, render_metric_card
from src.analytics.kpis import compute_overview_kpis, get_top_and_bottom_products, compute_category_breakdown, compute_weekday_weekend_stats
from src.analytics.charts import plot_revenue_trend, plot_category_distribution, plot_top_products_bar, plot_weekday_vs_weekend
from src.config import SAMPLE_DIR
from src.generate_samples import generate_all_samples

st.set_page_config(
    page_title="Retail Sales Forecasting & Inventory System",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

# Sidebar Branding
st.sidebar.markdown(f"### 🏪 {shop['shop_name']}")
st.sidebar.caption(f"**Type:** {shop['shop_type']}")
st.sidebar.caption(f"**Currency:** {shop['currency_code']} ({shop['currency_symbol']})")
st.sidebar.markdown("---")

# Fetch current sales data
sales_df = repo.get_daily_sales_df(shop_id=shop["shop_id"])

# ----------------- ONBOARDING SCREEN IF NO DATA -----------------
if sales_df.empty:
    st.title("🛒 Retail Sales Forecasting & Inventory Optimization System")
    st.markdown("##### Intelligent Demand Prediction & Supply Chain Optimization for Small Retailers")

    st.info(
        "👋 **Welcome! No sales data has been loaded into the system yet.**\n\n"
        "To explore the application, you can either **load the built-in Kirana Store demo dataset** "
        "(12 products, 90 days of transactions, inventory snapshots), or **upload your own CSV/Excel sales files**."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚀 Quick Demo Mode")
        st.write("Instant one-click setup using realistic synthetic Kirana / Retail data.")
        if st.button("📥 Load Built-in Kirana Store Dataset", type="primary", use_container_width=True):
            with st.spinner("Populating database with synthetic Kirana dataset..."):
                # Ensure samples exist
                if not (SAMPLE_DIR / "sample_daily_sales.csv").exists():
                    generate_all_samples()

                df_sample_daily = pd.read_csv(SAMPLE_DIR / "sample_daily_sales.csv")
                df_sample_inv = pd.read_csv(SAMPLE_DIR / "sample_inventory.csv")

                # Upsert products
                prods_data = []
                for _, r in df_sample_inv.iterrows():
                    prods_data.append({
                        "product_id": str(r["product_id"]),
                        "product_name": str(r["product_name"]),
                        "category": str(r["category"]),
                        "unit_price": float(df_sample_daily[df_sample_daily["product_id"] == r["product_id"]]["revenue"].sum() /
                                            max(1, df_sample_daily[df_sample_daily["product_id"] == r["product_id"]]["quantity_sold"].sum())),
                        "lead_time_days": int(r["lead_time_days"]),
                        "minimum_order_quantity": float(r["min_order_qty"]),
                        "case_pack_size": float(r["case_pack_size"])
                    })
                repo.upsert_products(shop["shop_id"], prods_data)

                # Record upload
                upload_id = repo.create_upload_record(
                    shop_id=shop["shop_id"],
                    file_name="sample_daily_sales.csv",
                    file_hash="demo_hash",
                    upload_type="combined",
                    row_count=len(df_sample_daily),
                    quality_summary={"status": "Demo dataset auto-loaded"}
                )

                # Save daily sales
                repo.save_daily_sales(shop["shop_id"], upload_id, df_sample_daily)

                # Save inventory snapshot
                inv_snapshots = []
                for _, r in df_sample_inv.iterrows():
                    inv_snapshots.append({
                        "product_id": str(r["product_id"]),
                        "on_hand_qty": float(r["current_stock"]),
                        "on_order_qty": float(r["on_order"]),
                        "backorders": 0.0,
                        "lead_time_days": int(r["lead_time_days"])
                    })
                repo.save_inventory_snapshot(shop["shop_id"], inv_snapshots)

                st.success("Demo dataset loaded successfully! Reloading dashboard...")
                st.rerun()

    with col2:
        st.subheader("📂 Upload Custom Data")
        st.write("Upload your shop's own sales receipts, invoice logs, or inventory sheets.")
        st.page_link("pages/1_Upload_Data.py", label="➡️ Navigate to Upload Page", icon="📤")

    st.markdown("---")
    st.markdown("""
    ### 🎯 System Features
    - **Dual Inventory Modes:** Works with sales data alone (*Mode A: Estimated Requirements*) or with full stock data (*Mode B: Exact Reorder Points*).
    - **Flexible Ingestion:** Reads CSV and Excel spreadsheets with automated column header detection.
    - **Robust Data Cleaning:** Identifies returns, duplicates, and missing dates; provides transparent audit logs.
    - **Machine Learning Forecasting:** Compares Naive, Moving Average, Exponential Smoothing, and XGBoost models using chronological out-of-sample validation.
    - **Supply Chain Optimization:** Calculates Reorder Points (ROP), Safety Stock via normal distribution variability, and Order-up-to Targets ($S$).
    """)
    st.stop()
else:
    # ----------------- LIVE HOME DASHBOARD -----------------
    st.title(f"📊 {shop['shop_name']} - Performance Overview")
    st.caption(f"Store Type: **{shop['shop_type']}** | Base Currency: **{shop['currency_code']} ({shop['currency_symbol']})**")

    # Top Filters
    with st.expander("🔍 Filter Dashboard Data", expanded=False):
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            dt_series = pd.to_datetime(sales_df["sale_date"])
            min_date = dt_series.min().date()
            max_date = dt_series.max().date()
            selected_date_range = st.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        with fcol2:
            all_categories = sorted(sales_df["category"].unique())
            selected_categories = st.multiselect(
                "Filter Categories",
                options=all_categories,
                default=all_categories
            )

    # Apply filters
    filtered_df = sales_df.copy()
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_d, end_d = selected_date_range
        filtered_df = filtered_df[
            (filtered_df["sale_date"].dt.date >= start_d) &
            (filtered_df["sale_date"].dt.date <= end_d)
        ]
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]

    # KPI Computations
    kpis = compute_overview_kpis(filtered_df)
    cur = shop["currency_symbol"]

    # Metric Cards Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        render_metric_card(
            "Total Revenue",
            f"{cur}{kpis['total_revenue']:,.2f}",
            f"Over {kpis['total_days']} active days",
            border_color="#1E88E5"
        )
    with kpi2:
        render_metric_card(
            "Total Units Sold",
            f"{kpis['total_units_sold']:,.1f}",
            f"Avg {(kpis['total_units_sold']/max(1, kpis['total_days'])):.1f} units/day",
            border_color="#43A047"
        )
    with kpi3:
        render_metric_card(
            "Active Products",
            f"{kpis['total_products']}",
            f"In {len(selected_categories)} selected categories",
            border_color="#FB8C00"
        )
    with kpi4:
        render_metric_card(
            "Avg Daily Revenue",
            f"{cur}{kpis['avg_daily_revenue']:,.2f}",
            f"Date range: {kpis['start_date']} to {kpis['end_date']}",
            border_color="#8E24AA"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart Row 1: Daily Revenue Trend
    st.plotly_chart(plot_revenue_trend(filtered_df, currency_symbol=cur), use_container_width=True)

    # Chart Row 2: Category Distribution and Day of Week Patterns
    c_left, c_right = st.columns([1, 1])
    with c_left:
        cat_df = compute_category_breakdown(filtered_df)
        st.plotly_chart(plot_category_distribution(cat_df, currency_symbol=cur), use_container_width=True)

    with c_right:
        day_stats = compute_weekday_weekend_stats(filtered_df)
        st.plotly_chart(plot_weekday_vs_weekend(day_stats, currency_symbol=cur), use_container_width=True)

    # Product Rankings
    st.subheader("🏆 Product Sales Highlights")
    top_df, bottom_df = get_top_and_bottom_products(filtered_df, top_n=5)

    p_left, p_right = st.columns(2)
    with p_left:
        st.markdown("##### 🟢 Top 5 Best-Selling Products")
        if not top_df.empty:
            display_top = top_df.copy()
            display_top["revenue"] = display_top["revenue"].apply(lambda x: f"{cur}{x:,.2f}")
            display_top["quantity_sold"] = display_top["quantity_sold"].apply(lambda x: f"{x:,.1f}")
            display_top.columns = ["Product ID", "Product Name", "Category", "Units Sold", "Total Revenue"]
            st.dataframe(display_top, hide_index=True, use_container_width=True)
        else:
            st.write("No product data matching current filters.")

    with p_right:
        st.markdown("##### 🔴 5 Slowest-Moving Products")
        if not bottom_df.empty:
            display_bot = bottom_df.copy()
            display_bot["revenue"] = display_bot["revenue"].apply(lambda x: f"{cur}{x:,.2f}")
            display_bot["quantity_sold"] = display_bot["quantity_sold"].apply(lambda x: f"{x:,.1f}")
            display_bot.columns = ["Product ID", "Product Name", "Category", "Units Sold", "Total Revenue"]
            st.dataframe(display_bot, hide_index=True, use_container_width=True)
        else:
            st.write("No product data matching current filters.")

    # Quick Navigation Footer
    st.markdown("---")
    st.subheader("⚡ Quick Navigation")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.page_link("pages/1_Upload_Data.py", label="Upload New Data", icon="📤")
    with q2:
        st.page_link("pages/3_Sales_Analytics.py", label="Detailed Sales Analytics", icon="📈")
    with q3:
        st.page_link("pages/4_Demand_Forecasting.py", label="Run Demand Forecast", icon="🔮")
    with q4:
        st.page_link("pages/5_Inventory_Optimization.py", label="Inventory Optimization", icon="📦")
