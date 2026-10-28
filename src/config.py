"""
System Configuration & Constants
Retail Sales Forecasting & Inventory Optimization System
"""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IS_VERCEL = bool(os.getenv("VERCEL"))

if IS_VERCEL:
    TMP_DIR = Path("/tmp")
    DB_DIR = TMP_DIR / "db"
    DATA_DIR = TMP_DIR / "data"
    SAMPLE_DIR = DATA_DIR / "sample"
    TEMPLATE_DIR = DATA_DIR / "templates"
    try:
        for d in [DB_DIR, SAMPLE_DIR, TEMPLATE_DIR]:
            d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    DEFAULT_SQLITE_PATH = DB_DIR / "retail_inventory.db"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")
else:
    DATA_DIR = PROJECT_ROOT / "data"
    SAMPLE_DIR = DATA_DIR / "sample"
    TEMPLATE_DIR = DATA_DIR / "templates"
    DB_DIR = PROJECT_ROOT / "db"
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    DEFAULT_SQLITE_PATH = DB_DIR / "retail_inventory.db"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")

# Default Business Settings
DEFAULT_CURRENCY = "₹"
DEFAULT_CURRENCY_CODE = "INR"
DEFAULT_FORECAST_HORIZON_DAYS = 15
ALLOWED_HORIZONS = [7, 15, 30]

DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_REVIEW_PERIOD_DAYS = 7
DEFAULT_SERVICE_LEVEL = 0.95  # 95% service level -> z ~ 1.645

# Service Level to Z-score mapping (Standard Normal Distribution)
SERVICE_LEVEL_Z_MAP = {
    0.80: 0.84,
    0.85: 1.04,
    0.90: 1.28,
    0.95: 1.645,
    0.98: 2.05,
    0.99: 2.33,
}

# Upload Limits
MAX_UPLOAD_SIZE_MB = 25
ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls"]

# Column mapping standard targets
STANDARD_COLUMNS = {
    "date": ["date", "sale_date", "order_date", "transaction_date", "invoice_date", "bill_date", "timestamp"],
    "product_id": ["product_id", "item_id", "sku", "item_code", "product_code", "barcode", "code"],
    "product_name": ["product_name", "product", "item", "item_name", "description", "title", "product_title"],
    "category": ["category", "product_category", "item_category", "dept", "department", "group"],
    "quantity": ["quantity", "qty", "units_sold", "sales_quantity", "volume", "sold_qty", "count"],
    "unit_price": ["unit_price", "price", "selling_price", "rate", "mrp", "item_price", "unit_cost"],
    "revenue": ["revenue", "sales_amount", "total_sales", "amount", "total_amount", "sales", "net_amount"],
    "stock": ["stock", "current_stock", "inventory_level", "stock_available", "on_hand", "quantity_on_hand", "qty_on_hand"],
    "on_order": ["on_order", "pending_stock", "units_on_order", "incoming_stock", "qty_on_order"],
    "lead_time": ["lead_time", "supplier_lead_time", "delivery_days", "lead_time_days"],
    "min_order_qty": ["moq", "minimum_order_quantity", "min_order_qty", "min_order"],
    "case_pack": ["case_pack", "case_pack_size", "pack_size", "batch_size"]
}
