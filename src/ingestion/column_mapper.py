"""
Intelligent column mapping engine for retail spreadsheets.
Matches variations in column names to standardized entities.
"""

import re
from typing import Dict, List, Optional, Tuple
from src.config import STANDARD_COLUMNS


def normalize_col_name(col: str) -> str:
    """Normalize column header for matching (lower, alphanumeric only)."""
    if not isinstance(col, str):
        col = str(col)
    clean = col.lower().strip()
    clean = re.sub(r"[^\w\s]", "", clean)
    clean = re.sub(r"\s+", "_", clean)
    return clean


def auto_detect_columns(actual_columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Match uploaded column names to standard schema targets.
    
    Returns a dict mapping standard_target -> actual_column_name_or_None.
    """
    mapped: Dict[str, Optional[str]] = {target: None for target in STANDARD_COLUMNS}
    used_actual_cols = set()

    normalized_map = {col: normalize_col_name(col) for col in actual_columns}

    # Pass 1: Exact matches against standard targets or synonyms
    for target, synonyms in STANDARD_COLUMNS.items():
        all_candidates = [target] + synonyms
        normalized_candidates = [normalize_col_name(c) for c in all_candidates]

        for orig_col, norm_col in normalized_map.items():
            if orig_col in used_actual_cols:
                continue
            if norm_col in normalized_candidates:
                mapped[target] = orig_col
                used_actual_cols.add(orig_col)
                break

    # Pass 2: Substring / keyword matches for unmapped targets
    for target, synonyms in STANDARD_COLUMNS.items():
        if mapped[target] is not None:
            continue
        all_candidates = [target] + synonyms
        normalized_candidates = [normalize_col_name(c) for c in all_candidates]

        for orig_col, norm_col in normalized_map.items():
            if orig_col in used_actual_cols:
                continue
            for cand in normalized_candidates:
                if (cand in norm_col or norm_col in cand) and len(cand) > 2:
                    mapped[target] = orig_col
                    used_actual_cols.add(orig_col)
                    break
            if mapped[target] is not None:
                break

    return mapped


def validate_mapping(
    mapping: Dict[str, Optional[str]],
    upload_type: str = "sales"
) -> Tuple[bool, List[str]]:
    """
    Validate that mandatory fields are mapped for the given upload type.
    
    Returns:
    - (is_valid, list_of_error_or_warning_messages)
    """
    errors = []

    if upload_type == "sales":
        if not mapping.get("date"):
            errors.append("Required column 'Date' is not mapped.")
        
        has_prod = mapping.get("product_id") or mapping.get("product_name")
        if not has_prod:
            errors.append("At least one product identifier ('Product ID' or 'Product Name') must be mapped.")

        has_qty = bool(mapping.get("quantity"))
        has_rev = bool(mapping.get("revenue"))
        has_price = bool(mapping.get("unit_price"))

        if not has_qty and not (has_rev and has_price):
            errors.append(
                "Either 'Quantity' must be mapped, or both 'Revenue' and 'Unit Price' must be mapped "
                "to calculate quantity. Cannot forecast demand with only revenue."
            )

    elif upload_type == "inventory":
        has_prod = mapping.get("product_id") or mapping.get("product_name")
        if not has_prod:
            errors.append("Product identifier ('Product ID' or 'Product Name') must be mapped for inventory.")
        if not mapping.get("stock"):
            errors.append("Current Stock / Inventory Level must be mapped for inventory upload.")

    return len(errors) == 0, errors
