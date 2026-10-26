# Software Test Plan & Verification Matrix

## Retail Sales Forecasting & Inventory Optimization System

---

### 1. Test Strategy & Objectives

The test suite validates data ingestion integrity, cleaning audit reliability, time-series feature engineering causality, forecasting out-of-sample accuracy, and inventory optimization formulas against analytical proofs.

- **Framework:** Pytest 9.1.1
- **Target Platform:** Windows 10/11 x64, Python 3.13.7
- **Database Engine for Tests:** SQLite isolated test instances via pytest `tmp_path` fixture.
- **Pass Criteria:** 100% pass rate across all unit, functional, mathematical, and integration tests.

---

### 2. Comprehensive Test Execution Matrix

| # | Test Identifier | Module Under Test | Description & Assertions | Status |
| :- | :--- | :--- | :--- | :--- |
| **1** | `test_read_valid_csv` | Ingestion | Validates safe ingestion of well-formed CSV file and metadata extraction. | **PASSED** |
| **2** | `test_read_empty_csv` | Ingestion | Asserts that empty file triggers `FileReadError` rather than crashing. | **PASSED** |
| **3** | `test_unsupported_file_extension` | Ingestion | Asserts that unsupported extensions (`.txt`, `.exe`) are rejected. | **PASSED** |
| **4** | `test_read_valid_xlsx` | Ingestion | Tests Excel ingestion using `openpyxl` with `data_only=True`. | **PASSED** |
| **5** | `test_column_auto_detection` | Ingestion | Verifies automatic synonym matching for dates, SKU, price, quantity, and revenue. | **PASSED** |
| **6** | `test_validate_mapping_valid` | Ingestion | Confirms mapping passes when all mandatory keys are mapped. | **PASSED** |
| **7** | `test_validate_mapping_missing_required` | Ingestion | Validates error reporting when Date or Product identifiers are absent. | **PASSED** |
| **8** | `test_clean_missing_and_unparseable_dates`| Cleaning | Verifies exclusion of missing and invalid dates, and accurate audit count. | **PASSED** |
| **9** | `test_clean_negative_quantities_as_returns`| Cleaning | Tests dual policy: retaining returns for net demand vs excluding them. | **PASSED** |
| **10**| `test_clean_duplicate_transactions` | Cleaning | Asserts exact duplicate transaction rows are deduplicated to prevent double-counting. | **PASSED** |
| **11**| `test_impute_missing_quantity_and_revenue` | Cleaning | Tests safe imputation: $Qty = Rev / Price$ and $Rev = Qty \times Price$. | **PASSED** |
| **12**| `test_aggregate_daily_sales_basic` | Aggregation | Verifies daily sales aggregation by product and date with correct ASP. | **PASSED** |
| **13**| `test_net_demand_non_negativity_with_excess_returns` | Aggregation | Asserts physical demand is clipped to $\ge 0$ if returns exceed daily sales. | **PASSED** |
| **14**| `test_gap_filling_creates_zero_sales` | Aggregation | Validates smart gap filling (creates explicit 0 sales during active period). | **PASSED** |
| **15**| `test_evaluation_metrics_known_values` | Forecasting | Validates MAE, RMSE, WAPE, and Bias against known hand-calculated values. | **PASSED** |
| **16**| `test_wape_zero_actual_handling` | Forecasting | Asserts WAPE handles zero-actual demand safely without division by zero. | **PASSED** |
| **17**| `test_chronological_split_no_leakage` | Forecasting | Verifies train and validation split is strictly chronological (no shuffling). | **PASSED** |
| **18**| `test_feature_engineering_strictly_causal` | Forecasting | Confirms features (lags, rolling stats) do not leak current or future target values. | **PASSED** |
| **19**| `test_baseline_forecasters` | Forecasting | Tests Naive and 3-day Moving Average forecast algorithms. | **PASSED** |
| **20**| `test_demand_model_trainer_and_predict` | Forecasting | Tests trainer pipeline, best model selection, and non-negative future projections. | **PASSED** |
| **21**| `test_inventory_position_formula` | Inventory | Verifies $IP = OnHand + OnOrder - Backorders$ ($50 + 20 - 5 = 65$). | **PASSED** |
| **22**| `test_safety_stock_variability_analytical_proof`| Inventory | Analytical proof: $z=1.645, \sigma=3, L=4 \implies \lceil 1.645 \times 3 \times 2 \rceil = 10$. | **PASSED** |
| **23**| `test_reorder_point_and_order_up_to_target` | Inventory | Tests continuous $ROP = D_L + SS$ and periodic target $S = D_{L+R} + SS$. | **PASSED** |
| **24**| `test_moq_and_case_pack_rounding` | Inventory | Tests supplier constraint adjustments (rounding to MOQ and case-pack multiples). | **PASSED** |
| **25**| `test_mode_a_recommendations_sales_only` | Inventory | Asserts Workflow A flags unknown stock and never makes false stockout claims. | **PASSED** |
| **26**| `test_mode_b_recommendations_full` | Inventory | Tests Workflow B end-to-end with stock, order-up-to, and pack size rounding. | **PASSED** |
| **27**| `test_shop_and_products_operations` | Database | Tests SQLAlchemy shop retrieval, product upsert, and catalog queries. | **PASSED** |
| **28**| `test_sales_daily_operations` | Database | Tests daily sales persistence, upload session linking, and aggregations. | **PASSED** |
| **29**| `test_inventory_snapshot_latest_query` | Database | Verifies latest snapshot query returns most recent timestamp per product. | **PASSED** |
| **30**| `test_forecast_and_recommendations_persistence`| Database | Tests saving and querying forecast runs, metrics JSON, and recommendations. | **PASSED** |
| **31**| `test_full_pipeline_integration` | Integration | End-to-end integration: Raw messy CSV $\to$ Clean $\to$ Aggregate $\to$ DB $\to$ Forecast $\to$ Inventory Mode B $\to$ Multi-Sheet Excel Workbook. | **PASSED** |

