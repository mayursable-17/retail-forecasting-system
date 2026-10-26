"""
Data Repository: safe abstraction for CRUD and analytical queries.
Uses SQLAlchemy parameterization and session contexts.
"""

from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from src.database.models import (
    Shop, Product, Upload, SaleDaily,
    InventorySnapshot, ForecastRun, ForecastResult, ReorderRecommendation
)
from src.database.connection import get_db_context


class Repository:
    def __init__(self, db_url: str = None):
        self.db_url = db_url

    def get_shop(self, shop_id: int = 1) -> Optional[Dict[str, Any]]:
        with get_db_context(self.db_url) as session:
            shop = session.query(Shop).filter(Shop.shop_id == shop_id).first()
            if not shop:
                return None
            return {
                "shop_id": shop.shop_id,
                "shop_name": shop.shop_name,
                "shop_type": shop.shop_type,
                "currency_symbol": shop.currency_symbol,
                "currency_code": shop.currency_code,
                "created_at": shop.created_at
            }

    def update_shop_settings(self, shop_id: int, name: str, shop_type: str, currency_symbol: str, currency_code: str):
        with get_db_context(self.db_url) as session:
            shop = session.query(Shop).filter(Shop.shop_id == shop_id).first()
            if shop:
                shop.shop_name = name
                shop.shop_type = shop_type
                shop.currency_symbol = currency_symbol
                shop.currency_code = currency_code
                return True
            return False

    def upsert_products(self, shop_id: int, products_data: List[Dict[str, Any]]):
        """Insert or update products."""
        with get_db_context(self.db_url) as session:
            for item in products_data:
                pid = str(item["product_id"])
                existing = session.query(Product).filter(
                    Product.shop_id == shop_id,
                    Product.product_id == pid
                ).first()
                if existing:
                    existing.product_name = item.get("product_name", existing.product_name)
                    existing.category = item.get("category", existing.category)
                    existing.unit_price = float(item.get("unit_price", existing.unit_price))
                    if "lead_time_days" in item and item["lead_time_days"] is not None:
                        existing.lead_time_days = int(item["lead_time_days"])
                    if "minimum_order_quantity" in item and item["minimum_order_quantity"] is not None:
                        existing.minimum_order_quantity = float(item["minimum_order_quantity"])
                    if "case_pack_size" in item and item["case_pack_size"] is not None:
                        existing.case_pack_size = float(item["case_pack_size"])
                else:
                    new_prod = Product(
                        product_id=pid,
                        shop_id=shop_id,
                        sku=item.get("sku", pid),
                        product_name=item.get("product_name", pid),
                        category=item.get("category", "General"),
                        unit_price=float(item.get("unit_price", 0.0)),
                        lead_time_days=int(item.get("lead_time_days", 7)),
                        minimum_order_quantity=float(item.get("minimum_order_quantity", 1.0)),
                        case_pack_size=float(item.get("case_pack_size", 1.0)),
                        is_active=True
                    )
                    session.add(new_prod)

    def get_products_df(self, shop_id: int = 1) -> pd.DataFrame:
        with get_db_context(self.db_url) as session:
            products = session.query(Product).filter(Product.shop_id == shop_id).all()
            if not products:
                return pd.DataFrame()
            return pd.DataFrame([
                {
                    "product_id": p.product_id,
                    "product_name": p.product_name,
                    "category": p.category,
                    "unit_price": p.unit_price,
                    "lead_time_days": p.lead_time_days,
                    "minimum_order_quantity": p.minimum_order_quantity,
                    "case_pack_size": p.case_pack_size,
                    "is_active": p.is_active
                }
                for p in products
            ])

    def create_upload_record(self, shop_id: int, file_name: str, file_hash: str,
                             upload_type: str, row_count: int, quality_summary: dict) -> int:
        with get_db_context(self.db_url) as session:
            upload = Upload(
                shop_id=shop_id,
                file_name=file_name,
                file_hash=file_hash,
                upload_type=upload_type,
                row_count=row_count,
                quality_summary=quality_summary,
                status="completed"
            )
            session.add(upload)
            session.flush()
            return upload.upload_id

    def get_upload_history(self, shop_id: int = 1) -> pd.DataFrame:
        with get_db_context(self.db_url) as session:
            uploads = session.query(Upload).filter(Upload.shop_id == shop_id).order_by(desc(Upload.uploaded_at)).all()
            if not uploads:
                return pd.DataFrame()
            return pd.DataFrame([
                {
                    "upload_id": u.upload_id,
                    "file_name": u.file_name,
                    "upload_type": u.upload_type,
                    "uploaded_at": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "row_count": u.row_count,
                    "status": u.status
                }
                for u in uploads
            ])

    def save_daily_sales(self, shop_id: int, upload_id: int, df_daily: pd.DataFrame):
        """
        Upsert daily sales records.
        df_daily must have columns: product_id, sale_date, quantity_sold, revenue
        """
        if df_daily.empty:
            return 0

        with get_db_context(self.db_url) as session:
            count = 0
            for _, row in df_daily.iterrows():
                dt = pd.to_datetime(row["sale_date"]).date()
                pid = str(row["product_id"])
                qty = float(row["quantity_sold"])
                rev = float(row["revenue"])

                existing = session.query(SaleDaily).filter(
                    SaleDaily.shop_id == shop_id,
                    SaleDaily.product_id == pid,
                    SaleDaily.sale_date == dt
                ).first()

                if existing:
                    existing.quantity_sold = qty
                    existing.revenue = rev
                    existing.upload_id = upload_id
                else:
                    new_sale = SaleDaily(
                        shop_id=shop_id,
                        product_id=pid,
                        sale_date=dt,
                        quantity_sold=qty,
                        revenue=rev,
                        upload_id=upload_id
                    )
                    session.add(new_sale)
                count += 1
            return count

    def get_daily_sales_df(self, shop_id: int = 1, product_ids: List[str] = None,
                           start_date: date = None, end_date: date = None) -> pd.DataFrame:
        """Fetch daily sales merged with product metadata."""
        with get_db_context(self.db_url) as session:
            q = session.query(
                SaleDaily.sale_date,
                SaleDaily.product_id,
                Product.product_name,
                Product.category,
                SaleDaily.quantity_sold,
                SaleDaily.revenue
            ).join(
                Product,
                (SaleDaily.product_id == Product.product_id) & (SaleDaily.shop_id == Product.shop_id)
            ).filter(SaleDaily.shop_id == shop_id)

            if product_ids:
                q = q.filter(SaleDaily.product_id.in_(product_ids))
            if start_date:
                q = q.filter(SaleDaily.sale_date >= start_date)
            if end_date:
                q = q.filter(SaleDaily.sale_date <= end_date)

            q = q.order_by(SaleDaily.sale_date.asc(), SaleDaily.product_id.asc())
            rows = q.all()

            if not rows:
                return pd.DataFrame(columns=["sale_date", "product_id", "product_name", "category", "quantity_sold", "revenue"])

            return pd.DataFrame([
                {
                    "sale_date": pd.to_datetime(r[0]),
                    "product_id": r[1],
                    "product_name": r[2],
                    "category": r[3],
                    "quantity_sold": r[4],
                    "revenue": r[5]
                }
                for r in rows
            ])

    def save_inventory_snapshot(self, shop_id: int, snapshots: List[Dict[str, Any]]):
        with get_db_context(self.db_url) as session:
            now = datetime.now(timezone.utc)
            for s in snapshots:
                snap = InventorySnapshot(
                    shop_id=shop_id,
                    product_id=str(s["product_id"]),
                    snapshot_date=now,
                    on_hand_qty=float(s.get("on_hand_qty", 0.0)),
                    on_order_qty=float(s.get("on_order_qty", 0.0)),
                    backorders=float(s.get("backorders", 0.0)),
                    lead_time_days=int(s.get("lead_time_days", 7))
                )
                session.add(snap)

    def get_latest_inventory_snapshots(self, shop_id: int = 1) -> pd.DataFrame:
        """Fetch latest snapshot per product."""
        with get_db_context(self.db_url) as session:
            subquery = session.query(
                InventorySnapshot.product_id,
                func.max(InventorySnapshot.snapshot_date).label("max_date")
            ).filter(InventorySnapshot.shop_id == shop_id).group_by(InventorySnapshot.product_id).subquery()

            q = session.query(
                InventorySnapshot.product_id,
                Product.product_name,
                Product.category,
                InventorySnapshot.on_hand_qty,
                InventorySnapshot.on_order_qty,
                InventorySnapshot.backorders,
                InventorySnapshot.lead_time_days,
                Product.minimum_order_quantity,
                Product.case_pack_size,
                InventorySnapshot.snapshot_date
            ).join(
                subquery,
                (InventorySnapshot.product_id == subquery.c.product_id) &
                (InventorySnapshot.snapshot_date == subquery.c.max_date)
            ).join(
                Product,
                (InventorySnapshot.product_id == Product.product_id) &
                (InventorySnapshot.shop_id == Product.shop_id)
            ).filter(InventorySnapshot.shop_id == shop_id)

            rows = q.all()
            if not rows:
                return pd.DataFrame()

            return pd.DataFrame([
                {
                    "product_id": r[0],
                    "product_name": r[1],
                    "category": r[2],
                    "on_hand_qty": r[3],
                    "on_order_qty": r[4],
                    "backorders": r[5],
                    "lead_time_days": r[6],
                    "minimum_order_quantity": r[7],
                    "case_pack_size": r[8],
                    "snapshot_date": r[9]
                }
                for r in rows
            ])

    def save_forecast_run(self, shop_id: int, model_name: str, horizon_days: int,
                          validation_metrics: dict, config: dict,
                          forecast_rows: List[Dict[str, Any]], upload_id: int = None) -> int:
        with get_db_context(self.db_url) as session:
            run = ForecastRun(
                shop_id=shop_id,
                upload_id=upload_id,
                model_name=model_name,
                model_version="1.0.0",
                horizon_days=horizon_days,
                created_at=datetime.now(timezone.utc),
                validation_metrics=validation_metrics,
                configuration=config
            )
            session.add(run)
            session.flush()

            for fr in forecast_rows:
                dt = pd.to_datetime(fr["forecast_date"]).date()
                res = ForecastResult(
                    run_id=run.run_id,
                    product_id=str(fr["product_id"]),
                    forecast_date=dt,
                    predicted_demand=float(fr["predicted_demand"]),
                    lower_bound=float(fr.get("lower_bound", 0.0)),
                    upper_bound=float(fr.get("upper_bound", 0.0))
                )
                session.add(res)

            return run.run_id

    def get_latest_forecast_run(self, shop_id: int = 1) -> Optional[Dict[str, Any]]:
        with get_db_context(self.db_url) as session:
            run = session.query(ForecastRun).filter(ForecastRun.shop_id == shop_id).order_by(desc(ForecastRun.created_at)).first()
            if not run:
                return None
            return {
                "run_id": run.run_id,
                "model_name": run.model_name,
                "model_version": run.model_version,
                "horizon_days": run.horizon_days,
                "created_at": run.created_at,
                "validation_metrics": run.validation_metrics,
                "configuration": run.configuration
            }

    def get_forecast_results_df(self, run_id: int) -> pd.DataFrame:
        with get_db_context(self.db_url) as session:
            rows = session.query(
                ForecastResult.forecast_date,
                ForecastResult.product_id,
                Product.product_name,
                Product.category,
                ForecastResult.predicted_demand,
                ForecastResult.lower_bound,
                ForecastResult.upper_bound
            ).join(
                Product,
                ForecastResult.product_id == Product.product_id
            ).filter(ForecastResult.run_id == run_id).order_by(ForecastResult.forecast_date.asc()).all()

            if not rows:
                return pd.DataFrame()

            return pd.DataFrame([
                {
                    "forecast_date": pd.to_datetime(r[0]),
                    "product_id": r[1],
                    "product_name": r[2],
                    "category": r[3],
                    "predicted_demand": r[4],
                    "lower_bound": r[5],
                    "upper_bound": r[6]
                }
                for r in rows
            ])

    def save_recommendations(self, run_id: int, recommendations: List[Dict[str, Any]]):
        with get_db_context(self.db_url) as session:
            # Delete old recommendations for this run if any
            session.query(ReorderRecommendation).filter(ReorderRecommendation.run_id == run_id).delete()
            for rec in recommendations:
                r = ReorderRecommendation(
                    run_id=run_id,
                    product_id=str(rec["product_id"]),
                    current_stock=rec.get("current_stock"),
                    inventory_position=rec.get("inventory_position"),
                    reorder_point=rec.get("reorder_point"),
                    safety_stock=rec.get("safety_stock"),
                    expected_lead_time_demand=rec.get("expected_lead_time_demand"),
                    order_up_to_target=rec.get("order_up_to_target"),
                    suggested_qty=float(rec.get("suggested_qty", 0.0)),
                    risk_status=rec.get("risk_status", "Insufficient Inventory Information"),
                    inventory_mode=rec.get("inventory_mode", "estimated_mode"),
                    explanation=rec.get("explanation", ""),
                    created_at=datetime.now(timezone.utc)
                )
                session.add(r)

    def get_recommendations_df(self, run_id: int) -> pd.DataFrame:
        with get_db_context(self.db_url) as session:
            rows = session.query(
                ReorderRecommendation.recommendation_id,
                ReorderRecommendation.product_id,
                Product.product_name,
                Product.category,
                ReorderRecommendation.current_stock,
                ReorderRecommendation.inventory_position,
                ReorderRecommendation.reorder_point,
                ReorderRecommendation.safety_stock,
                ReorderRecommendation.expected_lead_time_demand,
                ReorderRecommendation.order_up_to_target,
                ReorderRecommendation.suggested_qty,
                ReorderRecommendation.risk_status,
                ReorderRecommendation.inventory_mode,
                ReorderRecommendation.explanation,
                ReorderRecommendation.created_at
            ).join(
                Product,
                ReorderRecommendation.product_id == Product.product_id
            ).filter(ReorderRecommendation.run_id == run_id).all()

            if not rows:
                return pd.DataFrame()

            return pd.DataFrame([
                {
                    "recommendation_id": r[0],
                    "product_id": r[1],
                    "product_name": r[2],
                    "category": r[3],
                    "current_stock": r[4],
                    "inventory_position": r[5],
                    "reorder_point": r[6],
                    "safety_stock": r[7],
                    "expected_lead_time_demand": r[8],
                    "order_up_to_target": r[9],
                    "suggested_qty": r[10],
                    "risk_status": r[11],
                    "inventory_mode": r[12],
                    "explanation": r[13],
                    "created_at": r[14]
                }
                for r in rows
            ])

    def clear_all_data(self, shop_id: int = 1):
        with get_db_context(self.db_url) as session:
            session.query(ReorderRecommendation).delete()
            session.query(ForecastResult).delete()
            session.query(ForecastRun).filter(ForecastRun.shop_id == shop_id).delete()
            session.query(InventorySnapshot).filter(InventorySnapshot.shop_id == shop_id).delete()
            session.query(SaleDaily).filter(SaleDaily.shop_id == shop_id).delete()
            session.query(Upload).filter(Upload.shop_id == shop_id).delete()
            session.query(Product).filter(Product.shop_id == shop_id).delete()
