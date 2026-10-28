# Retail Sales Forecasting & Inventory Optimization System Using Machine Learning

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/mayursable-17/retail-forecasting-system)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black.svg?logo=vercel&logoColor=white)](https://vercel.com)
[![Framework](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-003B57.svg)](https://www.sqlalchemy.org/)
[![Machine Learning](https://img.shields.io/badge/ML-XGBoost%20%7C%20Scikit--Learn-F7931E.svg)](https://xgboost.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-42%20Passed%20%28100%25%29-brightgreen.svg)](tests/)

---

## 🌐 Live Application & 1-Click Vercel Deployment

Deploy and run this project live on Vercel with a single click:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/mayursable-17/retail-forecasting-system)

### How to Deploy Your Own Live Instance on Vercel:

1. **Option A: 1-Click Button (Fastest)**
   - Click the **Deploy with Vercel** button above.
   - Connect your GitHub account and select your repository: `mayursable-17/retail-forecasting-system`.
   - Vercel automatically detects `vercel.json` and builds the `@vercel/python` serverless deployment.
   - Your live public URL (e.g. `https://retail-forecasting-system.vercel.app`) is generated in under 60 seconds!

2. **Option B: Vercel Dashboard Import**
   - Log into [vercel.com](https://vercel.com).
   - Click **Add New...** -> **Project**.
   - Select `mayursable-17/retail-forecasting-system` from your GitHub repos.
   - Leave default settings unchanged (`vercel.json` handles routing and runtime).
   - Click **Deploy**.

3. **Option C: Vercel CLI**
   ```bash
   npm i -g vercel
   vercel
   ```

> [!NOTE]
> The backend automatically detects the Vercel serverless environment (`VERCEL=1`) and routes ephemeral database writes to `/tmp/db/retail_inventory.db` to adhere to Vercel's read-only serverless filesystem. For permanent database persistence across cold starts, simply set `DATABASE_URL=postgresql://user:pass@host:5432/db` (e.g. Neon, Supabase, or AWS RDS) in your Vercel Project Environment Variables.

---

## 1. Project Abstract

Small and medium-sized retail enterprises (such as neighbourhood kirana stores, apparel boutiques, stationery vendors, and general merchants) operate under thin margins and unpredictable consumer demand patterns. Inefficient inventory management leads to two critical problems: stockouts that forfeit sales and damage customer loyalty, and overstocking that ties up operating capital in depreciating or perishable goods.

This project delivers a **Retail Sales Forecasting & Inventory Optimization System** designed specifically for small business retailers. The system provides an automated pipeline that ingests arbitrary store spreadsheets, executes data cleaning and return auditing, builds causal machine learning demand forecasting models via chronological out-of-sample validation, and applies inventory optimization algorithms based on $(R, s, S)$ periodic review replenishment policies.

---

## 2. Problem Statement & Objectives

### 2.1 The Problem
Small retailers face major hurdles when attempting to utilize modern analytics:
- **Disorganized Data Formats:** Sales data is tracked in heterogeneous, unstandardized Excel or CSV sheets with inconsistent headers (`Qty`, `Quantity`, `Units Sold`).
- **Data Quality Anomalies:** Real retail data contains customer returns (negative quantities), unparseable dates, and missing keys.
- **Intermittent & Seasonal Demand:** Retail goods exhibit weekly seasonality, weekend spikes, and sparse demand that break standard linear assumptions.
- **Asymmetric Stock Knowledge:** Many retailers track sales but lack real-time digital inventory balances.

### 2.2 Objectives
1. **Intelligent Ingestion:** Accept `.csv` and `.xlsx` spreadsheets, auto-detect column semantics using synonym catalogs, and allow manual confirmation.
2. **Robust Cleaning & Audit Trail:** Distinguish customer returns from bad data, prevent double-counting of duplicate transactions, and produce transparent data quality audit reports.
3. **Dual Inventory Workflows:** Support both **Workflow A** (sales-only gross requirement estimation with clear caveats) and **Workflow B** (full inventory optimization with safety stock and reorder points).
4. **Time-Series Machine Learning:** Implement and benchmark Naive baselines, Seasonal Naive, Moving Averages, Exponential Smoothing, and XGBoost regressor using strictly chronological out-of-sample holdout validation without target leakage.
5. **Supply Chain Optimization:** Formulate Reorder Points ($ROP$), Safety Stock ($SS$) via normal distribution variability ($z \times \sigma_d \times \sqrt{L}$), Order-up-to Targets ($S$), and supplier MOQ/case pack constraints.
6. **Production-Ready Web Architecture:** Full-stack high-performance FastAPI server with modern Tailwind CSS responsive single-page dashboard, interactive Plotly charts, and formatted multi-sheet Excel exports deployed on Vercel Serverless.

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.11, 3.12, 3.13 | Core runtime environment |
| **Backend & Web Framework** | FastAPI & Uvicorn | $\ge 0.110.0$ | Async ASGI web API & serverless endpoints |
| **Cloud Deployment** | Vercel Serverless Functions | `@vercel/python` | Global serverless deployment via `vercel.json` |
| **Frontend UI** | Tailwind CSS & Modern HTML5 SPA | CDN / ES6 | Responsive, tabbed storekeeper dashboard |
| **Data Visualization** | Plotly.js | $\ge 2.29.0$ | Interactive analytical, Pareto, and forecast charts |
| **Data Processing** | Pandas, NumPy | $\ge 2.0.0$ | DataFrames, matrix math, aggregation, date indexing |
| **Spreadsheet Engine** | openpyxl | $\ge 3.1.0$ | Safe formula-isolated Excel read/write |
| **Machine Learning** | XGBoost, Scikit-learn, Statsmodels | $\ge 2.0.0$ | Boosted trees, Random Forests, statistical baselines |
| **ORM & Database** | SQLAlchemy, SQLite | $\ge 2.0.0$ | Relational data persistence, PostgreSQL-ready |
| **Test Automation** | Pytest, HTTPX / TestClient | $\ge 8.0.0$ | Automated unit, mathematical, and API integration tests |

---

## 4. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Browser (Single-Page Application)"]
        UI["Tailwind CSS + Plotly.js SPA (templates/index.html)"]
        Tab1["Overview Dashboard"]
        Tab2["Upload & Smart Mapper"]
        Tab3["Data Quality & Anomaly Audit"]
        Tab4["Sales & ABC Pareto Analytics"]
        Tab5["ML Forecasting & What-If Simulator"]
        Tab6["Inventory Optimization & PO Calc"]
        Tab7["Product Catalog & Live Stock Take"]
        Tab8["Reports & Excel Export"]
        Tab9["Store Settings & SLA Rules"]
        UI --> Tab1 & Tab2 & Tab3 & Tab4 & Tab5 & Tab6 & Tab7 & Tab8 & Tab9
    end

    subgraph ServerlessGateway ["Vercel Serverless Gateway"]
        VercelRoute["vercel.json Routing"]
        API["FastAPI Entrypoint (api/index.py)"]
        VercelRoute --> API
    end

    subgraph Ingestion ["Ingestion & Preprocessing Engine"]
        Reader["file_reader.py (CSV / XLSX data_only)"]
        Mapper["column_mapper.py (Synonym Auto-Detection)"]
        Cleaner["cleaning.py (Anomalies, Returns, Imputation)"]
        Aggregator["aggregation.py (Daily Normalization & Zero Filling)"]
    end

    subgraph Forecasting ["Forecasting & Machine Learning Engine"]
        Trainer["train.py (Chronological Split & Benchmarking)"]
        Features["features.py (Strict Non-Leaking Lags & Rolling Stats)"]
        Models["baseline.py & ML (Naive, SES, MA, XGBoost, RF)"]
        Evaluator["evaluate.py (MAE, RMSE, WAPE, Bias)"]
        Predictor["predict.py (Multi-Step Recursive Horizon Projections)"]
    end

    subgraph Optimization ["Inventory Optimization Engine"]
        SafetyStock["safety_stock.py (Variability: z * σ_d * √L / Fixed Buffer)"]
        ROP["reorder_point.py (ROP = D_L + SS, S = D_L+R + SS, MOQ, Packs)"]
        Recommender["recommendations.py (Workflow A & Workflow B Logic)"]
    end

    subgraph DataAccess ["Persistence Layer"]
        Repo["repository.py (DAO)"]
        ORM["models.py (SQLAlchemy Schema)"]
        DB[(SQLite / PostgreSQL Engine)]
    end

    UI <-->|JSON REST API| API
    API --> Reader --> Mapper --> Cleaner --> Aggregator --> Repo
    Repo --> ORM --> DB
    API --> Repo
    API --> Trainer --> Features --> Models --> Evaluator
    Trainer --> Predictor --> Repo
    API --> Recommender --> SafetyStock
    Recommender --> ROP --> Repo
```

---

## 5. Mathematical Formulations

### 5.1 Demand Forecasting Models
1. **Simple Naive Baseline:**
   $$\hat{y}_{t+h} = y_t$$
2. **Seasonal Naive (Weekly Seasonality $s = 7$):**
   $$\hat{y}_{t+h} = y_{t + h - s \cdot k}$$
3. **Simple Moving Average ($k = 7$):**
   $$\hat{y}_{t+h} = \frac{1}{k} \sum_{i=0}^{k-1} y_{t-i}$$
4. **Simple Exponential Smoothing ($\alpha \in [0.1, 0.5]$):**
   $$\ell_t = \alpha y_t + (1 - \alpha) \ell_{t-1}, \quad \hat{y}_{t+h} = \ell_t$$
5. **XGBoost Auto-Regressive Regressor:**
   $$\hat{y}_{t} = f\left(\text{lag}_1, \text{lag}_7, \text{lag}_{14}, \text{lag}_{28}, \text{roll}_7, \text{std}_7, \text{dayofweek}, \text{is\_weekend}, \text{month}\right)$$
   Features are constructed strictly causally without data leakage. Multi-step forecasts are projected via recursive autoregression, with negative predictions clipped to $\ge 0$.

### 5.2 Out-of-Sample Evaluation Metrics
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
- **Weighted Absolute Percentage Error (WAPE):**
  $$\text{WAPE} = \frac{\sum_{i=1}^n |y_i - \hat{y}_i|}{\sum_{i=1}^n y_i} \times 100\%$$
- **Forecast Bias:**
  $$\text{Bias} = \frac{\sum_{i=1}^n (\hat{y}_i - y_i)}{\sum_{i=1}^n y_i} \times 100\%$$

### 5.3 Inventory Optimization $(R, s, S)$ Formulations
1. **Inventory Position ($IP$):**
   $$IP = \text{On-Hand Stock} + \text{On-Order Units} - \text{Backorders}$$
2. **Statistical Safety Stock ($SS$):**
   $$SS = \lceil z \times \sigma_d \times \sqrt{L} \rceil$$
   *(Where $z$ is the standard normal z-score for the target service level, e.g., $z=1.645$ for 95%, $\sigma_d$ is daily demand standard deviation, and $L$ is lead time in days).*
3. **Reorder Point ($ROP$):**
   $$ROP = D_L + SS, \quad \text{where } D_L = \sum_{t=1}^L \hat{y}_t$$
4. **Order-up-to Target ($S$):**
   $$S = D_{L+R} + SS, \quad \text{where } D_{L+R} = \sum_{t=1}^{L+R} \hat{y}_t$$
5. **Preliminary Order Quantity ($O_{\text{prelim}}$):**
   $$O_{\text{prelim}} = \begin{cases} \max(0, S - IP) & \text{if } IP \le ROP \\ 0 & \text{if } IP > ROP \end{cases}$$
6. **Packaging Constraints:**
   - MOQ check: if $0 < O_{\text{prelim}} < \text{MOQ}$, order is adjusted to $\text{MOQ}$.
   - Case pack rounding:
     $$O_{\text{final}} = \lceil \frac{O_{\text{prelim}}}{\text{Pack Size}} \rceil \times \text{Pack Size}$$

---

## 6. Project Structure

```
retail-forecasting-system/
│
├── vercel.json                 # Vercel Serverless Function & routing configuration
├── requirements.txt            # Python dependencies (FastAPI, ML, SQLAlchemy)
├── README.md                   # Academic and operational documentation
├── .gitignore                  # Git ignore rules
│
├── api/                        # Serverless API layer
│   └── index.py                # FastAPI entrypoint, REST endpoints & Vercel handler
│
├── templates/                  # Frontend single-page application
│   └── index.html              # Responsive Tailwind CSS, Plotly.js & vanilla JS UI
│
├── src/                        # Modular service packages
│   ├── config.py               # Constants, thresholds, and Vercel /tmp path routing
│   ├── generate_samples.py     # Synthetic retail data generation script
│   ├── ingestion/              # File reader, column mapper, schema validation
│   ├── preprocessing/          # Cleaning, anomaly audit, daily aggregation
│   ├── forecasting/            # Baseline models, feature engineering, trainer, evaluation
│   ├── inventory/              # Safety stock, ROP, order-up-to, Mode A & B recommenders
│   ├── database/               # SQLAlchemy models, connection, repository DAO, migrations
│   ├── analytics/              # Overview KPIs, Pareto analysis, day-of-week patterns
│   └── exports/                # Multi-tab styled Excel report builder & CSV streams
│
├── data/
│   ├── sample/                 # Synthetic transactions, daily sales, inventory, messy datasets
│   └── templates/              # Blank CSV templates for user uploads
│
├── tests/                      # Automated test suite (Pytest)
│   ├── conftest.py             # Isolated SQLite fixtures
│   ├── test_api.py             # FastAPI REST endpoints & TestClient tests
│   ├── test_upload.py          # Upload & column mapping tests
│   ├── test_cleaning.py        # Cleaning, returns, and anomaly tests
│   ├── test_aggregation.py     # Aggregation and gap-filling tests
│   ├── test_forecasting.py     # Lags, chronological split, metrics, model tests
│   ├── test_inventory.py       # Safety stock, ROP, MOQ, Mode A & B math proofs
│   ├── test_database.py        # SQLAlchemy CRUD, migrations, and snapshot persistence
│   └── test_integration.py     # Full end-to-end integration test
│
└── docs/                       # Technical documentation
    ├── architecture.md         # Detailed architecture & design
    ├── data_dictionary.md      # Schema specifications & synonyms catalog
    ├── test_plan.md            # Complete test execution matrix
    └── user_guide.md           # Non-technical shopkeeper manual
```

---

## 7. Local Setup & Execution Guide

### Prerequisites
- Python 3.11, 3.12, or 3.13 installed.
- Windows PowerShell, macOS Terminal, or Linux Shell.

### Step 1: Clone Repository & Navigate
```bash
git clone https://github.com/mayursable-17/retail-forecasting-system.git
cd retail-forecasting-system
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
Verify that all 42 automated tests pass with 100% success:
```bash
python -m pytest -v
```

### Step 5: Launch Local FastAPI Server
```bash
python -m uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
```
*Open your browser and navigate to:* **`http://localhost:8000`**
*Interactive API Swagger Documentation:* **`http://localhost:8000/docs`**

---

## 8. Sample Datasets Included

The repository contains reproducible synthetic datasets in `data/sample/`:

1. `sample_transactions.csv`: 90 days of itemized customer purchase receipts.
2. `sample_daily_sales.csv`: Aggregated daily sales across 12 staple retail items.
3. `sample_inventory.csv`: Physical stock counts, on-order quantities, lead times, and MOQs.
4. `sample_retail_store.xlsx`: Multi-sheet workbook with `Sales Transactions` and `Current Inventory`.
5. `messy_sales_data.csv`: A deliberately malformed dataset containing missing dates, unparseable timestamps, blank product IDs, customer returns (-2 qty), negative prices, duplicate transactions, and non-standard column headers (e.g. `Item SKU`, `Qty Sold`).
6. `data/templates/sales_template.csv` & `inventory_template.csv`: Clean CSV formatting templates.

---

## 9. Verification & Test Suite Summary

All 42 automated tests execute in under 4.5 seconds with zero failures:

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.7.0
rootdir: retail-forecasting-system
plugins: anyio-4.15.1
collected 42 items

tests/test_aggregation.py::test_aggregate_daily_sales_basic PASSED       [  2%]
tests/test_aggregation.py::test_net_demand_non_negativity_with_excess_returns PASSED [  4%]
tests/test_aggregation.py::test_gap_filling_creates_zero_sales PASSED    [  7%]
tests/test_api.py::test_root_serves_html PASSED                          [  9%]
tests/test_api.py::test_api_health PASSED                                [ 11%]
tests/test_api.py::test_api_shop PASSED                                  [ 14%]
tests/test_api.py::test_api_dashboard PASSED                             [ 16%]
tests/test_api.py::test_api_products PASSED                              [ 19%]
tests/test_api.py::test_api_inventory_recommendations_endpoint PASSED    [ 21%]
tests/test_api.py::test_api_csv_export PASSED                            [ 23%]
tests/test_api.py::test_api_shop_defaults_update PASSED                  [ 26%]
tests/test_cleaning.py::test_clean_missing_and_unparseable_dates PASSED  [ 28%]
tests/test_cleaning.py::test_clean_negative_quantities_as_returns PASSED [ 30%]
tests/test_cleaning.py::test_clean_duplicate_transactions PASSED         [ 33%]
tests/test_cleaning.py::test_impute_missing_quantity_and_revenue PASSED  [ 35%]
tests/test_database.py::test_shop_and_products_operations PASSED         [ 38%]
tests/test_database.py::test_sales_daily_operations PASSED               [ 40%]
tests/test_database.py::test_inventory_snapshot_latest_query PASSED      [ 42%]
tests/test_database.py::test_forecast_and_recommendations_persistence PASSED [ 45%]
tests/test_database.py::test_operational_defaults_persistence PASSED     [ 47%]
tests/test_database.py::test_batch_update_products PASSED                [ 50%]
tests/test_database.py::test_latest_upload_and_alerts_summary PASSED     [ 52%]
tests/test_forecasting.py::test_evaluation_metrics_known_values PASSED   [ 54%]
tests/test_forecasting.py::test_wape_zero_actual_handling PASSED         [ 57%]
tests/test_forecasting.py::test_chronological_split_no_leakage PASSED    [ 59%]
tests/test_forecasting.py::test_feature_engineering_strictly_causal PASSED [ 61%]
tests/test_forecasting.py::test_baseline_forecasters PASSED              [ 64%]
tests/test_forecasting.py::test_demand_model_trainer_and_predict PASSED  [ 66%]
tests/test_integration.py::test_full_pipeline_integration PASSED         [ 69%]
tests/test_inventory.py::test_inventory_position_formula PASSED          [ 71%]
tests/test_inventory.py::test_safety_stock_variability_analytical_proof PASSED [ 73%]
tests/test_inventory.py::test_reorder_point_and_order_up_to_target PASSED [ 76%]
tests/test_inventory.py::test_moq_and_case_pack_rounding PASSED          [ 78%]
tests/test_inventory.py::test_mode_a_recommendations_sales_only PASSED   [ 80%]
tests/test_inventory.py::test_mode_b_recommendations_full PASSED         [ 83%]
tests/test_upload.py::test_read_valid_csv PASSED                         [ 85%]
tests/test_upload.py::test_read_empty_csv PASSED                         [ 88%]
tests/test_upload.py::test_unsupported_file_extension PASSED             [ 90%]
tests/test_upload.py::test_read_valid_xlsx PASSED                        [ 92%]
tests/test_upload.py::test_column_auto_detection PASSED                  [ 95%]
tests/test_upload.py::test_validate_mapping_valid PASSED                 [ 97%]
tests/test_upload.py::test_validate_mapping_missing_required PASSED      [100%]

======================== 42 passed, 1 warning in 4.15s ========================
```

---

## 10. Deployment Guidelines

### 10.1 Vercel Serverless (Recommended)
1. Push your repository to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and select `retail-forecasting-system`.
3. Vercel automatically deploys using `vercel.json` and `@vercel/python`.
4. *(Optional for persistence)*: In Vercel Project Settings > Environment Variables, set `DATABASE_URL=postgresql://...` to connect a permanent managed PostgreSQL database.

### 10.2 Docker Containerization
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 11. Limitations & Future Work

### Limitations
- Lead time is modeled as a deterministic integer parameter. In real-world logistics, lead times can exhibit stochastic variability.
- The single-user prototype utilizes SQLite; high-concurrency multi-store setups should connect to managed PostgreSQL.
- Extreme black-swan events (such as sudden supply shocks or pandemics) exceed historical lag pattern assumptions.

### Future Enhancements
- Joint distribution models for simultaneous demand and supplier lead-time uncertainty.
- Optical Character Recognition (OCR) pipeline for physical paper bills and handwritten kirana chits.
- Multi-location warehouse replenishment routing and supplier batch pooling.

---

## 12. Academic Metadata

- **Degree:** Bachelor of Technology (B.Tech)
- **Specialization:** Computer Science & Engineering (Data Science)
- **Subject:** Final Year Capstone Project
- **Date of Completion:** October 2026
