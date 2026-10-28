"""
SQLAlchemy ORM Models for Retail Inventory & Forecasting System.
Supports SQLite out-of-the-box, compatible with PostgreSQL.
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean,
    ForeignKey, UniqueConstraint, Index, Text, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)


class Shop(Base):
    __tablename__ = "shops"

    shop_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_name = Column(String(150), nullable=False, default="Kirana & Retail Hub")
    shop_type = Column(String(80), nullable=False, default="General Store / Supermarket")
    currency_symbol = Column(String(10), nullable=False, default="₹")
    currency_code = Column(String(10), nullable=False, default="INR")
    default_lead_time_days = Column(Integer, nullable=False, default=7)
    default_review_period_days = Column(Integer, nullable=False, default=7)
    default_service_level = Column(Float, nullable=False, default=0.95)
    default_safety_stock_method = Column(String(50), nullable=False, default="variability")
    default_replenishment_buffer_pct = Column(Float, nullable=False, default=0.20)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="shop", cascade="all, delete-orphan")
    sales_daily = relationship("SaleDaily", back_populates="shop", cascade="all, delete-orphan")
    forecast_runs = relationship("ForecastRun", back_populates="shop", cascade="all, delete-orphan")
    inventory_snapshots = relationship("InventorySnapshot", back_populates="shop", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(100), primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.shop_id"), nullable=False, default=1)
    sku = Column(String(100), nullable=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="General")
    unit_price = Column(Float, nullable=False, default=0.0)
    lead_time_days = Column(Integer, nullable=False, default=7)
    minimum_order_quantity = Column(Float, nullable=False, default=1.0)
    case_pack_size = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    shop = relationship("Shop", back_populates="products")
    sales_daily = relationship("SaleDaily", back_populates="product", cascade="all, delete-orphan")
    snapshots = relationship("InventorySnapshot", back_populates="product", cascade="all, delete-orphan")
    forecast_results = relationship("ForecastResult", back_populates="product", cascade="all, delete-orphan")
    recommendations = relationship("ReorderRecommendation", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_product_shop_cat", "shop_id", "category"),
    )


class Upload(Base):
    __tablename__ = "uploads"

    upload_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.shop_id"), nullable=False, default=1)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=True)
    upload_type = Column(String(50), nullable=False, default="sales")  # sales, inventory, combined
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)
    status = Column(String(50), nullable=False, default="completed")  # completed, failed, partial
    row_count = Column(Integer, nullable=False, default=0)
    quality_summary = Column(JSON, nullable=True)

    shop = relationship("Shop", back_populates="uploads")
    sales_daily = relationship("SaleDaily", back_populates="upload")
    forecast_runs = relationship("ForecastRun", back_populates="upload")


class SaleDaily(Base):
    __tablename__ = "sales_daily"

    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.shop_id"), nullable=False, default=1)
    product_id = Column(String(100), ForeignKey("products.product_id"), nullable=False)
    sale_date = Column(Date, nullable=False)
    quantity_sold = Column(Float, nullable=False, default=0.0)
    revenue = Column(Float, nullable=False, default=0.0)
    upload_id = Column(Integer, ForeignKey("uploads.upload_id"), nullable=True)

    shop = relationship("Shop", back_populates="sales_daily")
    product = relationship("Product", back_populates="sales_daily")
    upload = relationship("Upload", back_populates="sales_daily")

    __table_args__ = (
        UniqueConstraint("shop_id", "product_id", "sale_date", name="uq_shop_product_date"),
        Index("idx_sales_date", "sale_date"),
        Index("idx_sales_shop_prod", "shop_id", "product_id"),
    )


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.shop_id"), nullable=False, default=1)
    product_id = Column(String(100), ForeignKey("products.product_id"), nullable=False)
    snapshot_date = Column(DateTime, default=utc_now, nullable=False)
    on_hand_qty = Column(Float, nullable=False, default=0.0)
    on_order_qty = Column(Float, nullable=False, default=0.0)
    backorders = Column(Float, nullable=False, default=0.0)
    lead_time_days = Column(Integer, nullable=False, default=7)

    shop = relationship("Shop", back_populates="inventory_snapshots")
    product = relationship("Product", back_populates="snapshots")

    __table_args__ = (
        Index("idx_snapshot_lookup", "shop_id", "product_id", "snapshot_date"),
    )


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.shop_id"), nullable=False, default=1)
    upload_id = Column(Integer, ForeignKey("uploads.upload_id"), nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False, default="1.0.0")
    horizon_days = Column(Integer, nullable=False, default=15)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    validation_metrics = Column(JSON, nullable=True)  # {mae, rmse, wape, bias}
    configuration = Column(JSON, nullable=True)

    shop = relationship("Shop", back_populates="forecast_runs")
    upload = relationship("Upload", back_populates="forecast_runs")
    results = relationship("ForecastResult", back_populates="run", cascade="all, delete-orphan")
    recommendations = relationship("ReorderRecommendation", back_populates="run", cascade="all, delete-orphan")


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("forecast_runs.run_id"), nullable=False)
    product_id = Column(String(100), ForeignKey("products.product_id"), nullable=False)
    forecast_date = Column(Date, nullable=False)
    predicted_demand = Column(Float, nullable=False, default=0.0)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)

    run = relationship("ForecastRun", back_populates="results")
    product = relationship("Product", back_populates="forecast_results")

    __table_args__ = (
        Index("idx_forecast_run_prod", "run_id", "product_id"),
        Index("idx_forecast_date", "forecast_date"),
    )


class ReorderRecommendation(Base):
    __tablename__ = "reorder_recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("forecast_runs.run_id"), nullable=False)
    product_id = Column(String(100), ForeignKey("products.product_id"), nullable=False)
    current_stock = Column(Float, nullable=True)
    inventory_position = Column(Float, nullable=True)
    reorder_point = Column(Float, nullable=True)
    safety_stock = Column(Float, nullable=True)
    expected_lead_time_demand = Column(Float, nullable=True)
    order_up_to_target = Column(Float, nullable=True)
    suggested_qty = Column(Float, nullable=False, default=0.0)
    risk_status = Column(String(50), nullable=False)  # Reorder Review, Stock Risk, Adequate Stock, Potential Excess Stock, Insufficient Inventory Information
    inventory_mode = Column(String(20), nullable=False)  # estimated_mode, inventory_mode
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("ForecastRun", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")

    __table_args__ = (
        Index("idx_rec_run_status", "run_id", "risk_status"),
    )
