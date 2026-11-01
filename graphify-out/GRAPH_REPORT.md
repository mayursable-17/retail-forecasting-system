# Graph Report - retail-forecasting-system  (2026-11-01)

## Corpus Check
- 47 files · ~42,211 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .csv 6, (none) 3)

## Summary
- 500 nodes · 1084 edges · 32 communities (17 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 77 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `22d9384e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- baseline.py
- Repository
- charts.py
- test_integration.py
- 2. Comprehensive Test Execution Matrix
- test_inventory.py
- Retail Sales Forecasting & Inventory Optimization System Using Machine Learning
- 1. Database Schema Specifications
- 3. Step-by-Step Walkthrough
- index.py
- Retail Sales Forecasting & Inventory Optimization System
- validation.py
- DataCleaner
- test_api.py
- test_forecasting.py
- test_upload.py
- train.py
- .train_and_evaluate
- vercel.json
- DemandModelTrainer
- pandas
- Retail Sales Forecasting & Inventory Optimization System
- VercelPathRewriteMiddleware

## God Nodes (most connected - your core abstractions)
1. `Repository` - 36 edges
2. `2. Comprehensive Test Execution Matrix` - 33 edges
3. `get_repo()` - 27 edges
4. `get_db_context()` - 25 edges
5. `seed_kirana_demo()` - 20 edges
6. `generate_mode_b_recommendations()` - 18 edges
7. `read_uploaded_file()` - 17 edges
8. `DemandModelTrainer` - 15 edges
9. `test_full_pipeline_integration()` - 15 edges
10. `generate_future_forecast()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `2. Comprehensive Test Execution Matrix` --references--> `test_aggregate_daily_sales_basic()`  [INFERRED]
  docs/test_plan.md → tests/test_aggregation.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_net_demand_non_negativity_with_excess_returns()`  [INFERRED]
  docs/test_plan.md → tests/test_aggregation.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_gap_filling_creates_zero_sales()`  [INFERRED]
  docs/test_plan.md → tests/test_aggregation.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_clean_missing_and_unparseable_dates()`  [INFERRED]
  docs/test_plan.md → tests/test_cleaning.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_clean_negative_quantities_as_returns()`  [INFERRED]
  docs/test_plan.md → tests/test_cleaning.py

## Import Cycles
- None detected.

## Communities (32 total, 15 thin omitted)

### Community 0 - "baseline.py"
Cohesion: 0.10
Nodes (4): CrostonIntermittentForecaster, ExponentialSmoothingForecaster, NaiveForecaster, SeasonalNaiveForecaster

### Community 1 - "Repository"
Cohesion: 0.06
Nodes (19): seed_kirana_demo(), _ensure_schema_migrations(), get_db_context(), get_engine(), get_session(), get_session_factory(), init_db(), ForecastResult (+11 more)

### Community 2 - "charts.py"
Cohesion: 0.22
Nodes (6): plot_category_distribution(), plot_forecast_vs_history(), plot_inventory_risk_pie(), plot_revenue_trend(), plot_top_products_bar(), plot_weekday_vs_weekend()

### Community 3 - "test_integration.py"
Cohesion: 0.13
Nodes (7): download_excel_report(), compute_overview_kpis(), format_excel_sheet(), generate_retail_master_excel(), compute_file_hash(), get_excel_sheet_names(), test_full_pipeline_integration()

### Community 4 - "2. Comprehensive Test Execution Matrix"
Cohesion: 0.12
Nodes (13): 2. Comprehensive Test Execution Matrix, FileReadError, read_uploaded_file(), test_forecast_and_recommendations_persistence(), test_inventory_snapshot_latest_query(), test_sales_daily_operations(), test_shop_and_products_operations(), test_baseline_forecasters() (+5 more)

### Community 5 - "test_inventory.py"
Cohesion: 0.12
Nodes (16): generate_mode_a_recommendations(), generate_mode_b_recommendations(), apply_order_constraints(), calculate_inventory_position(), calculate_order_up_to_target(), calculate_preliminary_order_quantity(), calculate_reorder_point(), calculate_safety_stock_buffer() (+8 more)

### Community 6 - "Retail Sales Forecasting & Inventory Optimization System Using Machine Learning"
Cohesion: 0.06
Nodes (30): 10.1 Vercel Serverless (Recommended), 10.2 Docker Containerization, 10. Deployment Guidelines, 11. Limitations & Future Work, 12. Academic Metadata, 1. Project Abstract, 2.1 The Problem, 2.2 Objectives (+22 more)

### Community 7 - "1. Database Schema Specifications"
Cohesion: 0.14
Nodes (13): 1. Database Schema Specifications, 2. Standard Column Mapping Synonyms Catalog, 3. Inventory Alert Status Definitions, Data Dictionary & Schema Specification, Retail Sales Forecasting & Inventory Optimization System, Table 1: `shops`, Table 2: `products`, Table 3: `uploads` (+5 more)

### Community 8 - "3. Step-by-Step Walkthrough"
Cohesion: 0.15
Nodes (12): 1. Introduction, 2. Navigating the Application, 3. Step-by-Step Walkthrough, Retail Sales Forecasting & Inventory Optimization System, Step 1: Loading Initial Data, Step 2: Uploading Your Own Spreadsheet, Step 3: Understanding Customer Returns & Data Health, Step 4: Generating Demand Forecasts (+4 more)

### Community 9 - "index.py"
Cohesion: 0.06
Nodes (40): add_product(), batch_update_products(), clear_all_data(), download_csv_report(), ForecastRequest, get_analytics_data(), get_dashboard_data(), get_index_html() (+32 more)

### Community 10 - "Retail Sales Forecasting & Inventory Optimization System"
Cohesion: 0.22
Nodes (8): 1. Architectural Overview, 2. Dual Inventory Workflow Architecture, 3. Database Entity Relationship (ER) Model, 4. Machine Learning & Forecasting Pipeline Details, 5. Inventory Optimization & Periodic Review Formulation, 6. Security & Safe Data Handling, Retail Sales Forecasting & Inventory Optimization System, System Architecture & Technical Design

### Community 12 - "DataCleaner"
Cohesion: 0.22
Nodes (5): DataCleaner, test_clean_duplicate_transactions(), test_clean_missing_and_unparseable_dates(), test_clean_negative_quantities_as_returns(), test_impute_missing_quantity_and_revenue()

### Community 23 - "test_forecasting.py"
Cohesion: 0.24
Nodes (8): calculate_bias(), calculate_mae(), calculate_rmse(), calculate_wape(), evaluate_forecast(), test_chronological_split_no_leakage(), test_evaluation_metrics_known_values(), test_wape_zero_actual_handling()

### Community 24 - "test_upload.py"
Cohesion: 0.22
Nodes (6): auto_detect_columns(), normalize_col_name(), validate_mapping(), test_column_auto_detection(), test_validate_mapping_missing_required(), test_validate_mapping_valid()

### Community 26 - ".train_and_evaluate"
Cohesion: 0.14
Nodes (5): MovingAverageForecaster, chronological_split(), DemandModelTrainer, NumpyRidgeRegressor, test_demand_model_trainer_and_predict()

### Community 30 - "pandas"
Cohesion: 0.35
Nodes (4): aggregate_daily_sales(), test_aggregate_daily_sales_basic(), test_gap_filling_creates_zero_sales(), test_net_demand_non_negativity_with_excess_returns()

### Community 31 - "Retail Sales Forecasting & Inventory Optimization System"
Cohesion: 0.40
Nodes (4): 1. Test Strategy & Objectives, 3. Execution Verification Record, Retail Sales Forecasting & Inventory Optimization System, Software Test Plan & Verification Matrix

## Knowledge Gaps
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Repository` connect `Repository` to `index.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Repository` (e.g. with `seed_kirana_demo()` and `ForecastResult`) actually correct?**
  _`Repository` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `baseline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Why does `seed_kirana_demo()` connect `Repository` to `test_inventory.py`, `index.py`, `.train_and_evaluate`, `DemandModelTrainer`, `pandas`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `2. Comprehensive Test Execution Matrix` (e.g. with `FileReadError` and `test_aggregate_daily_sales_basic()`) actually correct?**
  _`2. Comprehensive Test Execution Matrix` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.060833902939166094 - nodes in this community are weakly interconnected._
- **Why does `2. Comprehensive Test Execution Matrix` connect `2. Comprehensive Test Execution Matrix` to `test_integration.py`, `test_inventory.py`, `DataCleaner`, `test_forecasting.py`, `test_upload.py`, `train.py`, `.train_and_evaluate`, `pandas`, `Retail Sales Forecasting & Inventory Optimization System`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._