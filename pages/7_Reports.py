"""
Page 7: Reports and Data Downloads
Generates styled multi-tab Excel workbooks and CSV exports.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop
from src.exports.excel_report import generate_retail_master_excel, convert_df_to_csv_bytes
from src.analytics.kpis import compute_overview_kpis

st.set_page_config(page_title="Reports & Downloads - Retail System", page_icon="📑", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("📑 Export Reports & Data Downloads")
st.markdown("Download comprehensive multi-tab Excel reports and CSV files for accounting, suppliers, and audits.")

# Fetch system data
sales_df = repo.get_daily_sales_df(shop_id=shop["shop_id"])

# Check if data exists
if sales_df.empty:
    st.warning("⚠️ No data available in the system to generate reports. Please load data first.")
    st.page_link("pages/1_Upload_Data.py", label="➡️ Go to Upload Data", icon="📤")
    st.stop()
else:
    kpis = compute_overview_kpis(sales_df)
    products_df = repo.get_products_df(shop_id=shop["shop_id"])

    latest_run = repo.get_latest_forecast_run(shop_id=shop["shop_id"])
    forecast_df = repo.get_forecast_results_df(latest_run["run_id"]) if latest_run else pd.DataFrame()
    recs_df = repo.get_recommendations_df(latest_run["run_id"]) if latest_run else pd.DataFrame()
    quality_report = st.session_state.get("latest_quality_report")

    # 1. Master Excel Download
    st.subheader("📊 Master System Excel Workbook")
    st.markdown(
        "A fully styled, multi-sheet Excel file containing Executive Summary, Cleaned Sales Data, "
        "Quality Audit Trail, Product Analytics, Demand Forecasts, and Inventory Replenishment Orders."
    )

    inv_mode = recs_df["inventory_mode"].iloc[0] if not recs_df.empty else "inventory_mode"
    val_metrics = latest_run["validation_metrics"] if latest_run else None

    with st.spinner("Generating styled Excel workbook..."):
        excel_bytes = generate_retail_master_excel(
            shop_info=shop,
            kpis=kpis,
            cleaned_sales_df=sales_df,
            quality_report=quality_report,
            product_analytics_df=products_df,
            forecast_results_df=forecast_df,
            validation_metrics=val_metrics,
            recommendations_df=recs_df,
            inventory_mode=inv_mode
        )

    st.download_button(
        label="📥 Download Master Retail Analytics & Inventory Workbook (.xlsx)",
        data=excel_bytes,
        file_name=f"{shop['shop_name'].replace(' ', '_')}_Full_Report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

    st.markdown("---")

    # 2. Individual CSV Exports
    st.subheader("📄 Individual Section CSV Exports")
    st.write("Download specific data tables in CSV format for lightweight integration.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 1. Cleaned Daily Sales Data")
        st.download_button(
            "📥 Download Daily Sales (CSV)",
            data=convert_df_to_csv_bytes(sales_df),
            file_name="cleaned_daily_sales.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("##### 2. Product Catalog & Parameters")
        if not products_df.empty:
            st.download_button(
                "📥 Download Product Catalog (CSV)",
                data=convert_df_to_csv_bytes(products_df),
                file_name="product_catalog.csv",
                mime="text/csv",
                use_container_width=True
            )

    with c2:
        st.markdown("##### 3. Demand Forecast Results")
        if not forecast_df.empty:
            st.download_button(
                "📥 Download Forecast Results (CSV)",
                data=convert_df_to_csv_bytes(forecast_df),
                file_name="demand_forecast_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Run a forecast on the Demand Forecasting page to enable forecast export.")

        st.markdown("##### 4. Inventory Reorder Recommendations")
        if not recs_df.empty:
            st.download_button(
                "📥 Download Reorder Recommendations (CSV)",
                data=convert_df_to_csv_bytes(recs_df),
                file_name="inventory_reorder_recommendations.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Run inventory optimization to enable recommendations export.")
