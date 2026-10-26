"""
Page 1: Data Ingestion & Automatic Column Mapping
Supports CSV and XLSX uploads, sheet selection, column mapping, and sample templates.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop
from src.ingestion.file_reader import read_uploaded_file, get_excel_sheet_names, FileReadError
from src.ingestion.column_mapper import auto_detect_columns, validate_mapping
from src.preprocessing.cleaning import DataCleaner
from src.preprocessing.aggregation import aggregate_daily_sales
from src.config import SAMPLE_DIR, TEMPLATE_DIR, STANDARD_COLUMNS

st.set_page_config(page_title="Upload Data - Retail System", page_icon="📤", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("📤 Upload Retail Datasets")
st.markdown("Upload your store's sales records and inventory levels in **CSV** or **Excel (.xlsx, .xls)** formats.")

# Workflow tabs
tab_upload, tab_templates, tab_history = st.tabs(["📁 File Ingestion", "📋 Download Templates & Samples", "📜 Upload History"])

with tab_upload:
    u_col1, u_col2 = st.columns([2, 1])
    with u_col1:
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Files up to 25MB are accepted. Macros and embedded scripts are safely ignored."
        )
    with u_col2:
        dataset_type = st.radio(
            "Dataset Content Type",
            options=["Sales Records", "Inventory Snapshot"],
            help="Select whether this spreadsheet contains sales transaction history or current stock levels."
        )
        allow_returns = st.checkbox(
            "Interpret negative quantities as customer returns",
            value=True,
            help="If checked, negative numbers will deduct from daily net demand rather than being dropped."
        )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        is_excel = file_name.lower().endswith((".xlsx", ".xls"))
        selected_sheet = None

        if is_excel:
            try:
                sheet_names = get_excel_sheet_names(file_bytes)
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("Select Excel Worksheet to Import", sheet_names)
                else:
                    selected_sheet = sheet_names[0]
            except Exception as e:
                st.error(f"Error inspecting Excel worksheets: {str(e)}")

        # Read the file safely
        try:
            raw_df, meta = read_uploaded_file(file_bytes, file_name, sheet_name=selected_sheet)
            st.success(f"Successfully read **{file_name}** ({meta['row_count']} rows, {meta['column_count']} columns).")
        except FileReadError as fre:
            st.error(f"File Read Error: {str(fre)}")
            st.stop()
        except Exception as e:
            st.error(f"Unexpected parsing error: {str(e)}")
            st.stop()

        # Data Preview
        with st.expander("👀 Raw Data Preview (First 10 Rows)", expanded=True):
            st.dataframe(raw_df.head(10), use_container_width=True)

        st.markdown("---")
        st.subheader("🗺️ Column Mapping & Verification")
        st.caption(
            "The system automatically detected column matches based on standard retail synonyms. "
            "Please confirm or adjust mappings below before processing."
        )

        detected_map = auto_detect_columns(list(raw_df.columns))
        actual_cols_options = ["-- None / Not Present --"] + list(raw_df.columns)

        # Mapping form
        confirmed_mapping = {}

        if dataset_type == "Sales Records":
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                st.markdown("##### 📅 Transaction Info")
                def_date = detected_map.get("date")
                idx_date = actual_cols_options.index(def_date) if def_date in actual_cols_options else 0
                confirmed_mapping["date"] = st.selectbox("Date * (Mandatory)", actual_cols_options, index=idx_date)

                def_rev = detected_map.get("revenue")
                idx_rev = actual_cols_options.index(def_rev) if def_rev in actual_cols_options else 0
                confirmed_mapping["revenue"] = st.selectbox("Total Revenue / Sales Amount", actual_cols_options, index=idx_rev)

            with mcol2:
                st.markdown("##### 📦 Product Identification")
                def_pid = detected_map.get("product_id")
                idx_pid = actual_cols_options.index(def_pid) if def_pid in actual_cols_options else 0
                confirmed_mapping["product_id"] = st.selectbox("Product ID / SKU *", actual_cols_options, index=idx_pid)

                def_pname = detected_map.get("product_name")
                idx_pname = actual_cols_options.index(def_pname) if def_pname in actual_cols_options else 0
                confirmed_mapping["product_name"] = st.selectbox("Product / Item Name", actual_cols_options, index=idx_pname)

                def_cat = detected_map.get("category")
                idx_cat = actual_cols_options.index(def_cat) if def_cat in actual_cols_options else 0
                confirmed_mapping["category"] = st.selectbox("Category / Department", actual_cols_options, index=idx_cat)

            with mcol3:
                st.markdown("##### 🔢 Units & Pricing")
                def_qty = detected_map.get("quantity")
                idx_qty = actual_cols_options.index(def_qty) if def_qty in actual_cols_options else 0
                confirmed_mapping["quantity"] = st.selectbox("Quantity Sold *", actual_cols_options, index=idx_qty)

                def_price = detected_map.get("unit_price")
                idx_price = actual_cols_options.index(def_price) if def_price in actual_cols_options else 0
                confirmed_mapping["unit_price"] = st.selectbox("Unit Selling Price", actual_cols_options, index=idx_price)

        else: # Inventory Snapshot
            mcol1, mcol2 = st.columns(2)
            with mcol1:
                st.markdown("##### 📦 Product Details")
                def_pid = detected_map.get("product_id")
                idx_pid = actual_cols_options.index(def_pid) if def_pid in actual_cols_options else 0
                confirmed_mapping["product_id"] = st.selectbox("Product ID / SKU *", actual_cols_options, index=idx_pid)

                def_pname = detected_map.get("product_name")
                idx_pname = actual_cols_options.index(def_pname) if def_pname in actual_cols_options else 0
                confirmed_mapping["product_name"] = st.selectbox("Product Name", actual_cols_options, index=idx_pname)

                def_cat = detected_map.get("category")
                idx_cat = actual_cols_options.index(def_cat) if def_cat in actual_cols_options else 0
                confirmed_mapping["category"] = st.selectbox("Category", actual_cols_options, index=idx_cat)

            with mcol2:
                st.markdown("##### 📊 Stock & Parameters")
                def_stock = detected_map.get("stock")
                idx_stock = actual_cols_options.index(def_stock) if def_stock in actual_cols_options else 0
                confirmed_mapping["stock"] = st.selectbox("Current Stock on Hand *", actual_cols_options, index=idx_stock)

                def_order = detected_map.get("on_order")
                idx_order = actual_cols_options.index(def_order) if def_order in actual_cols_options else 0
                confirmed_mapping["on_order"] = st.selectbox("Pending / On-Order Units", actual_cols_options, index=idx_order)

                def_lead = detected_map.get("lead_time")
                idx_lead = actual_cols_options.index(def_lead) if def_lead in actual_cols_options else 0
                confirmed_mapping["lead_time"] = st.selectbox("Supplier Lead Time (Days)", actual_cols_options, index=idx_lead)

                def_moq = detected_map.get("min_order_qty")
                idx_moq = actual_cols_options.index(def_moq) if def_moq in actual_cols_options else 0
                confirmed_mapping["min_order_qty"] = st.selectbox("Min Order Quantity (MOQ)", actual_cols_options, index=idx_moq)

                def_pack = detected_map.get("case_pack")
                idx_pack = actual_cols_options.index(def_pack) if def_pack in actual_cols_options else 0
                confirmed_mapping["case_pack"] = st.selectbox("Case Pack Size", actual_cols_options, index=idx_pack)

        # Normalize None
        clean_mapping = {
            k: (v if v != "-- None / Not Present --" else None)
            for k, v in confirmed_mapping.items()
        }

        # Validation check
        req_type = "sales" if dataset_type == "Sales Records" else "inventory"
        is_valid, validation_errors = validate_mapping(clean_mapping, upload_type=req_type)

        if not is_valid:
            for err in validation_errors:
                st.warning(f"⚠️ {err}")
        else:
            st.success("✅ Column mappings are complete and valid!")

            if st.button("🚀 Process, Clean & Save Dataset", type="primary", use_container_width=True):
                with st.spinner("Executing cleaning pipeline and database normalization..."):
                    cleaner = DataCleaner(clean_mapping)

                    if req_type == "sales":
                        cleaned_df, quality_report = cleaner.clean_sales_data(raw_df, allow_returns=allow_returns)

                        # Aggregate to daily
                        df_daily = aggregate_daily_sales(cleaned_df, shop_id=shop["shop_id"], fill_gaps_with_zeros=True)

                        # Build product metadata to upsert
                        prods_to_upsert = []
                        for pid, pgroup in cleaned_df.groupby("product_id"):
                            pname = pgroup["product_name"].iloc[0] if "product_name" in pgroup else pid
                            cat = pgroup["category"].iloc[0] if "category" in pgroup else "General"
                            med_price = pgroup["unit_price"].loc[pgroup["unit_price"] > 0].median()
                            if pd.isna(med_price) or med_price <= 0:
                                med_price = 10.0
                            prods_to_upsert.append({
                                "product_id": str(pid),
                                "product_name": str(pname),
                                "category": str(cat),
                                "unit_price": float(med_price),
                                "lead_time_days": 7,
                                "minimum_order_quantity": 1.0,
                                "case_pack_size": 1.0
                            })
                        repo.upsert_products(shop["shop_id"], prods_to_upsert)

                        # Record upload
                        upload_id = repo.create_upload_record(
                            shop_id=shop["shop_id"],
                            file_name=file_name,
                            file_hash=meta["file_hash"],
                            upload_type="sales",
                            row_count=len(raw_df),
                            quality_summary=quality_report
                        )

                        # Save daily sales
                        rows_saved = repo.save_daily_sales(shop["shop_id"], upload_id, df_daily)

                        # Cache latest quality report in session state
                        st.session_state["latest_quality_report"] = quality_report
                        st.session_state["latest_cleaned_df"] = cleaned_df
                        st.session_state["latest_raw_df"] = raw_df

                        st.success(
                            f"🎉 Ingestion Complete! Cleaned {len(cleaned_df)} transactions and generated "
                            f"{rows_saved} normalized daily sales records for {len(prods_to_upsert)} products."
                        )
                        st.page_link("pages/2_Data_Quality.py", label="➡️ View Detailed Data Quality Audit Report", icon="🔍")

                    else:
                        # Clean inventory snapshot
                        cleaned_inv, inv_report = cleaner.clean_inventory_data(raw_df)

                        prods_to_upsert = []
                        snapshots = []
                        for _, row in cleaned_inv.iterrows():
                            pid = str(row["product_id"])
                            pname = str(row.get("product_name", pid))
                            cat = str(row.get("category", "General"))
                            lead = int(row.get("lead_time", 7))
                            moq = float(row.get("min_order_qty", 1.0))
                            pack = float(row.get("case_pack", 1.0))

                            prods_to_upsert.append({
                                "product_id": pid,
                                "product_name": pname,
                                "category": cat,
                                "unit_price": 0.0,
                                "lead_time_days": lead,
                                "minimum_order_quantity": moq,
                                "case_pack_size": pack
                            })
                            snapshots.append({
                                "product_id": pid,
                                "on_hand_qty": float(row.get("stock", 0.0)),
                                "on_order_qty": float(row.get("on_order", 0.0)),
                                "backorders": 0.0,
                                "lead_time_days": lead
                            })

                        repo.upsert_products(shop["shop_id"], prods_to_upsert)
                        repo.save_inventory_snapshot(shop["shop_id"], snapshots)

                        upload_id = repo.create_upload_record(
                            shop_id=shop["shop_id"],
                            file_name=file_name,
                            file_hash=meta["file_hash"],
                            upload_type="inventory",
                            row_count=len(raw_df),
                            quality_summary=inv_report
                        )
                        st.success(f"🎉 Inventory snapshot saved for {len(snapshots)} products!")
                        st.page_link("pages/5_Inventory_Optimization.py", label="➡️ Proceed to Inventory Optimization (Mode B)", icon="📦")


with tab_templates:
    st.subheader("📋 Sample Datasets & Ready-to-Use Templates")
    st.write("Download these files to test different scenarios and format your own spreadsheets.")

    t1, t2 = st.columns(2)
    with t1:
        st.markdown("##### 📄 Empty Formatting Templates")
        with open(TEMPLATE_DIR / "sales_template.csv", "rb") as f:
            st.download_button(
                "📥 Download Sales Template (CSV)",
                data=f.read(),
                file_name="sales_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        with open(TEMPLATE_DIR / "inventory_template.csv", "rb") as f:
            st.download_button(
                "📥 Download Inventory Template (CSV)",
                data=f.read(),
                file_name="inventory_template.csv",
                mime="text/csv",
                use_container_width=True
            )

    with t2:
        st.markdown("##### 📊 Pre-built Test Datasets")
        with open(SAMPLE_DIR / "sample_transactions.csv", "rb") as f:
            st.download_button(
                "📥 Download 90-Day Transactions CSV",
                data=f.read(),
                file_name="sample_transactions.csv",
                mime="text/csv",
                use_container_width=True
            )
        with open(SAMPLE_DIR / "messy_sales_data.csv", "rb") as f:
            st.download_button(
                "📥 Download Messy Dataset (For Cleaning Demo)",
                data=f.read(),
                file_name="messy_sales_data.csv",
                mime="text/csv",
                use_container_width=True
            )
        with open(SAMPLE_DIR / "sample_retail_store.xlsx", "rb") as f:
            st.download_button(
                "📥 Download Complete Multi-Sheet Excel Workbook",
                data=f.read(),
                file_name="sample_retail_store.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


with tab_history:
    st.subheader("📜 Upload History")
    history_df = repo.get_upload_history(shop_id=shop["shop_id"])
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("No uploads recorded yet for this store.")
