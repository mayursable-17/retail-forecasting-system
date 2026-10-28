"""
Tests for SQLAlchemy Database Layer and Repository Operations.
"""

import pytest
import pandas as pd
from datetime import date, datetime


def test_shop_and_products_operations(in_memory_repo):
    repo = in_memory_repo
    shop = repo.get_shop(1)
    assert shop is not None
    assert shop["currency_code"] == "INR"

    # Upsert product
    prods = [{
        "product_id": "P101",
        "product_name": "Basmati Rice 1kg",
        "category": "Groceries",
        "unit_price": 120.0,
        "lead_time_days": 5,
        "minimum_order_quantity": 10.0,
        "case_pack_size": 5.0
    }]
    repo.upsert_products(1, prods)

    df_p = repo.get_products_df(1)
    assert len(df_p) == 1
    assert df_p.iloc[0]["product_id"] == "P101"
    assert df_p.iloc[0]["unit_price"] == 120.0


def test_sales_daily_operations(in_memory_repo):
    repo = in_memory_repo
    # Add product first
    repo.upsert_products(1, [{
        "product_id": "P101",
        "product_name": "Basmati Rice 1kg",
        "category": "Groceries",
        "unit_price": 120.0
    }])

    # Add daily sales
    sales_df = pd.DataFrame([
        {"product_id": "P101", "sale_date": "2026-10-01", "quantity_sold": 5.0, "revenue": 600.0},
        {"product_id": "P101", "sale_date": "2026-10-02", "quantity_sold": 8.0, "revenue": 960.0},
    ])
    upload_id = repo.create_upload_record(1, "test.csv", "hash1", "sales", 2, {})
    repo.save_daily_sales(1, upload_id, sales_df)

    retrieved_df = repo.get_daily_sales_df(1)
    assert len(retrieved_df) == 2
    assert retrieved_df["quantity_sold"].sum() == 13.0
    assert retrieved_df["revenue"].sum() == 1560.0


def test_inventory_snapshot_latest_query(in_memory_repo):
    repo = in_memory_repo
    repo.upsert_products(1, [{
        "product_id": "P101",
        "product_name": "Basmati Rice 1kg",
        "category": "Groceries",
        "unit_price": 120.0
    }])

    # First snapshot
    repo.save_inventory_snapshot(1, [{
        "product_id": "P101",
        "on_hand_qty": 20.0,
        "on_order_qty": 0.0,
        "lead_time_days": 5
    }])
    # Second snapshot later
    repo.save_inventory_snapshot(1, [{
        "product_id": "P101",
        "on_hand_qty": 15.0,
        "on_order_qty": 10.0,
        "lead_time_days": 5
    }])

    snaps = repo.get_latest_inventory_snapshots(1)
    assert len(snaps) == 1
    # Should reflect the latest snapshot: on_hand = 15.0
    assert snaps.iloc[0]["on_hand_qty"] == 15.0
    assert snaps.iloc[0]["on_order_qty"] == 10.0


def test_forecast_and_recommendations_persistence(in_memory_repo):
    repo = in_memory_repo
    repo.upsert_products(1, [{
        "product_id": "P101",
        "product_name": "Basmati Rice 1kg",
        "category": "Groceries",
        "unit_price": 120.0
    }])

    run_id = repo.save_forecast_run(
        shop_id=1,
        model_name="Moving Average",
        horizon_days=7,
        validation_metrics={"mae": 1.5, "wape_pct": 12.0},
        config={},
        forecast_rows=[
            {"product_id": "P101", "forecast_date": "2026-10-10", "predicted_demand": 6.0, "lower_bound": 4.0, "upper_bound": 8.0}
        ]
    )
    assert run_id > 0

    results_df = repo.get_forecast_results_df(run_id)
    assert len(results_df) == 1
    assert results_df.iloc[0]["predicted_demand"] == 6.0

    # Save recommendations
    repo.save_recommendations(run_id, [{
        "product_id": "P101",
        "current_stock": 10.0,
        "inventory_position": 10.0,
        "reorder_point": 15.0,
        "suggested_qty": 20.0,
        "risk_status": "Reorder Review",
        "inventory_mode": "inventory_mode",
        "explanation": "Test explanation"
    }])

    recs_df = repo.get_recommendations_df(run_id)
    assert len(recs_df) == 1
    assert recs_df.iloc[0]["suggested_qty"] == 20.0
    assert recs_df.iloc[0]["risk_status"] == "Reorder Review"

    # Test overrides
    updated = repo.update_recommendations_overrides(run_id, {"P101": 35.0})
    assert updated == 1
    recs_df_after = repo.get_recommendations_df(run_id)
    assert recs_df_after.iloc[0]["suggested_qty"] == 35.0


def test_operational_defaults_persistence(in_memory_repo):
    repo = in_memory_repo
    success = repo.update_shop_operational_defaults(
        shop_id=1,
        lead_time_days=10,
        review_period_days=14,
        service_level=0.98,
        safety_stock_method="buffer",
        replenishment_buffer_pct=0.25
    )
    assert success is True

    shop = repo.get_shop(1)
    assert shop["default_lead_time_days"] == 10
    assert shop["default_review_period_days"] == 14
    assert shop["default_service_level"] == 0.98
    assert shop["default_safety_stock_method"] == "buffer"
    assert shop["default_replenishment_buffer_pct"] == 0.25


def test_batch_update_products(in_memory_repo):
    repo = in_memory_repo
    repo.upsert_products(1, [{
        "product_id": "P201",
        "product_name": "Mustard Oil 1L",
        "category": "Oils",
        "unit_price": 180.0
    }])

    updated_count = repo.batch_update_products(1, [{
        "product_id": "P201",
        "unit_price": 195.0,
        "lead_time_days": 12,
        "minimum_order_quantity": 24.0,
        "case_pack_size": 12.0
    }])
    assert updated_count == 1

    df_p = repo.get_products_df(1)
    p = df_p[df_p["product_id"] == "P201"].iloc[0]
    assert p["unit_price"] == 195.0
    assert p["lead_time_days"] == 12
    assert p["minimum_order_quantity"] == 24.0
    assert p["case_pack_size"] == 12.0


def test_latest_upload_and_alerts_summary(in_memory_repo):
    repo = in_memory_repo
    upload_id = repo.create_upload_record(
        shop_id=1,
        file_name="sales_audit_test.csv",
        file_hash="testhash123",
        upload_type="sales",
        row_count=50,
        quality_summary={"accepted_rows": 50, "flagged_rows": 0}
    )
    assert upload_id > 0

    latest = repo.get_latest_upload(shop_id=1)
    assert latest is not None
    assert latest["file_name"] == "sales_audit_test.csv"
    assert latest["quality_summary"]["accepted_rows"] == 50

    alerts = repo.get_stock_alerts_summary(shop_id=1)
    assert isinstance(alerts, dict)
    assert "stock_risk" in alerts
