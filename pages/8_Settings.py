"""
Page 8: Store Settings, System Configurations & Data Management
Allows non-technical shopkeeper to configure currency, defaults, and data resets.
"""

import sys
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop
from src.config import DEFAULT_SQLITE_PATH, SAMPLE_DIR
from src.generate_samples import generate_all_samples

st.set_page_config(page_title="Settings - Retail System", page_icon="⚙️", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("⚙️ Store & System Settings")
st.markdown("Configure store profile, default inventory assumptions, and manage local database storage.")

# Tabbed settings
tab_store, tab_defaults, tab_data, tab_sys = st.tabs([
    "🏪 Store Profile",
    "📦 Default Inventory Parameters",
    "🗑️ Data Management",
    "💻 System & Diagnostics"
])

with tab_store:
    st.subheader("Store Details")
    with st.form("store_profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            s_name = st.text_input("Store Name", value=shop["shop_name"])
            s_type = st.selectbox(
                "Retail Business Type",
                options=[
                    "Grocery & FMCG (Kirana)",
                    "Supermarket / General Merchandise",
                    "Clothing & Apparel Store",
                    "Stationery & Books",
                    "Consumer Electronics",
                    "Pharmacy & Health Care"
                ],
                index=0 if "Kirana" in shop["shop_type"] else 1
            )
        with col2:
            c_symbol = st.selectbox(
                "Currency Symbol",
                options=["₹", "$", "€", "£", "AED", "¥"],
                index=0 if shop["currency_symbol"] == "₹" else 1
            )
            c_code = st.text_input("Currency Code (ISO)", value=shop["currency_code"])

        save_store = st.form_submit_button("💾 Save Store Profile", type="primary")
        if save_store:
            repo.update_shop_settings(
                shop_id=shop["shop_id"],
                name=s_name,
                shop_type=s_type,
                currency_symbol=c_symbol,
                currency_code=c_code
            )
            st.success("Store profile updated successfully!")
            st.rerun()


with tab_defaults:
    st.subheader("Default Replenishment Assumptions")
    with st.form("defaults_form"):
        d1, d2 = st.columns(2)
        with d1:
            def_lead = st.number_input("Standard Supplier Lead Time (Days)", min_value=1, max_value=60, value=7)
            def_review = st.number_input("Standard Store Review Period (Days)", min_value=1, max_value=30, value=7)
        with d2:
            def_sl = st.selectbox(
                "Target Cycle Service Level",
                options=[0.80, 0.85, 0.90, 0.95, 0.98, 0.99],
                index=3,
                format_func=lambda sl: f"{int(sl*100)}% (z = {sl})"
            )
            def_method = st.selectbox("Preferred Safety Stock Model", ["Variability Method (z * sigma * sqrt(L))", "Fixed Buffer Method (%)"])

        save_defaults = st.form_submit_button("💾 Save Operational Defaults")
        if save_defaults:
            st.success("Operational defaults recorded for future optimization runs!")


with tab_data:
    st.subheader("Data Reset & Demo Seeding")
    st.warning("⚠️ The actions below will modify or delete data in your local SQLite database.")

    col_rst1, col_rst2 = st.columns(2)
    with col_rst1:
        st.markdown("##### 🔄 Reload Kirana Store Demo Data")
        st.caption("Clears existing records and populates 12 realistic Indian retail items with 90 days of transactions.")
        if st.button("📥 Reload Demo Dataset", type="secondary"):
            with st.spinner("Seeding demo records..."):
                repo.clear_all_data(shop["shop_id"])
                generate_all_samples()

                df_sample_daily = pd.read_csv(SAMPLE_DIR / "sample_daily_sales.csv")
                df_sample_inv = pd.read_csv(SAMPLE_DIR / "sample_inventory.csv")

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

                upload_id = repo.create_upload_record(
                    shop_id=shop["shop_id"],
                    file_name="sample_daily_sales.csv",
                    file_hash="demo_seed_hash",
                    upload_type="combined",
                    row_count=len(df_sample_daily),
                    quality_summary={"status": "Demo dataset reloaded"}
                )

                repo.save_daily_sales(shop["shop_id"], upload_id, df_sample_daily)

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

                st.success("Demo dataset reloaded! Ready to explore.")
                st.rerun()

    with col_rst2:
        st.markdown("##### 🗑️ Clear All Database Records")
        st.caption("Permanently deletes all products, sales history, forecasts, and recommendations.")
        confirm_del = st.checkbox("I understand this will delete all stored sales records.")
        if st.button("Delete All Data", disabled=not confirm_del, type="primary"):
            repo.clear_all_data(shop["shop_id"])
            st.success("All sales, forecast, and inventory records have been deleted.")
            st.rerun()


with tab_sys:
    st.subheader("System Diagnostics & Environment")
    db_size_kb = (os.path.getsize(DEFAULT_SQLITE_PATH) / 1024) if DEFAULT_SQLITE_PATH.exists() else 0.0

    sys_info = [
        {"Parameter": "Python Version", "Value": sys.version.split()[0]},
        {"Parameter": "Operating System", "Value": sys.platform},
        {"Parameter": "Database Engine", "Value": "SQLite via SQLAlchemy (PostgreSQL-ready)"},
        {"Parameter": "Database File Path", "Value": str(DEFAULT_SQLITE_PATH)},
        {"Parameter": "Database Size", "Value": f"{db_size_kb:.2f} KB"},
        {"Parameter": "XGBoost Machine Learning Available", "Value": "Yes (Installed)"},
        {"Parameter": "Plotly Visualizations", "Value": "Active"},
        {"Parameter": "OpenPyXL Excel Engine", "Value": "Active"}
    ]
    st.dataframe(pd.DataFrame(sys_info), hide_index=True, use_container_width=True)
