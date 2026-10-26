"""
Tests for Data Cleaning, Anomaly Handling, and Quality Audit Reporting.
"""

import pytest
import pandas as pd
import numpy as np

from src.preprocessing.cleaning import DataCleaner


def test_clean_missing_and_unparseable_dates():
    df_raw = pd.DataFrame([
        {"Date": "2026-10-01", "Product": "P1", "Quantity": 5, "Price": 10.0, "Revenue": 50.0},
        {"Date": "", "Product": "P1", "Quantity": 2, "Price": 10.0, "Revenue": 20.0},  # Missing
        {"Date": "NOT_A_DATE", "Product": "P1", "Quantity": 3, "Price": 10.0, "Revenue": 30.0},  # Invalid
        {"Date": "2026-10-02", "Product": "P1", "Quantity": 4, "Price": 10.0, "Revenue": 40.0},
    ])
    mapping = {"date": "Date", "product_id": "Product", "quantity": "Quantity", "unit_price": "Price", "revenue": "Revenue"}
    cleaner = DataCleaner(mapping)
    clean_df, report = cleaner.clean_sales_data(df_raw)

    assert len(clean_df) == 2
    assert report["missing_dates"] == 1
    assert report["excluded_rows"] == 2


def test_clean_negative_quantities_as_returns():
    df_raw = pd.DataFrame([
        {"Date": "2026-10-01", "Product": "P1", "Quantity": 10, "Price": 20.0, "Revenue": 200.0},
        {"Date": "2026-10-01", "Product": "P1", "Quantity": -2, "Price": 20.0, "Revenue": -40.0}, # Return
    ])
    mapping = {"date": "Date", "product_id": "Product", "quantity": "Quantity", "unit_price": "Price", "revenue": "Revenue"}
    
    # 1. Allow returns
    cleaner = DataCleaner(mapping)
    clean_df, report = cleaner.clean_sales_data(df_raw, allow_returns=True)
    assert len(clean_df) == 2
    assert report["negative_quantities"] == 1
    assert report["returns_policy"] == "Retained as Net Returns"

    # 2. Disallow returns
    cleaner2 = DataCleaner(mapping)
    clean_df2, report2 = cleaner2.clean_sales_data(df_raw, allow_returns=False)
    assert len(clean_df2) == 1
    assert report2["excluded_rows"] == 1


def test_clean_duplicate_transactions():
    df_raw = pd.DataFrame([
        {"Date": "2026-10-01", "Product": "P1", "Quantity": 5, "Price": 20.0, "Revenue": 100.0},
        {"Date": "2026-10-01", "Product": "P1", "Quantity": 5, "Price": 20.0, "Revenue": 100.0}, # Exact duplicate
    ])
    mapping = {"date": "Date", "product_id": "Product", "quantity": "Quantity", "unit_price": "Price", "revenue": "Revenue"}
    cleaner = DataCleaner(mapping)
    clean_df, report = cleaner.clean_sales_data(df_raw)

    assert len(clean_df) == 1
    assert report["duplicate_records"] == 1


def test_impute_missing_quantity_and_revenue():
    df_raw = pd.DataFrame([
        {"Date": "2026-10-01", "Product": "P1", "Quantity": None, "Price": 50.0, "Revenue": 250.0}, # Qty should be 5
        {"Date": "2026-10-02", "Product": "P1", "Quantity": 4, "Price": 50.0, "Revenue": None},      # Rev should be 200
    ])
    mapping = {"date": "Date", "product_id": "Product", "quantity": "Quantity", "unit_price": "Price", "revenue": "Revenue"}
    cleaner = DataCleaner(mapping)
    clean_df, report = cleaner.clean_sales_data(df_raw)

    assert len(clean_df) == 2
    assert clean_df.iloc[0]["quantity"] == 5.0
    assert clean_df.iloc[1]["revenue"] == 200.0
    assert report["imputed_quantities"] == 1
    assert report["imputed_revenues"] == 1
