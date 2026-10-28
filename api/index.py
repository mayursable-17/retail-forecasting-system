"""
FastAPI Full-Stack Application for Retail Forecasting & Inventory Optimization System.
Entry point for local execution and Vercel Serverless Function deployment.
"""

import sys
import os
import io
import json
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request, UploadFile, File, Form, Query, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import (
    DEFAULT_CURRENCY, DEFAULT_CURRENCY_CODE, ALLOWED_HORIZONS,
    SERVICE_LEVEL_Z_MAP, SAMPLE_DIR, TEMPLATE_DIR
)
from src.database.connection import init_db
from src.database.repository import Repository
from src.analytics.kpis import (
    compute_overview_kpis, get_top_and_bottom_products,
    compute_category_breakdown, compute_weekday_weekend_stats
)
from src.forecasting.train import DemandModelTrainer
from src.forecasting.predict import generate_future_forecast
from src.inventory.recommendations import (
    generate_mode_a_recommendations, generate_mode_b_recommendations
)
from src.ingestion.file_reader import read_uploaded_file, get_excel_sheet_names, FileReadError
from src.ingestion.column_mapper import auto_detect_columns, validate_mapping
from src.preprocessing.cleaning import DataCleaner
from src.preprocessing.aggregation import aggregate_daily_sales
from src.generate_samples import generate_all_samples
from src.exports.excel_report import generate_retail_master_excel, convert_df_to_csv_bytes

import pandas as pd
import numpy as np

app = FastAPI(
    title="Retail Sales Forecasting & Inventory System",
    description="Intelligent Demand Prediction & Supply Chain Optimization for Small Retailers",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_repo() -> Repository:
    init_db()
    repo = Repository()
    # Check if DB is empty; if so, seed demo data automatically for smooth first-time experience
    shop = repo.get_shop(1)
    if shop:
        sales = repo.get_daily_sales_df(1)
        if sales.empty:
            try:
                seed_kirana_demo(repo, 1)
            except Exception:
                pass
    return repo


def seed_kirana_demo(repo: Repository, shop_id: int = 1):
    """Seed synthetic Kirana retail data."""
    if not (SAMPLE_DIR / "sample_daily_sales.csv").exists():
        generate_all_samples()

    df_sample_daily = pd.read_csv(SAMPLE_DIR / "sample_daily_sales.csv")
    df_sample_inv = pd.read_csv(SAMPLE_DIR / "sample_inventory.csv")

    prods_data = []
    for _, r in df_sample_inv.iterrows():
        prods_data.append({
            "product_id": str(r["product_id"]),
            "product_name": str(r["product_name"]),
            "category": str(r["category"]),
            "unit_price": float(df_sample_daily[df_sample_daily["product_id"] == r["product_id"]]["revenue"].sum() /
                                max(1, df_sample_daily[df_sample_daily["product_id"] == r["product_id"]]["quantity_sold"].sum())),
            "lead_time_days": int(r["lead_time_days"]),
            "minimum_order_quantity": float(r["min_order_qty"]),
            "case_pack_size": float(r["case_pack_size"])
        })
    repo.upsert_products(shop_id, prods_data)

    upload_id = repo.create_upload_record(
        shop_id=shop_id,
        file_name="sample_daily_sales.csv",
        file_hash="demo_hash",
        upload_type="combined",
        row_count=len(df_sample_daily),
        quality_summary={
            "initial_rows": len(df_sample_daily),
            "accepted_rows": len(df_sample_daily),
            "flagged_rows": 0,
            "excluded_rows": 0,
            "missing_dates": 0,
            "missing_products": 0,
            "duplicate_records": 0,
            "negative_quantities": 0,
            "negative_prices": 0,
            "imputed_quantities": 0,
            "imputed_revenues": 0,
            "imputed_prices": 0,
            "returns_policy": "Retained as Net Returns",
            "cleaning_actions": [
                "Demo dataset loaded with 12 staple grocery products.",
                "Generated 90 days of synthetic daily sales records."
            ]
        }
    )

    repo.save_daily_sales(shop_id, upload_id, df_sample_daily)

    inv_snapshots = []
    for _, r in df_sample_inv.iterrows():
        inv_snapshots.append({
            "product_id": str(r["product_id"]),
            "on_hand_qty": float(r["current_stock"]),
            "on_order_qty": float(r["on_order"]),
            "backorders": 0.0,
            "lead_time_days": int(r["lead_time_days"])
        })
    repo.save_inventory_snapshot(shop_id, inv_snapshots)


# ---------------- API ROUTES ----------------

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "retail-forecasting-api", "version": "2.0.0"}


