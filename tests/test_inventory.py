"""
Tests for Inventory Optimization, Safety Stock, Reorder Points, and Business Constraints.
Includes mathematical proof verification against known analytical answers.
"""

import pytest
import math
import pandas as pd

from src.inventory.safety_stock import calculate_safety_stock_variability, calculate_safety_stock_buffer, get_z_score
from src.inventory.reorder_point import (
    calculate_inventory_position,
    calculate_reorder_point,
    calculate_order_up_to_target,
    calculate_preliminary_order_quantity,
    apply_order_constraints
)
from src.inventory.recommendations import generate_mode_a_recommendations, generate_mode_b_recommendations


def test_inventory_position_formula():
    # OH = 50, On-order = 20, Backorders = 5 -> IP = 65
    ip = calculate_inventory_position(on_hand_stock=50, on_order_quantity=20, backorders=5)
    assert ip == 65.0


def test_safety_stock_variability_analytical_proof():
    # Given: daily_std = 3.0, lead_time = 4 days, service_level = 95% (z = 1.645)
    # Expected SS = ceil(1.645 * 3.0 * sqrt(4)) = ceil(1.645 * 3 * 2) = ceil(9.87) = 10.0
    ss = calculate_safety_stock_variability(daily_demand_std=3.0, lead_time_days=4, service_level=0.95)
    assert ss == 10.0


def test_reorder_point_and_order_up_to_target():
    # Lead time demand = 40, Safety Stock = 10 -> ROP = ceil(40 + 10) = 50
    rop = calculate_reorder_point(expected_lead_time_demand=40, safety_stock=10)
    assert rop == 50.0

    # Review period demand = 30, Total cycle demand (L + R) = 70, Safety Stock = 10
    # Target S = ceil(70 + 10) = 80
    target_s = calculate_order_up_to_target(expected_demand_during_lead_and_review=70, safety_stock=10)
    assert target_s == 80.0

    # Case 1: Inventory position = 30 (below ROP 50)
    # Preliminary order = max(0, 80 - 30) = 50
    prelim_qty = calculate_preliminary_order_quantity(order_up_to_target=target_s, inventory_position=30)
    assert prelim_qty == 50.0

    # Case 2: Inventory position = 90 (above target S 80)
    # Preliminary order = max(0, 80 - 90) = 0
    prelim_qty_zero = calculate_preliminary_order_quantity(order_up_to_target=target_s, inventory_position=90)
    assert prelim_qty_zero == 0.0


def test_moq_and_case_pack_rounding():
    # Prelim order = 14, MOQ = 20 -> adjusts to 20
    qty_moq, _ = apply_order_constraints(preliminary_quantity=14, minimum_order_quantity=20, case_pack_size=1)
    assert qty_moq == 20.0

    # Prelim order = 14, MOQ = 10, Case Pack = 6 -> ceil(14/6)*6 = 3 * 6 = 18
    qty_pack, _ = apply_order_constraints(preliminary_quantity=14, minimum_order_quantity=10, case_pack_size=6)
    assert qty_pack == 18.0


def test_mode_a_recommendations_sales_only():
    forecast_df = pd.DataFrame([
        {"forecast_date": f"2026-11-0{i}", "product_id": "P1", "product_name": "Item A", "category": "General", "predicted_demand": 10.0}
        for i in range(1, 8)
    ])
    prods_df = pd.DataFrame([{"product_id": "P1", "product_name": "Item A", "category": "General"}])

    recs = generate_mode_a_recommendations(
        forecast_results_df=forecast_df,
        products_df=prods_df,
        planning_period_days=7,
        replenishment_buffer_pct=0.15
    )

    assert len(recs) == 1
    r = recs[0]
    assert r["inventory_mode"] == "estimated_mode"
    assert r["risk_status"] == "Insufficient Inventory Information"
    assert r["current_stock"] is None
    # 7 days * 10 = 70. 70 * 0.15 = 10.5 -> ceil = 11. Total = 81.
    assert r["suggested_qty"] == 81.0
    assert "NOTE: Actual on-hand inventory and incoming purchase orders are unknown" in r["explanation"]


def test_mode_b_recommendations_full():
    forecast_df = pd.DataFrame([
        {"forecast_date": f"2026-11-{i:02d}", "product_id": "P1", "product_name": "Item A", "category": "General", "predicted_demand": 5.0}
        for i in range(1, 20)
    ])
    # Low stock snapshot: on_hand = 2, lead_time = 4, review_period = 7, moq = 10, case_pack = 5
    inv_df = pd.DataFrame([{
        "product_id": "P1",
        "on_hand_qty": 2.0,
        "on_order_qty": 0.0,
        "backorders": 0.0,
        "lead_time_days": 4,
        "minimum_order_quantity": 10.0,
        "case_pack_size": 5.0
    }])
    hist_sales_df = pd.DataFrame([
        {"product_id": "P1", "quantity_sold": 5.0} for _ in range(30)
    ])

    recs = generate_mode_b_recommendations(
        forecast_results_df=forecast_df,
        inventory_snapshots_df=inv_df,
        historical_daily_sales_df=hist_sales_df,
        review_period_days=7,
        safety_stock_method="buffer",
        buffer_percentage=0.20
    )

    assert len(recs) == 1
    r = recs[0]
    assert r["inventory_mode"] == "inventory_mode"
    assert r["risk_status"] in ["Stock Risk", "Reorder Review"]
    assert r["current_stock"] == 2.0
    assert r["suggested_qty"] > 0
    # Must be rounded to multiple of case_pack (5)
    assert r["suggested_qty"] % 5.0 == 0.0
