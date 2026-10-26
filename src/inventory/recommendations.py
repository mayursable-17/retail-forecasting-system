"""
High-Level Inventory Recommendation Engines for Mode A (Sales Only) and Mode B (Inventory + Sales).
Provides complete business rule evaluation and explanatory narratives.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from src.inventory.safety_stock import compute_safety_stock
from src.inventory.reorder_point import (
    calculate_inventory_position,
    calculate_reorder_point,
    calculate_order_up_to_target,
    calculate_preliminary_order_quantity,
    apply_order_constraints
)


def generate_mode_a_recommendations(
    forecast_results_df: pd.DataFrame,
    products_df: pd.DataFrame,
    planning_period_days: int = 15,
    replenishment_buffer_pct: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Mode A: Estimated Requirements (Sales Data Only).
    When stock levels are unknown, estimates required units without claiming verified reorders.
    """
    recommendations = []
    prod_meta = {
        row["product_id"]: row.to_dict()
        for _, row in products_df.iterrows()
    } if not products_df.empty else {}

    for pid, group in forecast_results_df.groupby("product_id"):
        # Slice group to planning period
        group_sorted = group.sort_values(by="forecast_date").head(planning_period_days)
        gross_forecast = float(group_sorted["predicted_demand"].sum())
        buffer_qty = float(np.ceil(gross_forecast * replenishment_buffer_pct))
        estimated_requirement = float(np.ceil(gross_forecast + buffer_qty))

        pname = group_sorted["product_name"].iloc[0] if "product_name" in group_sorted else prod_meta.get(pid, {}).get("product_name", pid)
        cat = group_sorted["category"].iloc[0] if "category" in group_sorted else prod_meta.get(pid, {}).get("category", "General")

        explanation = (
            f"Mode A (Sales Only): Forecasted demand is {gross_forecast:.1f} units over {planning_period_days} days. "
            f"With a {int(replenishment_buffer_pct*100)}% replenishment buffer (+{buffer_qty:.1f} units), "
            f"estimated requirement is {estimated_requirement:.1f} units. "
            "NOTE: Actual on-hand inventory and incoming purchase orders are unknown. "
            "This is an estimated requirement, NOT a confirmed reorder quantity or stockout alert."
        )

        recommendations.append({
            "product_id": str(pid),
            "product_name": pname,
            "category": cat,
            "current_stock": None,
            "inventory_position": None,
            "reorder_point": None,
            "safety_stock": buffer_qty,
            "expected_lead_time_demand": gross_forecast,
            "order_up_to_target": None,
            "suggested_qty": estimated_requirement,
            "risk_status": "Insufficient Inventory Information",
            "inventory_mode": "estimated_mode",
            "explanation": explanation
        })

    return recommendations


