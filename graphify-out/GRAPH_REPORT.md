# Graph Report - retail-forecasting-system  (2026-10-28)

## Corpus Check
- 47 files · ~30,820 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .csv 6, (none) 3)

## Summary
- 481 nodes · 1047 edges · 24 communities (12 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `829b8176`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_forecasting.py
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
- pandas
- test_api.py
- vercel.json

## God Nodes (most connected - your core abstractions)
1. `Repository` - 36 edges
2. `2. Comprehensive Test Execution Matrix` - 33 edges
3. `get_repo()` - 27 edges
4. `get_db_context()` - 25 edges
5. `read_uploaded_file()` - 17 edges
6. `generate_mode_b_recommendations()` - 17 edges
7. `test_full_pipeline_integration()` - 15 edges
8. `DemandModelTrainer` - 14 edges
9. `Retail Sales Forecasting & Inventory Optimization System Using Machine Learning` - 14 edges
10. `generate_future_forecast()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `2. Comprehensive Test Execution Matrix` --references--> `test_clean_missing_and_unparseable_dates()`  [INFERRED]
  docs/test_plan.md → tests/test_cleaning.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_clean_negative_quantities_as_returns()`  [INFERRED]
  docs/test_plan.md → tests/test_cleaning.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_clean_duplicate_transactions()`  [INFERRED]
  docs/test_plan.md → tests/test_cleaning.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_impute_missing_quantity_and_revenue()`  [INFERRED]
  docs/test_plan.md → tests/test_cleaning.py
- `2. Comprehensive Test Execution Matrix` --references--> `test_shop_and_products_operations()`  [INFERRED]
  docs/test_plan.md → tests/test_database.py

## Import Cycles
- None detected.

## Communities (24 total, 12 thin omitted)

### Community 0 - "test_forecasting.py"
Cohesion: 0.05
Nodes (20): CrostonIntermittentForecaster, ExponentialSmoothingForecaster, MovingAverageForecaster, NaiveForecaster, SeasonalNaiveForecaster, calculate_bias(), calculate_mae(), calculate_rmse() (+12 more)

### Community 1 - "Repository"
Cohesion: 0.06
Nodes (19): seed_kirana_demo(), _ensure_schema_migrations(), get_db_context(), get_engine(), get_session(), get_session_factory(), init_db(), ForecastResult (+11 more)

### Community 2 - "charts.py"
Cohesion: 0.22
Nodes (6): plot_category_distribution(), plot_forecast_vs_history(), plot_inventory_risk_pie(), plot_revenue_trend(), plot_top_products_bar(), plot_weekday_vs_weekend()

### Community 3 - "test_integration.py"
Cohesion: 0.08
Nodes (9): compute_overview_kpis(), convert_df_to_csv_bytes(), format_excel_sheet(), generate_retail_master_excel(), generate_future_forecast(), auto_detect_columns(), normalize_col_name(), test_full_pipeline_integration() (+1 more)

### Community 4 - "2. Comprehensive Test Execution Matrix"
Cohesion: 0.07
Nodes (24): 1. Test Strategy & Objectives, 2. Comprehensive Test Execution Matrix, 3. Execution Verification Record, Retail Sales Forecasting & Inventory Optimization System, Software Test Plan & Verification Matrix, validate_mapping(), compute_file_hash(), FileReadError (+16 more)

### Community 5 - "test_inventory.py"
Cohesion: 0.11
Nodes (17): generate_mode_a_recommendations(), generate_mode_b_recommendations(), apply_order_constraints(), calculate_inventory_position(), calculate_order_up_to_target(), calculate_preliminary_order_quantity(), calculate_reorder_point(), calculate_safety_stock_buffer() (+9 more)

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
Cohesion: 0.08
Nodes (36): add_product(), batch_update_products(), clear_all_data(), download_csv_report(), download_excel_report(), ForecastRequest, get_analytics_data(), get_dashboard_data() (+28 more)

### Community 10 - "Retail Sales Forecasting & Inventory Optimization System"
Cohesion: 0.22
Nodes (8): 1. Architectural Overview, 2. Dual Inventory Workflow Architecture, 3. Database Entity Relationship (ER) Model, 4. Machine Learning & Forecasting Pipeline Details, 5. Inventory Optimization & Periodic Review Formulation, 6. Security & Safe Data Handling, Retail Sales Forecasting & Inventory Optimization System, System Architecture & Technical Design

### Community 12 - "pandas"
Cohesion: 0.21
Nodes (6): process_upload(), DataCleaner, test_clean_duplicate_transactions(), test_clean_missing_and_unparseable_dates(), test_clean_negative_quantities_as_returns(), test_impute_missing_quantity_and_revenue()

## Knowledge Gaps
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Repository` connect `Repository` to `index.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Repository` (e.g. with `seed_kirana_demo()` and `ForecastResult`) actually correct?**
  _`Repository` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_forecasting.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05034199726402189 - nodes in this community are weakly interconnected._
- **Why does `2. Comprehensive Test Execution Matrix` connect `2. Comprehensive Test Execution Matrix` to `test_forecasting.py`, `test_integration.py`, `pandas`, `test_inventory.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `2. Comprehensive Test Execution Matrix` (e.g. with `FileReadError` and `test_aggregate_daily_sales_basic()`) actually correct?**
  _`2. Comprehensive Test Execution Matrix` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.059125085440874914 - nodes in this community are weakly interconnected._
- **Why does `DemandModelTrainer` connect `test_forecasting.py` to `index.py`, `test_integration.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._