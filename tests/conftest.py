"""
Pytest Fixtures and Test Configurations.
Provides in-memory SQLite databases and standard test dataframes.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.database.models import Base
from src.database.connection import get_engine, init_db
from src.database.repository import Repository


@pytest.fixture
def in_memory_repo(tmp_path):
    """Provides a fresh isolated SQLite database repository for each test."""
    db_file = tmp_path / "test_retail.db"
    test_db_url = f"sqlite:///{db_file.as_posix()}"
    engine = get_engine(test_db_url)
    init_db(engine)
    repo = Repository(test_db_url)
    return repo


@pytest.fixture
def sample_sales_raw_df():
    """Generates a small test transaction dataframe."""
    return pd.DataFrame([
        {"Sale Date": "2026-10-01", "Item Code": "P1", "Item Name": "Atta 5kg", "Dept": "Groceries", "Qty": 4, "Price": 200.0, "Revenue": 800.0},
        {"Sale Date": "2026-10-01", "Item Code": "P2", "Item Name": "Oil 1L", "Dept": "Groceries", "Qty": 2, "Price": 150.0, "Revenue": 300.0},
        {"Sale Date": "2026-10-02", "Item Code": "P1", "Item Name": "Atta 5kg", "Dept": "Groceries", "Qty": 6, "Price": 200.0, "Revenue": 1200.0},
        {"Sale Date": "2026-10-02", "Item Code": "P2", "Item Name": "Oil 1L", "Dept": "Groceries", "Qty": 3, "Price": 150.0, "Revenue": 450.0},
    ])


@pytest.fixture
def sample_daily_series():
    """Generates 45 days of daily sales series for a product."""
    np.random.seed(42)
    start = datetime(2026, 8, 1)
    dates = [start + timedelta(days=i) for i in range(45)]
    qtys = [max(0.0, float(np.random.poisson(10))) for _ in range(45)]
    revs = [q * 100.0 for q in qtys]

    return pd.DataFrame({
        "sale_date": dates,
        "product_id": "P1",
        "product_name": "Atta 5kg",
        "category": "Groceries",
        "quantity_sold": qtys,
        "revenue": revs
    })
