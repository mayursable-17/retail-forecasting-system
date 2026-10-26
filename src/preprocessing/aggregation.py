"""
Daily Sales Aggregation and Time-Series Normalization.
Converts transaction-level records into regular daily time series.
"""

from typing import List, Optional, Tuple, Dict
import pandas as pd
import numpy as np


def aggregate_daily_sales(
    df_clean: pd.DataFrame,
    shop_id: int = 1,
    fill_gaps_with_zeros: bool = True
) -> pd.DataFrame:
    """
    Aggregate transaction records to (shop_id, product_id, sale_date).
    
    Parameters:
    - df_clean: Cleaned transaction DataFrame with 'date', 'product_id', 'quantity', 'revenue'.
    - shop_id: Target shop identifier.
    - fill_gaps_with_zeros: When True, creates explicit zero-sales records for days
      between each product's first active sale date and the global dataset end date.
      
    Returns:
    - DataFrame with columns: [shop_id, product_id, product_name, category, sale_date, quantity_sold, revenue, avg_selling_price]
    """
    if df_clean.empty:
        return pd.DataFrame(columns=[
            "shop_id", "product_id", "product_name", "category", "sale_date",
            "quantity_sold", "revenue", "avg_selling_price"
        ])

    df = df_clean.copy()
    df["sale_date"] = pd.to_datetime(df["date"]).dt.date

    # Group by product_id and sale_date
    grouped = df.groupby(["product_id", "sale_date"]).agg(
        quantity_sold=("quantity", "sum"),
        revenue=("revenue", "sum"),
        product_name=("product_name", "first"),
        category=("category", "first")
    ).reset_index()

    # Product demand cannot be negative in physical inventory replenishment.
    # If net daily sales was negative (more returns than purchases on that day),
    # net demand is set to 0.0, and revenue is floored to 0.0.
    grouped["quantity_sold"] = grouped["quantity_sold"].apply(lambda q: max(0.0, float(q)))
    grouped["revenue"] = grouped["revenue"].apply(lambda r: max(0.0, float(r)))

    # Compute average selling price
    grouped["avg_selling_price"] = np.where(
        grouped["quantity_sold"] > 0,
        grouped["revenue"] / grouped["quantity_sold"],
        0.0
    )
    grouped["shop_id"] = shop_id

    if not fill_gaps_with_zeros:
        return grouped[[
            "shop_id", "product_id", "product_name", "category",
            "sale_date", "quantity_sold", "revenue", "avg_selling_price"
        ]].sort_values(by=["sale_date", "product_id"]).reset_index(drop=True)

    # Smart gap-filling: for each product, create continuous date range from its FIRST sale date to global max date
    global_max_date = grouped["sale_date"].max()
    filled_dfs = []

    for pid, pgroup in grouped.groupby("product_id"):
        pname = pgroup["product_name"].iloc[0]
        cat = pgroup["category"].iloc[0]
        min_date = pgroup["sale_date"].min()

        all_dates = pd.date_range(start=min_date, end=global_max_date, freq="D").date
        date_df = pd.DataFrame({"sale_date": all_dates})
        date_df["product_id"] = pid
        date_df["product_name"] = pname
        date_df["category"] = cat
        date_df["shop_id"] = shop_id

        merged = pd.merge(
            date_df,
            pgroup[["product_id", "sale_date", "quantity_sold", "revenue", "avg_selling_price"]],
            on=["product_id", "sale_date"],
            how="left"
        )
        merged["quantity_sold"] = merged["quantity_sold"].fillna(0.0)
        merged["revenue"] = merged["revenue"].fillna(0.0)
        
        # Forward fill or default ASP
        default_price = pgroup["avg_selling_price"].loc[pgroup["avg_selling_price"] > 0].median()
        if pd.isna(default_price) or default_price <= 0:
            default_price = 10.0
        merged["avg_selling_price"] = merged["avg_selling_price"].fillna(default_price)

        filled_dfs.append(merged)

    if filled_dfs:
        res = pd.concat(filled_dfs, ignore_index=True)
    else:
        res = grouped

    cols = [
        "shop_id", "product_id", "product_name", "category",
        "sale_date", "quantity_sold", "revenue", "avg_selling_price"
    ]
    return res[cols].sort_values(by=["sale_date", "product_id"]).reset_index(drop=True)
