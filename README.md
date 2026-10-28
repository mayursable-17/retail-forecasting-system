# Retail Sales Forecasting & Inventory Optimization System Using Machine Learning

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=mayursable-17/retail-forecasting-system&branch=main&mainModule=app.py)
[![Live Demo](https://img.shields.io/badge/Live%20App-Streamlit%20Community%20Cloud-FF4B4B?logo=streamlit&logoColor=white)](https://share.streamlit.io/deploy?repository=mayursable-17/retail-forecasting-system&branch=main&mainModule=app.py)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-003B57.svg)](https://www.sqlalchemy.org/)
[![Machine Learning](https://img.shields.io/badge/ML-XGBoost%20%7C%20Scikit--Learn-F7931E.svg)](https://xgboost.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-34%20Passed%20%28100%25%29-brightgreen.svg)](tests/)

---

## 🌐 Live Application & 1-Click Launch

Access and run the live application directly on the web:

* **1-Click Streamlit Cloud Deployment:** Click the badge below to immediately launch or connect this repository to Streamlit Community Cloud for free:

  [![Deploy with Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=mayursable-17/retail-forecasting-system&branch=main&mainModule=app.py)

* **Direct App URL:** [https://share.streamlit.io/mayursable-17/retail-forecasting-system/main/app.py](https://share.streamlit.io/mayursable-17/retail-forecasting-system/main/app.py)
* **Custom Domain (When Hosted):** https://retail-forecasting-system.streamlit.app

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
6. **Production-Ready Multi-Page UI:** Provide an intuitive Streamlit interface, interactive Plotly charts, and formatted multi-sheet Excel exports.

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.11, 3.12, 3.13 | Core runtime environment |
| **Frontend Framework** | Streamlit | $\ge 1.40.0$ | Multipage interactive web application |
| **Data Visualization** | Plotly Express & Graph Objects | $\ge 5.18.0$ | Interactive analytical and forecast visualizations |
| **Data Processing** | Pandas, NumPy | $\ge 2.0.0$ | DataFrames, matrix math, aggregation, date indexing |
| **Spreadsheet Engine** | openpyxl | $\ge 3.1.0$ | Safe formula-isolated Excel read/write |
| **Machine Learning** | XGBoost, Scikit-learn, Statsmodels | $\ge 2.0.0$ | Boosted trees, Random Forests, statistical baselines |
| **ORM & Database** | SQLAlchemy, SQLite | $\ge 2.0.0$ | Relational data persistence, PostgreSQL-ready |
| **Test Automation** | Pytest | $\ge 8.0.0$ | Automated unit, mathematical, and integration tests |

---

## 4. System Architecture

```mermaid
flowchart TD
    subgraph UI ["Presentation Layer (Streamlit Multipage)"]
        Dashboard["Home Dashboard (app.py)"]
        UploadPage["Upload & Column Mapping"]
        QualityPage["Data Quality & Audit"]
        AnalyticsPage["Sales Analytics"]
        ForecastPage["Demand Forecasting"]
        InventoryPage["Inventory Optimization"]
        ProductPage["Product Management"]
        ReportsPage["Reports & Downloads"]
        SettingsPage["Settings & Configuration"]
    end

    subgraph Ingestion ["Ingestion & Preprocessing Engine"]
        Reader["file_reader.py<br/>(openpyxl data_only / CSV)"]
        Mapper["column_mapper.py<br/>(Synonym Auto-Detection)"]
        Cleaner["cleaning.py<br/>(Anomalies, Returns, Imputation)"]
        Aggregator["aggregation.py<br/>(Daily Normalization & Zero Filling)"]
    end

    subgraph Forecasting ["Forecasting & Machine Learning Engine"]
        Trainer["train.py<br/>(Chronological Split & Benchmarking)"]
        Features["features.py<br/>(Strict Non-Leaking Lags & Rolling Stats)"]
        Models["baseline.py & ML<br/>(Naive, SES, MA, XGBoost, RF)"]
        Evaluator["evaluate.py<br/>(MAE, RMSE, WAPE, Bias)"]
        Predictor["predict.py<br/>(Multi-Step Recursive Horizon Projections)"]
    end

    subgraph Optimization ["Inventory Optimization Engine"]
        SafetyStock["safety_stock.py<br/>(Variability: z * σ_d * √L / Fixed Buffer)"]
        ROP["reorder_point.py<br/>(ROP = D_L + SS, S = D_L+R + SS, MOQ, Packs)"]
        Recommender["recommendations.py<br/>(Workflow A & Workflow B Logic)"]
    end

    subgraph DataAccess ["Persistence Layer"]
        Repo["repository.py (DAO)"]
        ORM["models.py (SQLAlchemy Schema)"]
        DB[(SQLite / PostgreSQL Engine)]
    end

    UploadPage --> Reader --> Mapper --> Cleaner --> Aggregator --> Repo
    Repo --> ORM --> DB
    Dashboard --> Repo
    AnalyticsPage --> Repo
    ForecastPage --> Trainer --> Features --> Models --> Evaluator
    Trainer --> Predictor --> Repo
    InventoryPage --> Recommender --> SafetyStock
    Recommender --> ROP --> Repo
    ReportsPage --> Repo
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
  *Advantage over MAPE:* Well-defined even when individual actual demand days are zero.
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
├── app.py                      # Main entrypoint & Home Dashboard
├── requirements.txt            # Python dependencies
├── README.md                   # Academic project documentation
├── .gitignore                  # Git ignore rules
│
├── pages/                      # Streamlit Multipage application
│   ├── 1_Upload_Data.py        # File ingestion & column mapping
│   ├── 2_Data_Quality.py       # Data cleaning & anomaly audit
│   ├── 3_Sales_Analytics.py    # Sales trends & visual exploration
│   ├── 4_Demand_Forecasting.py # ML forecasting & validation holdout
│   ├── 5_Inventory_Optimization.py # Reorder points & safety stock
│   ├── 6_Product_Management.py # Catalog & stock snapshot logging
│   ├── 7_Reports.py            # Master Excel & CSV export
│   └── 8_Settings.py           # Store profile & operational defaults
│
├── src/                        # Modular service packages
│   ├── config.py               # Constants, thresholds, and paths
│   ├── ui_helpers.py           # CSS injection & UI widgets
│   ├── generate_samples.py     # Synthetic data generation script
│   ├── ingestion/              # File reader, column mapper, schema validation
│   ├── preprocessing/          # Cleaning, anomaly audit, daily aggregation
│   ├── forecasting/            # Baseline models, feature engineering, trainer, evaluation
│   ├── inventory/              # Safety stock, ROP, order-up-to, Mode A & B recommenders
│   ├── database/               # SQLAlchemy models, connection, repository DAO
│   ├── analytics/              # Overview KPIs, Pareto analysis, day-of-week patterns
│   └── exports/                # Multi-tab styled Excel report builder
│
├── data/
│   ├── sample/                 # Synthetic transactions, daily sales, inventory, messy datasets
│   └── templates/              # Blank CSV templates for user uploads
│
├── tests/                      # Automated test suite (Pytest)
│   ├── conftest.py             # Isolated SQLite fixtures
│   ├── test_upload.py          # Upload & column mapping tests
│   ├── test_cleaning.py        # Cleaning, returns, and anomaly tests
│   ├── test_aggregation.py     # Aggregation and gap-filling tests
│   ├── test_forecasting.py     # Lags, chronological split, metrics, model tests
│   ├── test_inventory.py       # Safety stock, ROP, MOQ, Mode A & B math proofs
│   ├── test_database.py        # SQLAlchemy CRUD and snapshot persistence tests
│   └── test_integration.py     # Full end-to-end integration test
│
└── docs/                       # Technical documentation
    ├── architecture.md         # Detailed architecture & design
    ├── data_dictionary.md      # Schema specifications & synonyms catalog
    ├── test_plan.md            # Complete test execution matrix
    └── user_guide.md           # Non-technical shopkeeper manual
```

---

## 7. Local Setup & Execution Guide (Windows)

### Prerequisites
- Python 3.11, 3.12, or 3.13 installed.
- Windows PowerShell or Command Prompt.

### Step 1: Navigate to Project Directory
```powershell
cd "C:\Users\MAYUR\.gemini\antigravity\scratch\retail-forecasting-system"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
Verify that all 31 automated tests pass:
```powershell
pytest -v
```

### Step 5: Launch the Streamlit Web Application
```powershell
streamlit run app.py
```
*The application will open automatically in your browser at `http://localhost:8501`.*

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

All 31 automated tests execute in under 3.5 seconds with zero errors:

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

---

## 10. Deployment Guidelines

### 10.1 Streamlit Community Cloud
1. Push this repository to GitHub.
2. Connect your repository on [share.streamlit.io](https://share.streamlit.io).
3. Set Main file path: `app.py`.
4. Add environment variables if utilizing external PostgreSQL: `DATABASE_URL=postgresql://user:pass@host:5432/db`.
5. *Persistence Note:* Default SQLite files on ephemeral hosting reset on server reboot. For permanent cloud storage, attach an external hosted PostgreSQL instance (e.g., Supabase, Neon, or AWS RDS).

### 10.2 Docker Containerization
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 11. Limitations & Future Work

### Limitations
- Lead time is modeled as a deterministic integer parameter. In real-world logistics, lead times can exhibit stochastic variability.
- The single-user prototype utilizes SQLite; high-concurrency multi-store setups should migrate to PostgreSQL.
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