@app.get("/api/shop")
def get_shop_info():
    repo = get_repo()
    shop = repo.get_shop(1)
    if not shop:
        shop = {
            "shop_id": 1,
            "shop_name": "Kirana & Retail Hub",
            "shop_type": "Grocery & FMCG Retail",
            "currency_symbol": DEFAULT_CURRENCY,
            "currency_code": DEFAULT_CURRENCY_CODE,
            "default_lead_time_days": 7,
            "default_review_period_days": 7,
            "default_service_level": 0.95,
            "default_safety_stock_method": "variability",
            "default_replenishment_buffer_pct": 0.20
        }
    return shop


class ShopProfileUpdate(BaseModel):
    shop_name: str
    shop_type: str
    currency_symbol: str
    currency_code: str


@app.post("/api/shop")
def update_shop_profile(data: ShopProfileUpdate):
    repo = get_repo()
    success = repo.update_shop_settings(1, data.shop_name, data.shop_type, data.currency_symbol, data.currency_code)
    return {"success": success}


class OperationalDefaultsUpdate(BaseModel):
    lead_time_days: int
    review_period_days: int
    service_level: float
    safety_stock_method: str
    replenishment_buffer_pct: float


@app.post("/api/shop/defaults")
def update_operational_defaults(data: OperationalDefaultsUpdate):
    repo = get_repo()
    success = repo.update_shop_operational_defaults(
        1, data.lead_time_days, data.review_period_days,
        data.service_level, data.safety_stock_method, data.replenishment_buffer_pct
    )
    return {"success": success}


@app.get("/api/dashboard")
def get_dashboard_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    categories: Optional[str] = None
):
    repo = get_repo()
    shop = repo.get_shop(1) or {}
    cur = shop.get("currency_symbol", "₹")

    sales_df = repo.get_daily_sales_df(1)
    if sales_df.empty:
        return {
            "has_data": False,
            "shop": shop,
            "alerts": {"stock_risk": 0, "reorder_review": 0, "total_items": 0}
        }

    # Date filter
    filtered_df = sales_df.copy()
    filtered_df["dt"] = pd.to_datetime(filtered_df["sale_date"]).dt.date

    if start_date:
        s_d = pd.to_datetime(start_date).date()
        filtered_df = filtered_df[filtered_df["dt"] >= s_d]
    if end_date:
        e_d = pd.to_datetime(end_date).date()
        filtered_df = filtered_df[filtered_df["dt"] <= e_d]

    # Category filter
    all_categories = sorted(sales_df["category"].unique().tolist())
    if categories:
        cat_list = [c.strip() for c in categories.split(",") if c.strip()]
        if cat_list:
            filtered_df = filtered_df[filtered_df["category"].isin(cat_list)]

    kpis = compute_overview_kpis(filtered_df)
    alerts = repo.get_stock_alerts_summary(1)

    # Calculate period growth
    daily_rev = filtered_df.groupby("dt")["revenue"].sum().sort_index()
    if len(daily_rev) >= 4:
        half_pt = len(daily_rev) // 2
        rev_first = daily_rev.iloc[:half_pt].mean()
        rev_second = daily_rev.iloc[half_pt:].mean()
        growth_pct = round(((rev_second - rev_first) / rev_first * 100.0), 1) if rev_first > 0 else 0.0
    else:
        growth_pct = 0.0

    # Daily revenue trend
    daily_trend = filtered_df.groupby("dt").agg(
        revenue=("revenue", "sum"),
        units=("quantity_sold", "sum")
    ).reset_index()
    daily_trend["rolling_7_rev"] = daily_trend["revenue"].rolling(7, min_periods=1).mean().round(2)
    daily_trend["rolling_7_units"] = daily_trend["units"].rolling(7, min_periods=1).mean().round(1)
    daily_trend["date_str"] = daily_trend["dt"].astype(str)

    # Category breakdown
    cat_df = compute_category_breakdown(filtered_df)

    # Day of week stats
    day_stats = compute_weekday_weekend_stats(filtered_df)

    # Top & Bottom products
    top_p, bot_p = get_top_and_bottom_products(filtered_df, top_n=5)
    tot_rev = max(1.0, float(filtered_df["revenue"].sum()))
    if not top_p.empty:
        top_p["share_pct"] = (top_p["revenue"] / tot_rev * 100).round(1)
    if not bot_p.empty:
        bot_p["share_pct"] = (bot_p["revenue"] / tot_rev * 100).round(1)

    min_date_str = str(sales_df["sale_date"].min().date())
    max_date_str = str(sales_df["sale_date"].max().date())

    return {
        "has_data": True,
        "shop": shop,
        "kpis": kpis,
        "growth_pct": growth_pct,
        "alerts": alerts,
        "all_categories": all_categories,
        "date_bounds": {"min_date": min_date_str, "max_date": max_date_str},
        "daily_trend": daily_trend.to_dict(orient="records"),
        "category_breakdown": cat_df.to_dict(orient="records"),
        "day_stats": day_stats.to_dict(orient="records"),
        "top_products": top_p.to_dict(orient="records") if not top_p.empty else [],
        "bottom_products": bot_p.to_dict(orient="records") if not bot_p.empty else []
    }