---

### 3. Execution Verification Record

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\MAYUR\.gemini\antigravity\scratch\retail-forecasting-system
plugins: anyio-4.15.1
collected 31 items

tests/test_aggregation.py::test_aggregate_daily_sales_basic PASSED       [  3%]
tests/test_aggregation.py::test_net_demand_non_negativity_with_excess_returns PASSED [  6%]
tests/test_aggregation.py::test_gap_filling_creates_zero_sales PASSED    [  9%]
tests/test_cleaning.py::test_clean_missing_and_unparseable_dates PASSED  [ 12%]
tests/test_cleaning.py::test_clean_negative_quantities_as_returns PASSED [ 16%]
tests/test_cleaning.py::test_clean_duplicate_transactions PASSED         [ 19%]
tests/test_cleaning.py::test_impute_missing_quantity_and_revenue PASSED  [ 22%]
tests/test_database.py::test_shop_and_products_operations PASSED         [ 25%]
tests/test_database.py::test_sales_daily_operations PASSED               [ 29%]
tests/test_database.py::test_inventory_snapshot_latest_query PASSED      [ 32%]
tests/test_database.py::test_forecast_and_recommendations_persistence PASSED [ 35%]
tests/test_forecasting.py::test_evaluation_metrics_known_values PASSED   [ 38%]
tests/test_forecasting.py::test_wape_zero_actual_handling PASSED         [ 41%]
tests/test_forecasting.py::test_chronological_split_no_leakage PASSED    [ 45%]
tests/test_forecasting.py::test_feature_engineering_strictly_causal PASSED [ 48%]
tests/test_forecasting.py::test_baseline_forecasters PASSED              [ 51%]
tests/test_forecasting.py::test_demand_model_trainer_and_predict PASSED  [ 54%]
tests/test_integration.py::test_full_pipeline_integration PASSED         [ 58%]
tests/test_inventory.py::test_inventory_position_formula PASSED          [ 61%]
tests/test_inventory.py::test_safety_stock_variability_analytical_proof PASSED [ 64%]
tests/test_inventory.py::test_reorder_point_and_order_up_to_target PASSED [ 67%]
tests/test_inventory.py::test_moq_and_case_pack_rounding PASSED          [ 70%]
tests/test_inventory.py::test_mode_a_recommendations_sales_only PASSED   [ 74%]
tests/test_inventory.py::test_mode_b_recommendations_full PASSED         [ 77%]
tests/test_upload.py::test_read_valid_csv PASSED                         [ 80%]
tests/test_upload.py::test_read_empty_csv PASSED                         [ 83%]
tests/test_upload.py::test_unsupported_file_extension PASSED             [ 87%]
tests/test_upload.py::test_read_valid_xlsx PASSED                        [ 90%]
tests/test_upload.py::test_column_auto_detection PASSED                  [ 93%]
tests/test_upload.py::test_validate_mapping_valid PASSED                 [ 96%]
tests/test_upload.py::test_validate_mapping_missing_required PASSED      [100%]

============================= 31 passed in 3.12s ==============================
```
