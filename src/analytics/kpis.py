"""
Sales and Inventory KPI Calculation Engine.
Derives metrics, rankings, seasonal patterns, and aggregations from actual data.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np


def compute_overview_kpis(df_sales_daily: pd.DataFrame) -> Dict[str, Any]:
    """Compute top-level retail KPIs for the Home Dashboard."""
    if df_sales_daily.empty:
        return {
            "total_revenue": 0.0,
            "total_units_sold": 0.0,
            "total_products": 0,
            "avg_daily_revenue": 0.0,
            "total_days": 0,
            "start_date": None,
            "end_date": None,
            "avg_order_value": 0.0
        }

    df = df_sales_daily.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    total_revenue = float(df["revenue"].sum())
    total_units = float(df["quantity_sold"].sum())
    unique_products = int(df["product_id"].nunique())
    unique_days = int(df["sale_date"].dt.date.nunique())

    avg_daily_revenue = (total_revenue / unique_days) if unique_days > 0 else 0.0
    start_date = df["sale_date"].min().strftime("%Y-%m-%d")
    end_date = df["sale_date"].max().strftime("%Y-%m-%d")

    return {
        "total_revenue": round(total_revenue, 2),
        "total_units_sold": round(total_units, 1),
        "total_products": unique_products,
        "avg_daily_revenue": round(avg_daily_revenue, 2),
        "total_days": unique_days,
        "start_date": start_date,
        "end_date": end_date
    }


def get_top_and_bottom_products(
    df_sales_daily: pd.DataFrame,
    top_n: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return top-performing and lowest-performing products by total revenue and units."""
    if df_sales_daily.empty:
        empty_df = pd.DataFrame(columns=["product_id", "product_name", "category", "quantity_sold", "revenue"])
        return empty_df, empty_df

    agg = df_sales_daily.groupby(["product_id", "product_name", "category"]).agg(
        quantity_sold=("quantity_sold", "sum"),
        revenue=("revenue", "sum")
    ).reset_index()

    top_products = agg.sort_values(by="revenue", ascending=False).head(top_n).reset_index(drop=True)
    bottom_products = agg.sort_values(by="revenue", ascending=True).head(top_n).reset_index(drop=True)

    return top_products, bottom_products


def compute_category_breakdown(df_sales_daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total sales, units, and percentage contribution by category."""
    if df_sales_daily.empty:
        return pd.DataFrame(columns=["category", "quantity_sold", "revenue", "revenue_share_pct"])

    cat_df = df_sales_daily.groupby("category").agg(
        quantity_sold=("quantity_sold", "sum"),
        revenue=("revenue", "sum")
    ).reset_index()

    total_rev = cat_df["revenue"].sum()
    if total_rev > 0:
        cat_df["revenue_share_pct"] = (cat_df["revenue"] / total_rev * 100).round(2)
    else:
        cat_df["revenue_share_pct"] = 0.0

    return cat_df.sort_values(by="revenue", ascending=False).reset_index(drop=True)


def compute_weekday_weekend_stats(df_sales_daily: pd.DataFrame) -> pd.DataFrame:
    """Analyze sales differences between weekdays and weekends."""
    if df_sales_daily.empty:
        return pd.DataFrame(columns=["day_type", "avg_daily_revenue", "avg_daily_units"])

    df = df_sales_daily.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    
    # Aggregate to store daily totals first
    daily_store = df.groupby(df["sale_date"].dt.date).agg(
        total_rev=("revenue", "sum"),
        total_units=("quantity_sold", "sum")
    ).reset_index()
    daily_store["day_type"] = pd.to_datetime(daily_store["sale_date"]).dt.dayofweek.apply(
        lambda d: "Weekend (Sat-Sun)" if d in [5, 6] else "Weekday (Mon-Fri)"
    )

    stats = daily_store.groupby("day_type").agg(
        avg_daily_revenue=("total_rev", "mean"),
        avg_daily_units=("total_units", "mean"),
        day_count=("total_rev", "count")
    ).reset_index()

    stats["avg_daily_revenue"] = stats["avg_daily_revenue"].round(2)
    stats["avg_daily_units"] = stats["avg_daily_units"].round(1)

    return stats