@app.get("/api/analytics")
def get_analytics_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    categories: Optional[str] = None,
    products: Optional[str] = None
):
    repo = get_repo()
    sales_df = repo.get_daily_sales_df(1)
    if sales_df.empty:
        return {"has_data": False}

    df = sales_df.copy()
    df["dt"] = pd.to_datetime(df["sale_date"]).dt.date

    if start_date:
        df = df[df["dt"] >= pd.to_datetime(start_date).date()]
    if end_date:
        df = df[df["dt"] <= pd.to_datetime(end_date).date()]
    if categories:
        cat_list = [c.strip() for c in categories.split(",") if c.strip()]
        if cat_list:
            df = df[df["category"].isin(cat_list)]
    if products:
        prod_list = [p.strip() for p in products.split(",") if p.strip()]
        if prod_list:
            df = df[df["product_name"].isin(prod_list)]

    if df.empty:
        return {"has_data": True, "is_empty": True}

    # Summary numbers
    f_rev = float(df["revenue"].sum())
    f_units = float(df["quantity_sold"].sum())
    f_days = int(df["dt"].nunique())
    f_asp = round((f_rev / f_units), 2) if f_units > 0 else 0.0

    # Pareto ABC
    prod_agg = df.groupby(["product_id", "product_name", "category"]).agg(
        revenue=("revenue", "sum"),
        units=("quantity_sold", "sum")
    ).reset_index().sort_values(by="revenue", ascending=False).reset_index(drop=True)

    tot_rev = max(1.0, float(prod_agg["revenue"].sum()))
    prod_agg["cum_revenue"] = prod_agg["revenue"].cumsum()
    prod_agg["cum_share_pct"] = (prod_agg["cum_revenue"] / tot_rev * 100).round(2)

    def get_abc(row):
        if row["cum_share_pct"] <= 80.0 or row.name == 0:
            return "Class A (Top 80%)"
        elif row["cum_share_pct"] <= 95.0:
            return "Class B (Next 15%)"
        else:
            return "Class C (Bottom 5%)"

    prod_agg["abc_class"] = prod_agg.apply(get_abc, axis=1)

    # Monthly performance
    df["year_month"] = pd.to_datetime(df["sale_date"]).dt.to_period("M").astype(str)
    monthly_agg = df.groupby("year_month").agg(
        total_rev=("revenue", "sum"),
        total_units=("quantity_sold", "sum"),
        active_days=("dt", "nunique")
    ).reset_index()
    monthly_agg["avg_daily_rev"] = (monthly_agg["total_rev"] / monthly_agg["active_days"]).round(2)

    # Day of week breakdown
    df["dow_num"] = pd.to_datetime(df["sale_date"]).dt.dayofweek
    df["dow_name"] = pd.to_datetime(df["sale_date"]).dt.day_name()
    dow_df = df.groupby(["dow_num", "dow_name"]).agg(
        total_rev=("revenue", "sum"),
        total_units=("quantity_sold", "sum"),
        day_count=("dt", "nunique")
    ).reset_index().sort_values(by="dow_num")
    dow_df["avg_rev"] = (dow_df["total_rev"] / dow_df["day_count"]).round(2)
    dow_df["avg_units"] = (dow_df["total_units"] / dow_df["day_count"]).round(1)

    # Heatmap category x day
    heat_pivot = df.pivot_table(index="category", columns="dow_name", values="revenue", aggfunc="mean").fillna(0).round(2)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    avail_days = [d for d in day_order if d in heat_pivot.columns]
    heat_pivot = heat_pivot[avail_days]

    heatmap_data = {
        "categories": heat_pivot.index.tolist(),
        "days": avail_days,
        "values": heat_pivot.values.tolist()
    }

    return {
        "has_data": True,
        "is_empty": False,
        "summary": {
            "revenue": round(f_rev, 2),
            "units": round(f_units, 1),
            "asp": f_asp,
            "active_days": f_days
        },
        "pareto_products": prod_agg.to_dict(orient="records"),
        "monthly_agg": monthly_agg.to_dict(orient="records"),
        "dow_stats": dow_df.to_dict(orient="records"),
        "heatmap": heatmap_data
    }


