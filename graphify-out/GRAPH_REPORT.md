# Graph Report - retail-forecasting-system  (2026-10-27)

## Corpus Check
- 53 files · ~26,197 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: .csv 6, (none) 2)

## Summary
- 425 nodes · 977 edges · 22 communities (12 shown, 10 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ee2ce0d8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_forecasting.py
- Repository
- app.py
- pandas
- 2. Comprehensive Test Execution Matrix
- test_inventory.py
- Retail Sales Forecasting & Inventory Optimization System Using Machine Learning
- 1. Database Schema Specifications
- 3. Step-by-Step Walkthrough
- excel_report.py
- Retail Sales Forecasting & Inventory Optimization System
- validation.py
- Retail Sales Forecasting & Inventory Optimization System

## God Nodes (most connected - your core abstractions)
1. `2. Comprehensive Test Execution Matrix` - 33 edges
2. `Repository` - 31 edges
3. `get_db_context()` - 21 edges
4. `generate_mode_b_recommendations()` - 16 edges
5. `read_uploaded_file()` - 15 edges
6. `test_full_pipeline_integration()` - 15 edges
7. `get_active_shop()` - 14 edges
8. `DemandModelTrainer` - 13 edges
9. `get_shared_repo()` - 13 edges
10. `Retail Sales Forecasting & Inventory Optimization System Using Machine Learning` - 13 edges

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

## Communities (22 total, 10 thin omitted)

### Community 0 - "test_forecasting.py"
Cohesion: 0.06
Nodes (17): CrostonIntermittentForecaster, ExponentialSmoothingForecaster, MovingAverageForecaster, NaiveForecaster, SeasonalNaiveForecaster, calculate_bias(), calculate_mae(), calculate_rmse() (+9 more)

### Community 1 - "Repository"
Cohesion: 0.08
Nodes (17): get_db_context(), get_engine(), get_session(), get_session_factory(), init_db(), ForecastResult, ForecastRun, InventorySnapshot (+9 more)

### Community 2 - "app.py"
Cohesion: 0.10
Nodes (11): plot_category_distribution(), plot_forecast_vs_history(), plot_inventory_risk_pie(), plot_revenue_trend(), plot_top_products_bar(), plot_weekday_vs_weekend(), generate_all_samples(), get_active_shop() (+3 more)

### Community 3 - "pandas"
Cohesion: 0.07
Nodes (18): compute_category_breakdown(), compute_overview_kpis(), compute_weekday_weekend_stats(), get_top_and_bottom_products(), generate_future_forecast(), DemandModelTrainer, auto_detect_columns(), aggregate_daily_sales() (+10 more)

### Community 4 - "2. Comprehensive Test Execution Matrix"
Cohesion: 0.09
Nodes (18): 2. Comprehensive Test Execution Matrix, normalize_col_name(), validate_mapping(), compute_file_hash(), FileReadError, get_excel_sheet_names(), read_uploaded_file(), test_forecast_and_recommendations_persistence() (+10 more)

### Community 5 - "test_inventory.py"
Cohesion: 0.11
Nodes (17): generate_mode_a_recommendations(), generate_mode_b_recommendations(), apply_order_constraints(), calculate_inventory_position(), calculate_order_up_to_target(), calculate_preliminary_order_quantity(), calculate_reorder_point(), calculate_safety_stock_buffer() (+9 more)

### Community 6 - "Retail Sales Forecasting & Inventory Optimization System Using Machine Learning"
Cohesion: 0.07
Nodes (28): 10.1 Streamlit Community Cloud, 10.2 Docker Containerization, 10. Deployment Guidelines, 11. Limitations & Future Work, 12. Academic Metadata, 1. Project Abstract, 2.1 The Problem, 2.2 Objectives (+20 more)

### Community 7 - "1. Database Schema Specifications"
Cohesion: 0.14
Nodes (13): 1. Database Schema Specifications, 2. Standard Column Mapping Synonyms Catalog, 3. Inventory Alert Status Definitions, Data Dictionary & Schema Specification, Retail Sales Forecasting & Inventory Optimization System, Table 1: `shops`, Table 2: `products`, Table 3: `uploads` (+5 more)

### Community 8 - "3. Step-by-Step Walkthrough"
Cohesion: 0.15
Nodes (12): 1. Introduction, 2. Navigating the Application, 3. Step-by-Step Walkthrough, Retail Sales Forecasting & Inventory Optimization System, Step 1: Loading Initial Data, Step 2: Uploading Your Own Spreadsheet, Step 3: Understanding Customer Returns & Data Health, Step 4: Generating Demand Forecasts (+4 more)

### Community 9 - "excel_report.py"
Cohesion: 0.20
Nodes (3): convert_df_to_csv_bytes(), format_excel_sheet(), generate_retail_master_excel()

### Community 10 - "Retail Sales Forecasting & Inventory Optimization System"
Cohesion: 0.22
Nodes (8): 1. Architectural Overview, 2. Dual Inventory Workflow Architecture, 3. Database Entity Relationship (ER) Model, 4. Machine Learning & Forecasting Pipeline Details, 5. Inventory Optimization & Periodic Review Formulation, 6. Security & Safe Data Handling, Retail Sales Forecasting & Inventory Optimization System, System Architecture & Technical Design

### Community 12 - "Retail Sales Forecasting & Inventory Optimization System"
Cohesion: 0.40
Nodes (4): 1. Test Strategy & Objectives, 3. Execution Verification Record, Retail Sales Forecasting & Inventory Optimization System, Software Test Plan & Verification Matrix

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Repository` connect `Repository` to `app.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `2. Comprehensive Test Execution Matrix` (e.g. with `FileReadError` and `test_aggregate_daily_sales_basic()`) actually correct?**
  _`2. Comprehensive Test Execution Matrix` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_forecasting.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0579476861167002 - nodes in this community are weakly interconnected._
- **Why does `2. Comprehensive Test Execution Matrix` connect `2. Comprehensive Test Execution Matrix` to `test_forecasting.py`, `pandas`, `Retail Sales Forecasting & Inventory Optimization System`, `test_inventory.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Repository` (e.g. with `ForecastResult` and `ForecastRun`) actually correct?**
  _`Repository` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.07615018508725542 - nodes in this community are weakly interconnected._
- **Why does `test_full_pipeline_integration()` connect `pandas` to `test_forecasting.py`, `excel_report.py`, `2. Comprehensive Test Execution Matrix`, `test_inventory.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._