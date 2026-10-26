"""
Reorder Point (ROP) and Order-up-to Target Inventory Calculations.
Implements continuous and periodic review formulas with packaging constraints.
"""

import math
from typing import Tuple


def calculate_inventory_position(
    on_hand_stock: float,
    on_order_quantity: float = 0.0,
    backorders: float = 0.0
) -> float:
    """
    Inventory Position = On-hand Stock + On-order Quantity - Backorders
    """
    return float(on_hand_stock) + float(on_order_quantity) - float(backorders)


def calculate_reorder_point(
    expected_lead_time_demand: float,
    safety_stock: float
) -> float:
    """
    Reorder Point (ROP) = Expected Demand During Lead Time + Safety Stock
    """
    return max(0.0, float(math.ceil(expected_lead_time_demand + safety_stock)))


def calculate_order_up_to_target(
    expected_demand_during_lead_and_review: float,
    safety_stock: float
) -> float:
    """
    Periodic Review Target (S) = Expected Demand During (Lead Time + Review Period) + Safety Stock
    """
    return max(0.0, float(math.ceil(expected_demand_during_lead_and_review + safety_stock)))


def calculate_preliminary_order_quantity(
    order_up_to_target: float,
    inventory_position: float
) -> float:
    """
    Preliminary Order Qty = max(0, Order-up-to Target - Inventory Position)
    """
    return max(0.0, float(order_up_to_target - inventory_position))


def apply_order_constraints(
    preliminary_quantity: float,
    minimum_order_quantity: float = 1.0,
    case_pack_size: float = 1.0,
    moq: float = None,
    case_pack: float = None
) -> Tuple[float, str]:
    """
    Applies supplier constraints:
    1. If preliminary_quantity > 0 and < MOQ: round up to MOQ.
    2. Case-pack rounding: round up to nearest multiple of case_pack_size.
    
    Returns:
    - (constrained_quantity, explanation_of_adjustments)
    """
    if moq is not None:
        minimum_order_quantity = moq
    if case_pack is not None:
        case_pack_size = case_pack
    qty = float(preliminary_quantity)
    if qty <= 0.0:
        return 0.0, "No reorder needed (inventory position meets or exceeds target)."

    adjustments = []

    # 1. MOQ constraint
    moq = max(1.0, float(minimum_order_quantity))
    if qty < moq:
        adjustments.append(f"Adjusted from {qty:.1f} to MOQ of {moq:.1f}")
        qty = moq

    # 2. Case pack rounding
    case_pack = max(1.0, float(case_pack_size))
    if case_pack > 1.0:
        packs_needed = math.ceil(qty / case_pack)
        rounded_qty = float(packs_needed * case_pack)
        if rounded_qty != qty:
            adjustments.append(f"Rounded up to {rounded_qty:.1f} ({packs_needed} packs of {case_pack:.1f})")
            qty = rounded_qty

    explanation = "; ".join(adjustments) if adjustments else "Standard order quantity without packaging constraints."
    return qty, explanation
