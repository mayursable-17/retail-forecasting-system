"""
Data Cleaning & Quality Pipeline.
Validates, cleans, and audits raw retail records according to Module 4 specifications.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd


class DataCleaner:
    def __init__(self, mapping: Dict[str, Optional[str]]):
        self.mapping = mapping
        self.actions_taken: List[str] = []
        self.quality_report: Dict[str, Any] = {}

    def clean_sales_data(
        self,
        raw_df: pd.DataFrame,
        allow_returns: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Clean raw sales dataframe using user-confirmed column mappings.
        
        Parameters:
        - raw_df: Original input DataFrame (preserved untouched).
        - allow_returns: If True, negative quantities are interpreted as returns/refunds
          and deducted from net demand, rather than being discarded.
          
        Returns:
        - (cleaned_df, quality_report)
        """
        df = raw_df.copy()
        initial_count = len(df)
        self.actions_taken = []

        date_col = self.mapping.get("date")
        prod_id_col = self.mapping.get("product_id")
        prod_name_col = self.mapping.get("product_name")
        qty_col = self.mapping.get("quantity")
        price_col = self.mapping.get("unit_price")
        rev_col = self.mapping.get("revenue")
        cat_col = self.mapping.get("category")

        # Track audit metrics
        missing_dates = 0
        missing_products = 0
        duplicate_records = 0
        invalid_numbers = 0
        negative_qtys = 0
        negative_prices = 0
        flagged_count = 0
        excluded_count = 0

        # Rename mapped columns to standardized names
        standard_cols_map = {}
        for std_key, orig_col in self.mapping.items():
            if orig_col and orig_col in df.columns:
                standard_cols_map[orig_col] = std_key
        
        # Keep track of unmapped original columns
        df = df.rename(columns=standard_cols_map)

        # 1. Date Validation & Parsing
        if "date" in df.columns:
            df["date"] = df["date"].replace(r"^\s*$", np.nan, regex=True)
            missing_dates = int(df["date"].isnull().sum())
            parsed_dates = pd.to_datetime(df["date"], errors="coerce")
            invalid_dates = int(parsed_dates.isnull().sum() - missing_dates)
            if invalid_dates > 0 or missing_dates > 0:
                self.actions_taken.append(
                    f"Identified {missing_dates} empty dates and {invalid_dates} unparseable date values."
                )
            df["date"] = parsed_dates
        else:
            raise ValueError("Date column is not mapped or missing.")

        # 2. Product Identifier Standardization
        # If product_id is missing but product_name exists, use product_name as product_id
        if "product_id" not in df.columns and "product_name" in df.columns:
            df["product_id"] = df["product_name"]
            self.actions_taken.append("Derived product_id from product_name column.")
        elif "product_name" not in df.columns and "product_id" in df.columns:
            df["product_name"] = df["product_id"]
            self.actions_taken.append("Derived product_name from product_id column.")

        df["product_id"] = df["product_id"].astype(str).str.strip()
        df["product_name"] = df["product_name"].astype(str).str.strip()

        # Check missing or invalid product identifiers
        invalid_pids = df["product_id"].isin(["nan", "None", "", "null", "N/A"])
        missing_products = int(invalid_pids.sum())
        if missing_products > 0:
            self.actions_taken.append(f"Flagged {missing_products} records with blank or null product IDs.")

        # Category standardisation
        if "category" not in df.columns:
            df["category"] = "General"
            self.actions_taken.append("Assigned default category 'General' to unmapped category records.")
        else:
            df["category"] = df["category"].fillna("General").astype(str).str.strip()
            df.loc[df["category"].isin(["nan", "None", ""]), "category"] = "General"

        # 3. Numeric conversions for Quantity, Unit Price, Revenue
        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        else:
            df["quantity"] = np.nan

        if "unit_price" in df.columns:
            df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        else:
            df["unit_price"] = np.nan

        if "revenue" in df.columns:
            df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
        else:
            df["revenue"] = np.nan

        # Deduce missing quantity or revenue if possible
        # Case A: Qty is missing, but Revenue and Unit Price are present
        qty_imputed = 0
        missing_qty_mask = df["quantity"].isnull() & df["revenue"].notnull() & df["unit_price"].notnull()
        if missing_qty_mask.sum() > 0:
            valid_price = df.loc[missing_qty_mask, "unit_price"] > 0
            df.loc[missing_qty_mask & valid_price, "quantity"] = (
                df.loc[missing_qty_mask & valid_price, "revenue"] / df.loc[missing_qty_mask & valid_price, "unit_price"]
            )
            qty_imputed = int((missing_qty_mask & valid_price).sum())
            self.actions_taken.append(f"Imputed {qty_imputed} quantity values from revenue / unit_price.")

        # Case B: Revenue is missing, but Quantity and Unit Price are present
        rev_imputed = 0
        missing_rev_mask = df["revenue"].isnull() & df["quantity"].notnull() & df["unit_price"].notnull()
        if missing_rev_mask.sum() > 0:
            df.loc[missing_rev_mask, "revenue"] = (
                df.loc[missing_rev_mask, "quantity"] * df.loc[missing_rev_mask, "unit_price"]
            )
            rev_imputed = int(missing_rev_mask.sum())
            self.actions_taken.append(f"Calculated {rev_imputed} revenue values from quantity * unit_price.")

        # Case C: Unit Price is missing, but Revenue and Quantity are present
        price_imputed = 0
        missing_price_mask = df["unit_price"].isnull() & df["revenue"].notnull() & df["quantity"].notnull()
        if missing_price_mask.sum() > 0:
            valid_qty = df.loc[missing_price_mask, "quantity"] != 0
            df.loc[missing_price_mask & valid_qty, "unit_price"] = (
                df.loc[missing_price_mask & valid_qty, "revenue"] / df.loc[missing_price_mask & valid_qty, "quantity"]
            ).abs()
            price_imputed = int((missing_price_mask & valid_qty).sum())
            self.actions_taken.append(f"Imputed {price_imputed} unit prices from revenue / quantity.")

        # 4. Check for duplicates
        duplicate_records = int(df.duplicated(subset=["date", "product_id", "quantity", "revenue"]).sum())
        if duplicate_records > 0:
            self.actions_taken.append(f"Identified {duplicate_records} exact duplicate transaction rows (kept first occurrence).")
            df = df.drop_duplicates(subset=["date", "product_id", "quantity", "revenue"], keep="first")

        # 5. Check negative values
        neg_qty_mask = df["quantity"] < 0
        negative_qtys = int(neg_qty_mask.sum())

        neg_price_mask = df["unit_price"] < 0
        negative_prices = int(neg_price_mask.sum())

        if negative_qtys > 0:
            if allow_returns:
                self.actions_taken.append(
                    f"Retained {negative_qtys} negative quantities as documented customer returns/refunds. "
                    "These will appropriately offset net demand during daily aggregation."
                )
            else:
                self.actions_taken.append(f"Flagged {negative_qtys} negative quantities for exclusion.")

        if negative_prices > 0:
            self.actions_taken.append(f"Flagged {negative_prices} negative price records as invalid.")

        # 6. Filtering & Inclusion/Exclusion Decisions
        # Required valid date and valid product_id
        valid_date_mask = df["date"].notnull()
        valid_prod_mask = ~df["product_id"].isin(["nan", "None", "", "null", "N/A"])
        valid_qty_mask = df["quantity"].notnull()
        valid_price_mask = (df["unit_price"].isnull()) | (df["unit_price"] >= 0)

        accepted_mask = valid_date_mask & valid_prod_mask & valid_qty_mask & valid_price_mask
        if not allow_returns:
            accepted_mask = accepted_mask & (~neg_qty_mask)

        flagged_mask = (~accepted_mask) | (neg_qty_mask & allow_returns)
        flagged_count = int(flagged_mask.sum())
        excluded_count = int((~accepted_mask).sum())

        cleaned_df = df[accepted_mask].copy()

        # Ensure unit price is non-null default 0.0 if still missing
        cleaned_df["unit_price"] = cleaned_df["unit_price"].fillna(0.0)
        # Ensure revenue is calculated
        cleaned_df["revenue"] = cleaned_df["revenue"].fillna(cleaned_df["quantity"] * cleaned_df["unit_price"])

        accepted_count = len(cleaned_df)

        self.quality_report = {
            "initial_rows": initial_count,
            "accepted_rows": accepted_count,
            "flagged_rows": flagged_count,
            "excluded_rows": excluded_count,
            "missing_dates": int(missing_dates),
            "missing_products": int(missing_products),
            "duplicate_records": int(duplicate_records),
            "negative_quantities": int(negative_qtys),
            "negative_prices": int(negative_prices),
            "imputed_quantities": int(qty_imputed),
            "imputed_revenues": int(rev_imputed),
            "imputed_prices": int(price_imputed),
            "returns_policy": "Retained as Net Returns" if allow_returns else "Excluded",
            "cleaning_actions": self.actions_taken
        }

        return cleaned_df, self.quality_report

    def clean_inventory_data(
        self,
        raw_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Clean uploaded inventory snapshot data."""
        df = raw_df.copy()
        initial_count = len(df)
        actions = []

        standard_cols_map = {}
        for std_key, orig_col in self.mapping.items():
            if orig_col and orig_col in df.columns:
                standard_cols_map[orig_col] = std_key
        df = df.rename(columns=standard_cols_map)

        if "product_id" not in df.columns and "product_name" in df.columns:
            df["product_id"] = df["product_name"]
        elif "product_name" not in df.columns and "product_id" in df.columns:
            df["product_name"] = df["product_id"]

        df["product_id"] = df["product_id"].astype(str).str.strip()
        df["product_name"] = df["product_name"].astype(str).str.strip()

        # Numerics
        df["stock"] = pd.to_numeric(df.get("stock", 0.0), errors="coerce").fillna(0.0)
        df["on_order"] = pd.to_numeric(df.get("on_order", 0.0), errors="coerce").fillna(0.0)
        df["lead_time"] = pd.to_numeric(df.get("lead_time", 7), errors="coerce").fillna(7).astype(int)
        df["min_order_qty"] = pd.to_numeric(df.get("min_order_qty", 1.0), errors="coerce").fillna(1.0)
        df["case_pack"] = pd.to_numeric(df.get("case_pack", 1.0), errors="coerce").fillna(1.0)

        # Flag negative stock
        neg_stock = int((df["stock"] < 0).sum())
        if neg_stock > 0:
            actions.append(f"Reset {neg_stock} negative stock values to 0.")
            df.loc[df["stock"] < 0, "stock"] = 0.0

        valid_mask = ~df["product_id"].isin(["nan", "None", "", "null", "N/A"])
        cleaned_df = df[valid_mask].copy()

        report = {
            "initial_rows": initial_count,
            "accepted_rows": len(cleaned_df),
            "excluded_rows": initial_count - len(cleaned_df),
            "negative_stock_fixed": neg_stock,
            "actions": actions
        }

        return cleaned_df, report
