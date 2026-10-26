"""
Page 6: Product & Inventory Management
View catalog, add/update products, enter new stock counts, and inspect historical inventory snapshots.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from datetime import datetime

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop

st.set_page_config(page_title="Product Management - Retail System", page_icon="🏷️", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("🏷️ Product & Inventory Management")
st.markdown("Manage your store's item catalog, update stock counts, and record supplier parameters.")

tab_catalog, tab_stock_update, tab_add_prod, tab_snapshots = st.tabs([
    "📦 Product Catalog",
    "📝 Update Stock & Purchase Orders",
    "➕ Add New Product",
    "📜 Inventory Snapshot History"
])

# 1. Product Catalog Tab
with tab_catalog:
    st.subheader("Current Product Catalog")
    prods_df = repo.get_products_df(shop_id=shop["shop_id"])
    if not prods_df.empty:
        cur = shop["currency_symbol"]
        disp_p = prods_df.copy()
        disp_p["unit_price"] = disp_p["unit_price"].apply(lambda p: f"{cur}{p:,.2f}")
        disp_p.columns = [
            "Product ID", "Product Name", "Category", "Unit Price",
            "Lead Time (Days)", "Min Order Qty (MOQ)", "Case Pack Size", "Active"
        ]
        st.dataframe(disp_p, hide_index=True, use_container_width=True)
    else:
        st.info("No products currently in catalog.")

# 2. Update Stock & Purchase Orders Tab
with tab_stock_update:
    st.subheader("Update Stock Counts & Incoming Orders")
    st.caption("Entering new stock counts creates a new timestamped snapshot. Historical records are preserved.")

    if not prods_df.empty:
        prod_map = {row["product_name"]: row["product_id"] for _, row in prods_df.iterrows()}
        target_prod_name = st.selectbox("Select Product to Update", list(prod_map.keys()), key="stock_prod_select")
        target_pid = prod_map[target_prod_name]

        # Get latest known snapshot
        snaps = repo.get_latest_inventory_snapshots(shop_id=shop["shop_id"])
        curr_snap = snaps[snaps["product_id"] == target_pid] if not snaps.empty else pd.DataFrame()
        
        curr_on_hand = float(curr_snap.iloc[0]["on_hand_qty"]) if not curr_snap.empty else 0.0
        curr_on_order = float(curr_snap.iloc[0]["on_order_qty"]) if not curr_snap.empty else 0.0
        curr_lead = int(curr_snap.iloc[0]["lead_time_days"]) if not curr_snap.empty else 7

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            new_on_hand = st.number_input("Physical On-Hand Stock (Units)", min_value=0.0, value=curr_on_hand, step=1.0)
        with sc2:
            new_on_order = st.number_input("On-Order / Pending Purchase Orders (Units)", min_value=0.0, value=curr_on_order, step=1.0)
        with sc3:
            new_lead = st.number_input("Supplier Lead Time (Days)", min_value=1, max_value=60, value=curr_lead, step=1)

        if st.button("💾 Record Stock Count Snapshot", type="primary"):
            repo.save_inventory_snapshot(
                shop_id=shop["shop_id"],
                snapshots=[{
                    "product_id": target_pid,
                    "on_hand_qty": new_on_hand,
                    "on_order_qty": new_on_order,
                    "backorders": 0.0,
                    "lead_time_days": new_lead
                }]
            )
            st.success(f"Successfully recorded new stock count for {target_prod_name} at {datetime.now().strftime('%H:%M:%S')}!")
    else:
        st.warning("Please add or upload products before updating stock.")

# 3. Add New Product Tab
with tab_add_prod:
    st.subheader("Add a New Product to Catalog")
    with st.form("add_product_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            new_id = st.text_input("Product ID / SKU *", placeholder="e.g. PROD-015")
            new_name = st.text_input("Product Name *", placeholder="e.g. Basmati Rice Premium 1kg")
            new_cat = st.text_input("Category", value="General", placeholder="e.g. Groceries")
            new_price = st.number_input(f"Unit Selling Price ({shop['currency_symbol']})", min_value=0.0, value=50.0, step=1.0)
        with f2:
            new_lead_time = st.number_input("Default Supplier Lead Time (Days)", min_value=1, max_value=60, value=7)
            new_moq = st.number_input("Minimum Order Quantity (MOQ)", min_value=1.0, value=5.0, step=1.0)
            new_pack = st.number_input("Supplier Case Pack Size", min_value=1.0, value=1.0, step=1.0)
            initial_stock = st.number_input("Initial On-Hand Stock (Units)", min_value=0.0, value=10.0, step=1.0)

        submitted = st.form_submit_button("➕ Save Product to Catalog", type="primary")
        if submitted:
            if not new_id.strip() or not new_name.strip():
                st.error("Product ID and Product Name are required fields.")
            else:
                repo.upsert_products(shop["shop_id"], [{
                    "product_id": new_id.strip(),
                    "product_name": new_name.strip(),
                    "category": new_cat.strip(),
                    "unit_price": new_price,
                    "lead_time_days": new_lead_time,
                    "minimum_order_quantity": new_moq,
                    "case_pack_size": new_pack
                }])
                repo.save_inventory_snapshot(shop["shop_id"], [{
                    "product_id": new_id.strip(),
                    "on_hand_qty": initial_stock,
                    "on_order_qty": 0.0,
                    "backorders": 0.0,
                    "lead_time_days": new_lead_time
                }])
                st.success(f"Product '{new_name}' added to catalog with initial stock of {initial_stock} units!")

# 4. Inventory Snapshot History Tab
with tab_snapshots:
    st.subheader("Historical Stock Snapshots")
    snapshots_df = repo.get_latest_inventory_snapshots(shop_id=shop["shop_id"])
    if not snapshots_df.empty:
        disp_snap = snapshots_df.copy()
        disp_snap["snapshot_date"] = pd.to_datetime(disp_snap["snapshot_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        disp_snap.columns = [
            "Product ID", "Product Name", "Category", "On-Hand Stock", "On-Order",
            "Backorders", "Lead Time (Days)", "MOQ", "Case Pack", "Snapshot Timestamp"
        ]
        st.dataframe(disp_snap, hide_index=True, use_container_width=True)
    else:
        st.info("No stock snapshots recorded yet.")
