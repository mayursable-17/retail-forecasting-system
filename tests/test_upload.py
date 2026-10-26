"""
Tests for Data Ingestion, File Reading, and Column Mapping.
"""

import io
import pytest
import pandas as pd

from src.ingestion.file_reader import read_uploaded_file, FileReadError
from src.ingestion.column_mapper import auto_detect_columns, validate_mapping


def test_read_valid_csv():
    csv_bytes = b"Date,Product_ID,Quantity,Revenue\n2026-10-01,P1,5,500.0\n"
    df, meta = read_uploaded_file(csv_bytes, "sales.csv")
    assert len(df) == 1
    assert meta["row_count"] == 1
    assert meta["extension"] == ".csv"
    assert "Date" in df.columns


def test_read_empty_csv():
    with pytest.raises(FileReadError, match="empty"):
        read_uploaded_file(b"", "empty.csv")


def test_unsupported_file_extension():
    with pytest.raises(FileReadError, match="Unsupported file format"):
        read_uploaded_file(b"some content", "data.txt")


def test_read_valid_xlsx():
    df_in = pd.DataFrame({"Date": ["2026-10-01"], "Product": ["P1"], "Qty": [10]})
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df_in.to_excel(writer, sheet_name="Sales", index=False)
    
    df_out, meta = read_uploaded_file(bio.getvalue(), "sales.xlsx", sheet_name="Sales")
    assert len(df_out) == 1
    assert "Date" in df_out.columns


def test_column_auto_detection():
    cols = ["Transaction Date", "Item SKU", "Item Description", "Qty Sold", "Price Each", "Total Amount"]
    mapped = auto_detect_columns(cols)

    assert mapped["date"] == "Transaction Date"
    assert mapped["product_id"] == "Item SKU"
    assert mapped["product_name"] == "Item Description"
    assert mapped["quantity"] == "Qty Sold"
    assert mapped["unit_price"] == "Price Each"
    assert mapped["revenue"] == "Total Amount"


def test_validate_mapping_valid():
    mapping = {
        "date": "Sale Date",
        "product_id": "SKU",
        "product_name": "Name",
        "quantity": "Qty",
        "revenue": "Revenue"
    }
    is_valid, errors = validate_mapping(mapping, upload_type="sales")
    assert is_valid is True
    assert len(errors) == 0


def test_validate_mapping_missing_required():
    mapping = {
        "date": None,
        "product_id": None,
        "quantity": "Qty"
    }
    is_valid, errors = validate_mapping(mapping, upload_type="sales")
    assert is_valid is False
    assert any("Date" in e for e in errors)
    assert any("product identifier" in e for e in errors)