@app.get("/api/products")
def get_products():
    repo = get_repo()
    prods_df = repo.get_products_df(1)
    if prods_df.empty:
        return []
    return prods_df.to_dict(orient="records")


class ProductBatchUpdate(BaseModel):
    products: List[Dict[str, Any]]


@app.post("/api/products/batch")
def batch_update_products(data: ProductBatchUpdate):
    repo = get_repo()
    count = repo.batch_update_products(1, data.products)
    return {"updated": count}


class ProductAdd(BaseModel):
    product_id: str
    product_name: str
    category: str = "General"
    unit_price: float = 0.0
    lead_time_days: int = 7
    minimum_order_quantity: float = 1.0
    case_pack_size: float = 1.0
    initial_stock: float = 0.0


@app.post("/api/products/add")
def add_product(data: ProductAdd):
    repo = get_repo()
    repo.upsert_products(1, [{
        "product_id": data.product_id.strip(),
        "product_name": data.product_name.strip(),
        "category": data.category.strip(),
        "unit_price": data.unit_price,
        "lead_time_days": data.lead_time_days,
        "minimum_order_quantity": data.minimum_order_quantity,
        "case_pack_size": data.case_pack_size
    }])
    if data.initial_stock > 0:
        repo.save_inventory_snapshot(1, [{
            "product_id": data.product_id.strip(),
            "on_hand_qty": data.initial_stock,
            "on_order_qty": 0.0,
            "backorders": 0.0,
            "lead_time_days": data.lead_time_days
        }])
    return {"success": True}


class InventorySnapshotUpdate(BaseModel):
    snapshots: List[Dict[str, Any]]


@app.post("/api/inventory/snapshot")
def save_inventory_snapshot(data: InventorySnapshotUpdate):
    repo = get_repo()
    repo.save_inventory_snapshot(1, data.snapshots)
    return {"saved": len(data.snapshots)}


