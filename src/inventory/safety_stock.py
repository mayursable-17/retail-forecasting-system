"""
Safety Stock Calculations.
Supports both Statistical Demand Variability Method and Fixed Buffer Method.
"""

import math
from typing import Dict, Any, Tuple
from src.config import SERVICE_LEVEL_Z_MAP, DEFAULT_SERVICE_LEVEL


def get_z_score(service_level: float = DEFAULT_SERVICE_LEVEL) -> float:
    """Return standard normal z-score corresponding to service level."""
    # Find closest known service level
    available_levels = list(SERVICE_LEVEL_Z_MAP.keys())
    closest_level = min(available_levels, key=lambda sl: abs(sl - service_level))
    return SERVICE_LEVEL_Z_MAP[closest_level]


def calculate_safety_stock_variability(
    daily_demand_std: float,
    lead_time_days: int,
    service_level: float = DEFAULT_SERVICE_LEVEL
) -> float:
    """
    Standard formula: Safety Stock = z * sigma_d * sqrt(Lead Time)
    Assumes lead time is deterministic and daily demand has standard deviation sigma_d.
    """
    if daily_demand_std <= 0 or lead_time_days <= 0:
        return 0.0
    z = get_z_score(service_level)
    ss = z * float(daily_demand_std) * math.sqrt(float(lead_time_days))
    return max(0.0, float(math.ceil(ss)))


def calculate_safety_stock_buffer(
    expected_daily_demand: float,
    lead_time_days: int,
    buffer_percentage: float = 0.20
) -> float:
    """
    Heuristic buffer formula: Safety Stock = Buffer% * Expected Daily Demand * Lead Time
    Useful when historical variability data is sparse or unreliable.
    """
    if expected_daily_demand <= 0 or lead_time_days <= 0 or buffer_percentage <= 0:
        return 0.0
    ss = float(buffer_percentage) * float(expected_daily_demand) * float(lead_time_days)
    return max(0.0, float(math.ceil(ss)))


def compute_safety_stock(
    daily_demand_std: float,
    expected_daily_demand: float,
    lead_time_days: int,
    method: str = "variability",
    service_level: float = DEFAULT_SERVICE_LEVEL,
    buffer_percentage: float = 0.20
) -> Tuple[float, str]:
    """
    Calculate safety stock based on chosen method, with automatic fallback
    if variability cannot be estimated.
    
    Returns:
    - (safety_stock_units, explanation_string)
    """
    lead_time_days = max(1, int(lead_time_days))

    if method == "variability":
        if daily_demand_std > 0:
            z = get_z_score(service_level)
            ss = calculate_safety_stock_variability(daily_demand_std, lead_time_days, service_level)
            explanation = (
                f"Statistical variability method (Service Level: {int(service_level*100)}%, z={z}, "
                f"daily demand std={daily_demand_std:.2f}, lead time={lead_time_days} days)."
            )
            return ss, explanation
        else:
            # Fallback to buffer
            ss = calculate_safety_stock_buffer(expected_daily_demand, lead_time_days, buffer_percentage)
            explanation = (
                f"Demand std is zero or sparse; fell back to {int(buffer_percentage*100)}% buffer method "
                f"(expected daily demand={expected_daily_demand:.2f}, lead time={lead_time_days} days)."
            )
            return ss, explanation

    else:
        # Buffer method
        ss = calculate_safety_stock_buffer(expected_daily_demand, lead_time_days, buffer_percentage)
        explanation = (
            f"Configured {int(buffer_percentage*100)}% replenishment buffer "
            f"(expected daily demand={expected_daily_demand:.2f}, lead time={lead_time_days} days)."
        )
        return ss, explanation
