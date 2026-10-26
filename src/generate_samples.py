"""
Realistic Synthetic Retail Dataset Generator.
Generates Indian retail / Kirana sample datasets and templates with reproducible patterns.
"""

from datetime import datetime, timedelta
import random
import os
import pandas as pd
import numpy as np
import openpyxl

from src.config import SAMPLE_DIR, TEMPLATE_DIR


def generate_all_samples():
    random.seed(42)
    np.random.seed(42)

    # 1. Product Catalog Definitions
    products = [
        {"id": "PROD-001", "name": "Aashirvaad Atta 5kg", "cat": "Groceries", "price": 245.0, "base_d": 12, "lead": 4, "moq": 10, "pack": 5, "stock": 18, "order": 0},
        {"id": "PROD-002", "name": "Fortune Sunflower Oil 1L", "cat": "Groceries", "price": 140.0, "base_d": 15, "lead": 5, "moq": 15, "pack": 6, "stock": 8, "order": 12},
        {"id": "PROD-003", "name": "Tata Salt 1kg", "cat": "Groceries", "price": 28.0, "base_d": 20, "lead": 3, "moq": 25, "pack": 10, "stock": 45, "order": 0},
        {"id": "PROD-004", "name": "Amul Butter 500g", "cat": "Dairy & Breakfast", "price": 275.0, "base_d": 8, "lead": 2, "moq": 6, "pack": 4, "stock": 4, "order": 0}, # low stock risk
        {"id": "PROD-005", "name": "Mother Dairy Toned Milk 1L", "cat": "Dairy & Breakfast", "price": 54.0, "base_d": 35, "lead": 1, "moq": 20, "pack": 10, "stock": 40, "order": 20},
        {"id": "PROD-006", "name": "Maggi 2-Minute Noodles 280g", "cat": "Snacks & Instant Food", "price": 50.0, "base_d": 25, "lead": 4, "moq": 20, "pack": 12, "stock": 15, "order": 24},
        {"id": "PROD-007", "name": "Britannia Good Day Biscuits", "cat": "Snacks & Instant Food", "price": 30.0, "base_d": 18, "lead": 3, "moq": 24, "pack": 12, "stock": 80, "order": 0}, # excess
        {"id": "PROD-008", "name": "Taj Mahal Tea 500g", "cat": "Beverages", "price": 380.0, "base_d": 6, "lead": 6, "moq": 5, "pack": 4, "stock": 2, "order": 0}, # reorder review
        {"id": "PROD-009", "name": "Surf Excel Matic Powder 1kg", "cat": "Personal & Home Care", "price": 210.0, "base_d": 7, "lead": 7, "moq": 8, "pack": 4, "stock": 10, "order": 0},
        {"id": "PROD-010", "name": "Dettol Antiseptic Liquid 250ml", "cat": "Personal & Home Care", "price": 125.0, "base_d": 5, "lead": 5, "moq": 6, "pack": 6, "stock": 0, "order": 0}, # stockout risk
        {"id": "PROD-011", "name": "Classmate Notebook 172 Pgs", "cat": "Stationery", "price": 60.0, "base_d": 10, "lead": 5, "moq": 10, "pack": 5, "stock": 25, "order": 0},
        {"id": "PROD-012", "name": "Cello Butterflow Pen Blue", "cat": "Stationery", "price": 10.0, "base_d": 30, "lead": 4, "moq": 50, "pack": 20, "stock": 35, "order": 40}
    ]

    # Generate 90 days of history
    end_date = datetime.now().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=89)

    transactions = []
    daily_sales = []
    trans_id = 10001

    curr_date = start_date
    while curr_date <= end_date:
        is_weekend = curr_date.weekday() in [5, 6]
        weekend_mult = 1.35 if is_weekend else 1.0

        for p in products:
            # Poisson distribution with weekend uplift
            expected = p["base_d"] * weekend_mult
            daily_qty = int(np.random.poisson(expected))
            daily_rev = round(daily_qty * p["price"], 2)

            daily_sales.append({
                "sale_date": curr_date.strftime("%Y-%m-%d"),
                "product_id": p["id"],
                "product_name": p["name"],
                "category": p["cat"],
                "quantity_sold": daily_qty,
                "revenue": daily_rev
            })

            # Break into 1-4 individual customer transactions if daily_qty > 0
            if daily_qty > 0:
                remaining_qty = daily_qty
                while remaining_qty > 0:
                    cust_qty = min(remaining_qty, random.choice([1, 1, 2, 2, 3, 4]))
                    remaining_qty -= cust_qty
                    transactions.append({
                        "transaction_id": f"TXN-{trans_id}",
                        "date": curr_date.strftime("%Y-%m-%d"),
                        "product_id": p["id"],
                        "product_name": p["name"],
                        "category": p["cat"],
                        "quantity": cust_qty,
                        "unit_price": p["price"],
                        "total_amount": round(cust_qty * p["price"], 2)
                    })
                    trans_id += 1

        curr_date += timedelta(days=1)

    # 1. Save Transaction CSV
    df_trans = pd.DataFrame(transactions)
    df_trans.to_csv(SAMPLE_DIR / "sample_transactions.csv", index=False)

    # 2. Save Daily Aggregated CSV
    df_daily = pd.DataFrame(daily_sales)
    df_daily.to_csv(SAMPLE_DIR / "sample_daily_sales.csv", index=False)

    # 3. Save Inventory Snapshot CSV
    inventory_rows = [
        {
            "product_id": p["id"],
            "product_name": p["name"],
            "category": p["cat"],
            "current_stock": p["stock"],
            "on_order": p["order"],
            "lead_time_days": p["lead"],
            "min_order_qty": p["moq"],
            "case_pack_size": p["pack"]
        }
        for p in products
    ]
    df_inv = pd.DataFrame(inventory_rows)
    df_inv.to_csv(SAMPLE_DIR / "sample_inventory.csv", index=False)

    # 4. Save Multi-sheet Excel workbook
    excel_path = SAMPLE_DIR / "sample_retail_store.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_trans.to_excel(writer, sheet_name="Sales Transactions", index=False)
        df_inv.to_excel(writer, sheet_name="Current Inventory", index=False)

    # 5. Save Deliberately Messy Sales Dataset (for demonstration of Data Quality cleaning engine)
    messy_rows = []
    # Pick a subset of 100 rows from df_trans
    for i, r in enumerate(df_trans.head(120).to_dict(orient="records")):
        row = {
            "Sale Date": r["date"],
            "Item SKU": r["product_id"],
            "Item Description": r["product_name"],
            "Dept": r["category"],
            "Qty Sold": r["quantity"],
            "Price": r["unit_price"],
            "Sales Revenue": r["total_amount"]
        }
        # Inject deliberate anomalies
        if i == 5:
            row["Sale Date"] = ""  # Missing date
        elif i == 12:
            row["Sale Date"] = "INVALID_DATE"  # Unparseable date
        elif i == 18:
            row["Item SKU"] = None  # Missing product ID
            row["Item Description"] = None
        elif i == 25:
            row["Qty Sold"] = -2  # Documented customer return
            row["Sales Revenue"] = -2 * r["unit_price"]
        elif i == 33:
            row["Price"] = -50.0  # Invalid negative price
        elif i == 40 or i == 41:
            # Exact duplicate record
            row["Sale Date"] = "2026-08-15"
            row["Item SKU"] = "PROD-001"
            row["Qty Sold"] = 5
            row["Price"] = 245.0
            row["Sales Revenue"] = 1225.0
        elif i == 50:
            row["Qty Sold"] = None  # Missing quantity (can be imputed from revenue / price)
        elif i == 60:
            row["Sales Revenue"] = None  # Missing revenue (can be calculated from qty * price)

        messy_rows.append(row)

    df_messy = pd.DataFrame(messy_rows)
    df_messy.to_csv(SAMPLE_DIR / "messy_sales_data.csv", index=False)

    # 6. Templates
    sales_template = pd.DataFrame([
        {"Date": "2026-10-01", "Product_ID": "SKU-101", "Product_Name": "Basmati Rice 1kg", "Category": "Groceries", "Quantity": 5, "Unit_Price": 120.0, "Revenue": 600.0},
        {"Date": "2026-10-01", "Product_ID": "SKU-102", "Product_Name": "Sunflower Oil 1L", "Category": "Groceries", "Quantity": 3, "Unit_Price": 145.0, "Revenue": 435.0},
        {"Date": "2026-10-02", "Product_ID": "SKU-101", "Product_Name": "Basmati Rice 1kg", "Category": "Groceries", "Quantity": 7, "Unit_Price": 120.0, "Revenue": 840.0}
    ])
    sales_template.to_csv(TEMPLATE_DIR / "sales_template.csv", index=False)

    inv_template = pd.DataFrame([
        {"Product_ID": "SKU-101", "Product_Name": "Basmati Rice 1kg", "Category": "Groceries", "Current_Stock": 25, "On_Order": 10, "Lead_Time_Days": 5, "Min_Order_Qty": 10, "Case_Pack_Size": 5},
        {"Product_ID": "SKU-102", "Product_Name": "Sunflower Oil 1L", "Category": "Groceries", "Current_Stock": 12, "On_Order": 0, "Lead_Time_Days": 7, "Min_Order_Qty": 15, "Case_Pack_Size": 6}
    ])
    inv_template.to_csv(TEMPLATE_DIR / "inventory_template.csv", index=False)

    print("Synthetic datasets and templates created successfully!")


if __name__ == "__main__":
    generate_all_samples()
