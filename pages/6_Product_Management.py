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
    st.subheader("Interactive Product Catalog")
    st.caption("You can modify prices, supplier lead times, and packaging parameters directly in the grid below, then click **Save Changes**.")

    prods_df = repo.get_products_df(shop_id=shop["shop_id"])
    if not prods_df.empty:
        cur = shop["currency_symbol"]
        f1, f2 = st.columns([2, 1])
        with f1:
            search_query = st.text_input("🔍 Search Catalog (Name or SKU)", placeholder="Type to filter products...")
        with f2:
            cats = ["All Categories"] + sorted(prods_df["category"].unique())
            cat_choice = st.selectbox("Category Filter", cats)

        view_p = prods_df.copy()
        if search_query:
            q = search_query.lower()
            view_p = view_p[
                view_p["product_name"].str.lower().str.contains(q) |
                view_p["product_id"].str.lower().str.contains(q)
            ]
        if cat_choice != "All Categories":
            view_p = view_p[view_p["category"] == cat_choice]

        edited_catalog = st.data_editor(
            view_p,
            key="catalog_editor",
            column_config={
                "product_id": st.column_config.TextColumn("Product ID / SKU", disabled=True),
                "product_name": st.column_config.TextColumn("Product Name"),
                "category": st.column_config.TextColumn("Category"),
                "unit_price": st.column_config.NumberColumn(f"Unit Price ({cur})", min_value=0.0, step=0.5, format=f"{cur}%.2f"),
                "lead_time_days": st.column_config.NumberColumn("Lead Time (Days)", min_value=1, max_value=60, step=1),
                "minimum_order_quantity": st.column_config.NumberColumn("MOQ", min_value=1.0, step=1.0),
                "case_pack_size": st.column_config.NumberColumn("Case Pack", min_value=1.0, step=1.0),
                "is_active": st.column_config.CheckboxColumn("Active")
            },
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Save Catalog Changes to Database", type="primary"):
            updated_count = repo.batch_update_products(shop["shop_id"], edited_catalog.to_dict(orient="records"))
            st.success(f"Successfully updated {updated_count} product parameter(s) in catalog database!")
            st.rerun()

    else:
        st.info("No products currently in catalog.")

# 2. Update Stock & Purchase Orders Tab
with tab_stock_update:
    st.subheader("Update Stock Counts & Incoming Orders")
    st.caption("Entering new stock counts creates a new timestamped snapshot. Historical records are preserved.")

    if not prods_df.empty:
        stock_mode = st.radio("Update Mode", ["Single Item Quick Update", "Bulk All Products Stock Grid"], horizontal=True)

        if stock_mode == "Single Item Quick Update":
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
                st.rerun()

        else:
            st.markdown("##### Bulk Stock Take / Physical Count Grid")
            latest_snaps = repo.get_latest_inventory_snapshots(shop_id=shop["shop_id"])
            snap_map = {r["product_id"]: r for _, r in latest_snaps.iterrows()} if not latest_snaps.empty else {}

            bulk_rows = []
            for _, p in prods_df.iterrows():
                pid = p["product_id"]
                s_data = snap_map.get(pid, {})
                bulk_rows.append({
                    "product_id": pid,
                    "product_name": p["product_name"],
                    "category": p["category"],
                    "on_hand_qty": float(s_data.get("on_hand_qty", 0.0)),
                    "on_order_qty": float(s_data.get("on_order_qty", 0.0)),
                    "lead_time_days": int(s_data.get("lead_time_days", p.get("lead_time_days", 7)))
                })

            df_bulk = pd.DataFrame(bulk_rows)
            edited_bulk = st.data_editor(
                df_bulk,
                key="bulk_stock_editor",
                column_config={
                    "product_id": st.column_config.TextColumn("Product ID", disabled=True),
                    "product_name": st.column_config.TextColumn("Product Name", disabled=True),
                    "category": st.column_config.TextColumn("Category", disabled=True),
                    "on_hand_qty": st.column_config.NumberColumn("Physical On-Hand (Units)", min_value=0.0, step=1.0),
                    "on_order_qty": st.column_config.NumberColumn("On-Order Pending (Units)", min_value=0.0, step=1.0),
                    "lead_time_days": st.column_config.NumberColumn("Lead Time (Days)", min_value=1, max_value=60, step=1)
                },
                hide_index=True,
                use_container_width=True
            )

            if st.button("💾 Record Complete Inventory Snapshot for All Items", type="primary"):
                snaps_to_save = []
                for _, r in edited_bulk.iterrows():
                    snaps_to_save.append({
                        "product_id": str(r["product_id"]),
                        "on_hand_qty": float(r["on_hand_qty"]),
                        "on_order_qty": float(r["on_order_qty"]),
                        "backorders": 0.0,
                        "lead_time_days": int(r["lead_time_days"])
                    })
                repo.save_inventory_snapshot(shop["shop_id"], snaps_to_save)
                st.success(f"Recorded new complete stock count snapshot for {len(snaps_to_save)} products at {datetime.now().strftime('%H:%M:%S')}!")
                st.rerun()

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
