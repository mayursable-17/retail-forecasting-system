# Graph Report - retail-forecasting-system  (2026-11-01)

## Corpus Check
- 47 files · ~41,937 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .csv 6, (none) 3)

## Summary
- 494 nodes · 1077 edges · 27 communities (13 shown, 14 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 77 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4b43cf69`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- baseline.py
- Repository
- charts.py
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
- test_forecasting.py
- train.py
- .train_and_evaluate
- vercel.json
- DemandModelTrainer

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

## Communities (27 total, 14 thin omitted)

### Community 0 - "baseline.py"
Cohesion: 0.09
Nodes (6): CrostonIntermittentForecaster, ExponentialSmoothingForecaster, MovingAverageForecaster, NaiveForecaster, SeasonalNaiveForecaster, test_baseline_forecasters()

### Community 1 - "Repository"
Cohesion: 0.06
Nodes (19): seed_kirana_demo(), _ensure_schema_migrations(), get_db_context(), get_engine(), get_session(), get_session_factory(), init_db(), ForecastResult (+11 more)

### Community 2 - "charts.py"
Cohesion: 0.22
Nodes (6): plot_category_distribution(), plot_forecast_vs_history(), plot_inventory_risk_pie(), plot_revenue_trend(), plot_top_products_bar(), plot_weekday_vs_weekend()

### Community 4 - "2. Comprehensive Test Execution Matrix"
Cohesion: 0.07
Nodes (23): 1. Test Strategy & Objectives, 2. Comprehensive Test Execution Matrix, 3. Execution Verification Record, Retail Sales Forecasting & Inventory Optimization System, Software Test Plan & Verification Matrix, auto_detect_columns(), normalize_col_name(), validate_mapping() (+15 more)

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
Cohesion: 0.07
Nodes (39): add_product(), batch_update_products(), clear_all_data(), download_csv_report(), download_excel_report(), ForecastRequest, get_analytics_data(), get_dashboard_data() (+31 more)

### Community 10 - "Retail Sales Forecasting & Inventory Optimization System"
Cohesion: 0.22
Nodes (8): 1. Architectural Overview, 2. Dual Inventory Workflow Architecture, 3. Database Entity Relationship (ER) Model, 4. Machine Learning & Forecasting Pipeline Details, 5. Inventory Optimization & Periodic Review Formulation, 6. Security & Safe Data Handling, Retail Sales Forecasting & Inventory Optimization System, System Architecture & Technical Design

### Community 12 - "pandas"
Cohesion: 0.08
Nodes (15): process_upload(), _sanitize_for_json(), convert_df_to_csv_bytes(), format_excel_sheet(), generate_retail_master_excel(), aggregate_daily_sales(), DataCleaner, test_aggregate_daily_sales_basic() (+7 more)

### Community 23 - "test_forecasting.py"
Cohesion: 0.24
Nodes (8): calculate_bias(), calculate_mae(), calculate_rmse(), calculate_wape(), evaluate_forecast(), test_chronological_split_no_leakage(), test_evaluation_metrics_known_values(), test_wape_zero_actual_handling()

### Community 29 - "DemandModelTrainer"
Cohesion: 0.22
Nodes (3): generate_future_forecast(), DemandModelTrainer, test_demand_model_trainer_and_predict()

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Repository` connect `Repository` to `index.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Repository` (e.g. with `seed_kirana_demo()` and `ForecastResult`) actually correct?**
  _`Repository` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `baseline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08735632183908046 - nodes in this community are weakly interconnected._
- **Why does `seed_kirana_demo()` connect `Repository` to `test_inventory.py`, `index.py`, `pandas`, `.train_and_evaluate`, `DemandModelTrainer`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `2. Comprehensive Test Execution Matrix` (e.g. with `FileReadError` and `test_aggregate_daily_sales_basic()`) actually correct?**
  _`2. Comprehensive Test Execution Matrix` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.060833902939166094 - nodes in this community are weakly interconnected._
- **Why does `2. Comprehensive Test Execution Matrix` connect `2. Comprehensive Test Execution Matrix` to `baseline.py`, `test_inventory.py`, `pandas`, `test_forecasting.py`, `train.py`, `DemandModelTrainer`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._