@app.get("/api/inventory/snapshots")
def get_inventory_snapshots():
    repo = get_repo()
    snaps = repo.get_latest_inventory_snapshots(1)
    if snaps.empty:
        return []
    snaps["snapshot_date_str"] = pd.to_datetime(snaps["snapshot_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return snaps.to_dict(orient="records")


@app.post("/api/demo/seed")
def reload_demo_data():
    repo = get_repo()
    repo.clear_all_data(1)
    generate_all_samples()
    seed_kirana_demo(repo, 1)
    return {"success": True, "message": "Built-in Kirana Store demo dataset successfully populated."}


@app.post("/api/data/clear")
def clear_all_data():
    repo = get_repo()
    repo.clear_all_data(1)
    return {"success": True, "message": "All database records have been purged."}


@app.get("/api/quality/latest")
def get_latest_quality_report():
    repo = get_repo()
    upload = repo.get_latest_upload(1)
    if not upload or not upload.get("quality_summary"):
        return {
            "has_report": False,
            "message": "No upload audit report available yet."
        }
    return {
        "has_report": True,
        "file_name": upload.get("file_name"),
        "uploaded_at": upload.get("uploaded_at"),
        "quality_report": upload["quality_summary"]
    }


# ---------------- FORECASTING & INVENTORY ----------------

class ForecastRequest(BaseModel):
    product_id: Optional[str] = None
    horizon_days: int = 15
    model_preference: str = "Best Model (Auto-select)"
    is_batch: bool = False


@app.post("/api/forecast/run")
def run_forecast(data: ForecastRequest):
    repo = get_repo()
    sales_df = repo.get_daily_sales_df(1)
    if sales_df.empty:
        raise HTTPException(status_code=400, detail="No sales records in database. Please upload or seed data first.")

    trainer = DemandModelTrainer(val_days=min(14, max(4, int(data.horizon_days * 0.7))))

    if not data.is_batch:
        pid = data.product_id
        if not pid:
            pid = sales_df["product_id"].iloc[0]

        prod_daily = sales_df[sales_df["product_id"] == pid].sort_values(by="sale_date").reset_index(drop=True)
        pname = prod_daily["product_name"].iloc[0] if "product_name" in prod_daily else pid

        train_res = trainer.train_and_evaluate(
            prod_daily,
            model_preference=data.model_preference,
            target_col="quantity_sold"
        )
        forecast_df = generate_future_forecast(
            train_res,
            product_id=pid,
            horizon_days=data.horizon_days
        )

        run_id = repo.save_forecast_run(
            shop_id=1,
            model_name=train_res["selected_model_name"],
            horizon_days=data.horizon_days,
            validation_metrics=train_res["val_metrics"],
            config={"model_preference": data.model_preference, "product_id": pid},
            forecast_rows=forecast_df.to_dict(orient="records")
        )

        # Prepare payload
        forecast_df["forecast_date_str"] = pd.to_datetime(forecast_df["forecast_date"]).dt.strftime("%A, %b %d, %Y")
        hist_recent = prod_daily.tail(60).copy()
        hist_recent["date_str"] = pd.to_datetime(hist_recent["sale_date"]).dt.strftime("%Y-%m-%d")

        return {
            "run_id": run_id,
            "product_id": pid,
            "product_name": pname,
            "selected_model": train_res["selected_model_name"],
            "val_metrics": train_res["val_metrics"],
            "data_notes": train_res.get("data_notes", "Standard"),
            "candidate_evaluations": train_res.get("candidate_evaluations", {}),
            "forecast": forecast_df.to_dict(orient="records"),
            "history": hist_recent[["date_str", "quantity_sold"]].to_dict(orient="records"),
            "val_dates": train_res.get("val_dates", []),
            "val_predictions": train_res.get("val_predictions", [])
        }

    else:
        # Batch forecast
        products_list = sales_df[["product_id", "product_name"]].drop_duplicates()
        all_rows = []
        batch_models = {}

        for _, r in products_list.iterrows():
            pid = r["product_id"]
            p_daily = sales_df[sales_df["product_id"] == pid].sort_values(by="sale_date").reset_index(drop=True)
            res = trainer.train_and_evaluate(p_daily, model_preference=data.model_preference)
            f_df = generate_future_forecast(res, product_id=pid, horizon_days=data.horizon_days)
            all_rows.extend(f_df.to_dict(orient="records"))
            m = res["selected_model_name"]
            batch_models[m] = batch_models.get(m, 0) + 1

        run_id = repo.save_forecast_run(
            shop_id=1,
            model_name=f"Batch Portfolio ({len(products_list)} Products)",
            horizon_days=data.horizon_days,
            validation_metrics={"models_used": batch_models},
            config={"model_preference": data.model_preference, "batch": True},
            forecast_rows=all_rows
        )

        return {
            "run_id": run_id,
            "is_batch": True,
            "total_products": len(products_list),
            "models_used": batch_models
        }


@app.get("/api/forecast/latest")
def get_latest_forecast():
    repo = get_repo()
    latest_run = repo.get_latest_forecast_run(1)
    if not latest_run:
        return {"has_forecast": False}

    forecast_results = repo.get_forecast_results_df(latest_run["run_id"])
    if forecast_results.empty:
        return {"has_forecast": False}

    forecast_results["forecast_date_str"] = pd.to_datetime(forecast_results["forecast_date"]).dt.strftime("%A, %b %d, %Y")

    return {
        "has_forecast": True,
        "run": latest_run,
        "forecast_results": forecast_results.to_dict(orient="records")
    }


class OptimizationRequest(BaseModel):
    mode: str = "Workflow B"  # "Workflow B" or "Workflow A"
    review_period_days: int = 7
    safety_stock_method: str = "variability"
    service_level: float = 0.95
    buffer_percentage: float = 0.20
    planning_period_days: int = 15


@app.post("/api/inventory/optimize")
def run_optimization(data: OptimizationRequest):
    repo = get_repo()
    shop = repo.get_shop(1) or {}
    latest_run = repo.get_latest_forecast_run(1)
    if not latest_run:
        raise HTTPException(status_code=400, detail="No demand forecast found. Please run a forecast before optimizing inventory.")

    forecast_results_df = repo.get_forecast_results_df(latest_run["run_id"])
    if forecast_results_df.empty:
        raise HTTPException(status_code=400, detail="Forecast run contains zero prediction records.")

    is_mode_b = "Workflow B" in data.mode
    snapshots_df = repo.get_latest_inventory_snapshots(1)

    if is_mode_b:
        sales_daily_df = repo.get_daily_sales_df(1)
        recs = generate_mode_b_recommendations(
            forecast_results_df=forecast_results_df,
            inventory_snapshots_df=snapshots_df,
            historical_daily_sales_df=sales_daily_df,
            review_period_days=data.review_period_days,
            safety_stock_method=data.safety_stock_method,
            service_level=data.service_level,
            buffer_percentage=data.buffer_percentage
        )
    else:
        prods_df = repo.get_products_df(1)
        recs = generate_mode_a_recommendations(
            forecast_results_df=forecast_results_df,
            products_df=prods_df,
            planning_period_days=data.planning_period_days,
            replenishment_buffer_pct=data.buffer_percentage
        )

    repo.save_recommendations(latest_run["run_id"], recs)
    saved_recs_df = repo.get_recommendations_df(latest_run["run_id"])

    # Calculate summary
    po_items = saved_recs_df[saved_recs_df["suggested_qty"] > 0]
    total_po_units = float(po_items["suggested_qty"].sum())
    total_po_cost = float((po_items["suggested_qty"] * po_items.get("unit_price", 0.0)).sum())

    counts = saved_recs_df["risk_status"].value_counts().to_dict()

    return {
        "success": True,
        "run_id": latest_run["run_id"],
        "mode": "Workflow B" if is_mode_b else "Workflow A",
        "total_items": len(saved_recs_df),
        "status_counts": counts,
        "po_summary": {
            "order_items": len(po_items),
            "total_units": round(total_po_units, 1),
            "total_cost": round(total_po_cost, 2)
        },
        "recommendations": saved_recs_df.to_dict(orient="records")
    }


@app.get("/api/inventory/recommendations")
def get_recommendations():
    repo = get_repo()
    latest_run = repo.get_latest_forecast_run(1)
    if not latest_run:
        return {"has_recommendations": False}

    recs_df = repo.get_recommendations_df(latest_run["run_id"])
    if recs_df.empty:
        return {"has_recommendations": False}

    counts = recs_df["risk_status"].value_counts().to_dict()
    po_items = recs_df[recs_df["suggested_qty"] > 0]
    total_po_units = float(po_items["suggested_qty"].sum())
    total_po_cost = float((po_items["suggested_qty"] * po_items.get("unit_price", 0.0)).sum())

    return {
        "has_recommendations": True,
        "run_id": latest_run["run_id"],
        "status_counts": counts,
        "po_summary": {
            "order_items": len(po_items),
            "total_units": round(total_po_units, 1),
            "total_cost": round(total_po_cost, 2)
        },
        "recommendations": recs_df.to_dict(orient="records")
    }


class OverridesUpdate(BaseModel):
    overrides: Dict[str, float]


@app.post("/api/inventory/overrides")
def update_recommendations_overrides(data: OverridesUpdate):
    repo = get_repo()
    latest_run = repo.get_latest_forecast_run(1)
    if not latest_run:
        raise HTTPException(status_code=400, detail="No active forecast run.")
    count = repo.update_recommendations_overrides(latest_run["run_id"], data.overrides)
    return {"saved": count}


# ---------------- UPLOADS & FILE INGESTION ----------------

@app.post("/api/upload/preview")
async def preview_upload(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        raw_df, meta = read_uploaded_file(contents, file.filename)
        detected_map = auto_detect_columns(list(raw_df.columns))
        return {
            "success": True,
            "meta": meta,
            "detected_mapping": detected_map,
            "sample_rows": raw_df.head(10).to_dict(orient="records"),
            "all_columns": list(raw_df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload/process")
async def process_upload(
    file: UploadFile = File(...),
    dataset_type: str = Form("sales"),
    allow_returns: bool = Form(True),
    mapping_json: str = Form(...)
):
    repo = get_repo()
    shop = repo.get_shop(1) or {}
    contents = await file.read()

    try:
        raw_df, meta = read_uploaded_file(contents, file.filename)
        confirmed_mapping = json.loads(mapping_json)

        clean_mapping = {
            k: (v if v and v != "-- None / Not Present --" else None)
            for k, v in confirmed_mapping.items()
        }

        req_type = "sales" if dataset_type == "sales" else "inventory"
        is_valid, validation_errors = validate_mapping(clean_mapping, upload_type=req_type)
        if not is_valid:
            raise HTTPException(status_code=400, detail="; ".join(validation_errors))

        cleaner = DataCleaner(clean_mapping)

        if req_type == "sales":
            cleaned_df, quality_report = cleaner.clean_sales_data(raw_df, allow_returns=allow_returns)
            df_daily = aggregate_daily_sales(cleaned_df, shop_id=1, fill_gaps_with_zeros=True)

            prods_to_upsert = []
            for pid, pgroup in cleaned_df.groupby("product_id"):
                pname = pgroup["product_name"].iloc[0] if "product_name" in pgroup else pid
                cat = pgroup["category"].iloc[0] if "category" in pgroup else "General"
                med_price = pgroup["unit_price"].loc[pgroup["unit_price"] > 0].median()
                if pd.isna(med_price) or med_price <= 0:
                    med_price = 10.0
                prods_to_upsert.append({
                    "product_id": str(pid),
                    "product_name": str(pname),
                    "category": str(cat),
                    "unit_price": float(med_price),
                    "lead_time_days": 7,
                    "minimum_order_quantity": 1.0,
                    "case_pack_size": 1.0
                })
            repo.upsert_products(1, prods_to_upsert)

            upload_id = repo.create_upload_record(
                shop_id=1,
                file_name=file.filename,
                file_hash=meta["file_hash"],
                upload_type="sales",
                row_count=len(raw_df),
                quality_summary=quality_report
            )
            rows_saved = repo.save_daily_sales(1, upload_id, df_daily)

            return {
                "success": True,
                "upload_id": upload_id,
                "rows_cleaned": len(cleaned_df),
                "daily_records_saved": rows_saved,
                "products_count": len(prods_to_upsert),
                "quality_report": quality_report
            }
        else:
            cleaned_inv, inv_report = cleaner.clean_inventory_data(raw_df)
            prods_to_upsert = []
            snapshots = []
            for _, row in cleaned_inv.iterrows():
                pid = str(row["product_id"])
                pname = str(row.get("product_name", pid))
                cat = str(row.get("category", "General"))
                lead = int(row.get("lead_time", 7))
                moq = float(row.get("min_order_qty", 1.0))
                pack = float(row.get("case_pack", 1.0))

                prods_to_upsert.append({
                    "product_id": pid,
                    "product_name": pname,
                    "category": cat,
                    "unit_price": 0.0,
                    "lead_time_days": lead,
                    "minimum_order_quantity": moq,
                    "case_pack_size": pack
                })
                snapshots.append({
                    "product_id": pid,
                    "on_hand_qty": float(row.get("stock", 0.0)),
                    "on_order_qty": float(row.get("on_order", 0.0)),
                    "backorders": 0.0,
                    "lead_time_days": lead
                })

            repo.upsert_products(1, prods_to_upsert)
            repo.save_inventory_snapshot(1, snapshots)
            upload_id = repo.create_upload_record(
                shop_id=1,
                file_name=file.filename,
                file_hash=meta["file_hash"],
                upload_type="inventory",
                row_count=len(raw_df),
                quality_summary=inv_report
            )
            return {
                "success": True,
                "upload_id": upload_id,
                "products_count": len(snapshots),
                "quality_report": inv_report
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------- EXPORT REPORTS ----------------

@app.get("/api/reports/excel")
def download_excel_report():
    repo = get_repo()
    shop = repo.get_shop(1) or {}
    sales_df = repo.get_daily_sales_df(1)
    if sales_df.empty:
        raise HTTPException(status_code=400, detail="No data available to generate report.")

    kpis = compute_overview_kpis(sales_df)
    products_df = repo.get_products_df(1)
    latest_run = repo.get_latest_forecast_run(1)
    forecast_df = repo.get_forecast_results_df(latest_run["run_id"]) if latest_run else pd.DataFrame()
    recs_df = repo.get_recommendations_df(latest_run["run_id"]) if latest_run else pd.DataFrame()
    latest_upload = repo.get_latest_upload(1)
    quality_report = latest_upload.get("quality_summary") if latest_upload else None

    inv_mode = recs_df["inventory_mode"].iloc[0] if not recs_df.empty else "inventory_mode"
    val_metrics = latest_run["validation_metrics"] if latest_run else None

    excel_bytes = generate_retail_master_excel(
        shop_info=shop,
        kpis=kpis,
        cleaned_sales_df=sales_df,
        quality_report=quality_report,
        product_analytics_df=products_df,
        forecast_results_df=forecast_df,
        validation_metrics=val_metrics,
        recommendations_df=recs_df,
        inventory_mode=inv_mode
    )

    filename = f"{shop.get('shop_name', 'Retail').replace(' ', '_')}_Full_Report.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/reports/csv/{report_type}")
def download_csv_report(report_type: str):
    repo = get_repo()
    if report_type == "sales":
        df = repo.get_daily_sales_df(1)
        filename = "daily_sales.csv"
    elif report_type == "products":
        df = repo.get_products_df(1)
        filename = "products_catalog.csv"
    elif report_type == "forecast":
        latest = repo.get_latest_forecast_run(1)
        df = repo.get_forecast_results_df(latest["run_id"]) if latest else pd.DataFrame()
        filename = "demand_forecast.csv"
    elif report_type == "recommendations":
        latest = repo.get_latest_forecast_run(1)
        df = repo.get_recommendations_df(latest["run_id"]) if latest else pd.DataFrame()
        filename = "inventory_recommendations.csv"
    elif report_type == "purchase_order":
        latest = repo.get_latest_forecast_run(1)
        if latest:
            recs = repo.get_recommendations_df(latest["run_id"])
            df = recs[recs["suggested_qty"] > 0].copy()
            if not df.empty:
                df["total_cost"] = (df["suggested_qty"] * df["unit_price"]).round(2)
        else:
            df = pd.DataFrame()
        filename = "confirmed_purchase_order.csv"
    else:
        raise HTTPException(status_code=404, detail="Invalid report type.")

    if df.empty:
        raise HTTPException(status_code=400, detail="No data available for this section.")

    csv_bytes = convert_df_to_csv_bytes(df)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ---------------- SPA FRONTEND ROUTE ----------------

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(request: Request, full_path: str):
    # Don't intercept API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Endpoint not found.")

    html_file = PROJECT_ROOT / "templates" / "index.html"
    if not html_file.exists():
        return HTMLResponse("<h1>Retail Forecasting System API Active</h1><p>FastAPI backend running.</p>")
    with open(html_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
