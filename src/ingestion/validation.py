"""
File and Data Pre-validation Utilities.
"""

from typing import Dict, List, Any, Optional
import pandas as pd


def check_basic_integrity(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect raw dataframe for row counts, null columns, and empty values."""
    total_rows = len(df)
    total_cols = len(df.columns)
    null_counts = df.isnull().sum().to_dict()
    all_null_cols = [col for col, count in null_counts.items() if count == total_rows]

    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "null_counts": null_counts,
        "all_null_cols": all_null_cols,
        "is_empty": total_rows == 0
    }
