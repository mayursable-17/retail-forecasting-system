"""
Tests for Daily Sales Aggregation and Time-Series Normalization.
"""

import pytest
import pandas as pd
from datetime import date
from src.preprocessing.aggregation import aggregate_daily_sales


def test_aggregate_daily_sales_basic():
    df_clean = pd.DataFrame([
        {"date": "2026-10-01", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": 3, "revenue": 60.0},
        {"date": "2026-10-01", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": 2, "revenue": 40.0},
        {"date": "2026-10-02", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": 4, "revenue": 80.0},
    ])

    agg = aggregate_daily_sales(df_clean, shop_id=1, fill_gaps_with_zeros=False)
    assert len(agg) == 2
    row1 = agg[agg["sale_date"] == date(2026, 10, 1)].iloc[0]
    assert row1["quantity_sold"] == 5.0
    assert row1["revenue"] == 100.0
    assert row1["avg_selling_price"] == 20.0


def test_net_demand_non_negativity_with_excess_returns():
    # If customer returns (-5) exceed purchases (+2) on a single day
    df_clean = pd.DataFrame([
        {"date": "2026-10-01", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": 2, "revenue": 40.0},
        {"date": "2026-10-01", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": -5, "revenue": -100.0},
    ])
    agg = aggregate_daily_sales(df_clean, shop_id=1, fill_gaps_with_zeros=False)
    assert len(agg) == 1
    # Physical daily demand must be clipped to >= 0
    assert agg.iloc[0]["quantity_sold"] == 0.0
    assert agg.iloc[0]["revenue"] == 0.0


def test_gap_filling_creates_zero_sales():
    df_clean = pd.DataFrame([
        {"date": "2026-10-01", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": 5, "revenue": 100.0},
        # Gap on 2026-10-02
        {"date": "2026-10-03", "product_id": "P1", "product_name": "Item A", "category": "Groceries", "quantity": 8, "revenue": 160.0},
    ])
    agg = aggregate_daily_sales(df_clean, shop_id=1, fill_gaps_with_zeros=True)
    # Should have 3 consecutive dates: Oct 1, Oct 2, Oct 3
    assert len(agg) == 3
    gap_row = agg[agg["sale_date"] == date(2026, 10, 2)].iloc[0]
    assert gap_row["quantity_sold"] == 0.0
    assert gap_row["revenue"] == 0.0