def generate_mode_b_recommendations(
    forecast_results_df: pd.DataFrame,
    inventory_snapshots_df: pd.DataFrame,
    historical_daily_sales_df: pd.DataFrame,
    review_period_days: int = 7,
    safety_stock_method: str = "variability",
    service_level: float = 0.95,
    buffer_percentage: float = 0.20
) -> List[Dict[str, Any]]:
    """
    Mode B: Inventory-Based Recommendations (Sales + Inventory).
    Calculates inventory position, safety stock, ROP, order-up-to target, and MOQ/case pack adjustments.
    """
    recommendations = []

    # Map inventory snapshot by product_id
    inv_map = {}
    if not inventory_snapshots_df.empty:
        for _, row in inventory_snapshots_df.iterrows():
            inv_map[str(row["product_id"])] = row.to_dict()

    # Calculate historical daily demand std dev per product
    daily_std_map = {}
    if not historical_daily_sales_df.empty:
        for pid, group in historical_daily_sales_df.groupby("product_id"):
            daily_std_map[str(pid)] = float(group["quantity_sold"].std(ddof=1)) if len(group) > 1 else 0.0

    for pid, group in forecast_results_df.groupby("product_id"):
        pid_str = str(pid)
        inv_data = inv_map.get(pid_str)

        group_sorted = group.sort_values(by="forecast_date")
        forecast_daily = group_sorted["predicted_demand"].values
        mean_forecast_daily = float(np.mean(forecast_daily)) if len(forecast_daily) > 0 else 0.0

        pname = group_sorted["product_name"].iloc[0] if "product_name" in group_sorted else pid_str
        cat = group_sorted["category"].iloc[0] if "category" in group_sorted else "General"

        # If this product has no inventory snapshot, fall back to Mode A behavior for this item
        if not inv_data:
            estimated_req = float(np.ceil(forecast_daily.sum()))
            recommendations.append({
                "product_id": pid_str,
                "product_name": pname,
                "category": cat,
                "current_stock": None,
                "inventory_position": None,
                "reorder_point": None,
                "safety_stock": None,
                "expected_lead_time_demand": round(forecast_daily.sum(), 1),
                "order_up_to_target": None,
                "suggested_qty": estimated_req,
                "risk_status": "Insufficient Inventory Information",
                "inventory_mode": "estimated_mode",
                "explanation": "No inventory record found for this product. Upload inventory or enter stock counts to unlock Mode B optimization."
            })
            continue

        on_hand = float(inv_data.get("on_hand_qty", 0.0))
        on_order = float(inv_data.get("on_order_qty", 0.0))
        backorders = float(inv_data.get("backorders", 0.0))
        lead_time = max(1, int(inv_data.get("lead_time_days", 7)))
        moq = float(inv_data.get("minimum_order_quantity", 1.0))
        case_pack = float(inv_data.get("case_pack_size", 1.0))

        # 1. Inventory Position
        inv_position = calculate_inventory_position(on_hand, on_order, backorders)

        # 2. Expected Demand During Lead Time
        if len(forecast_daily) >= lead_time:
            exp_lt_demand = float(forecast_daily[:lead_time].sum())
        else:
            exp_lt_demand = mean_forecast_daily * lead_time

        # 3. Expected Demand During (Lead Time + Review Period)
        total_cycle_days = lead_time + review_period_days
        if len(forecast_daily) >= total_cycle_days:
            exp_cycle_demand = float(forecast_daily[:total_cycle_days].sum())
        else:
            exp_cycle_demand = mean_forecast_daily * total_cycle_days

        # 4. Safety Stock
        std_d = daily_std_map.get(pid_str, 0.0)
        ss, ss_reason = compute_safety_stock(
            daily_demand_std=std_d,
            expected_daily_demand=mean_forecast_daily,
            lead_time_days=lead_time,
            method=safety_stock_method,
            service_level=service_level,
            buffer_percentage=buffer_percentage
        )

        # 5. Reorder Point (ROP) & Order-up-to Target (S)
        rop = calculate_reorder_point(exp_lt_demand, ss)
        order_up_to = calculate_order_up_to_target(exp_cycle_demand, ss)

        # 6. Preliminary and Constrained Order Quantity
        prelim_qty = calculate_preliminary_order_quantity(order_up_to, inv_position)
        
        # Only order if inventory position is at or below ROP (or if preliminary order > 0)
        if inv_position <= rop:
            final_qty, constraint_reason = apply_order_constraints(prelim_qty, moq=moq, case_pack=case_pack)
        else:
            final_qty = 0.0
            constraint_reason = "Inventory position is above Reorder Point; no order required."

        # 7. Risk Status Categorization
        if on_hand <= 0 or (inv_position < ss and exp_lt_demand > inv_position):
            risk_status = "Stock Risk"
            risk_reason = "CRITICAL: Stock is depleted or below safety buffer with incoming demand exceeding inventory position."
        elif inv_position <= rop:
            risk_status = "Reorder Review"
            risk_reason = f"Inventory position ({inv_position:.1f}) is at or below Reorder Point ({rop:.1f}). Replenishment required."
        elif inv_position > 2.5 * (exp_lt_demand + ss) and inv_position > 10:
            risk_status = "Potential Excess Stock"
            risk_reason = f"Inventory position ({inv_position:.1f}) significantly exceeds cycle demand and safety buffer. Risk of overstocking."
        else:
            risk_status = "Adequate Stock"
            risk_reason = f"Inventory position ({inv_position:.1f}) is healthy above Reorder Point ({rop:.1f})."

        full_explanation = (
            f"Status: {risk_status}. {risk_reason} "
            f"On-Hand: {on_hand:.1f}, On-Order: {on_order:.1f}, Inventory Position: {inv_position:.1f}. "
            f"Expected Lead Time Demand: {exp_lt_demand:.1f} (Lead time: {lead_time} days). "
            f"Safety Stock: {ss:.1f} ({ss_reason}). Reorder Point: {rop:.1f}. "
            f"Order-up-to Target: {order_up_to:.1f} (Review period: {review_period_days} days). "
            f"Order Action: {constraint_reason}"
        )

        recommendations.append({
            "product_id": pid_str,
            "product_name": pname,
            "category": cat,
            "current_stock": on_hand,
            "inventory_position": inv_position,
            "reorder_point": rop,
            "safety_stock": ss,
            "expected_lead_time_demand": round(exp_lt_demand, 1),
            "order_up_to_target": order_up_to,
            "suggested_qty": final_qty,
            "risk_status": risk_status,
            "inventory_mode": "inventory_mode",
            "explanation": full_explanation
        })

    return recommendations
