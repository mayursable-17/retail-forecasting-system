# System Architecture & Technical Design

## Retail Sales Forecasting & Inventory Optimization System

### 1. Architectural Overview

The system is designed following a **layered, decoupled service-oriented architecture (SOA)**. It cleanly isolates user interface presentation (Streamlit), data ingestion, validation, machine learning forecasting, inventory optimization algorithms, and relational data persistence (SQLAlchemy / SQLite).

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

    subgraph DataAccess ["Persistence & Database Layer"]
        Repo["repository.py<br/>(Data Access Object)"]
        ORM["models.py<br/>(SQLAlchemy Schema)"]
        DB[(SQLite / PostgreSQL Engine)]
    end

    subgraph Exports ["Reporting & Export Layer"]
        ExcelGen["excel_report.py<br/>(Styled OpenPyXL Multi-Tab Workbook)"]
    end

    UploadPage --> Reader --> Mapper --> Cleaner --> Aggregator --> Repo
    Repo --> ORM --> DB
    Dashboard --> Repo
    AnalyticsPage --> Repo
    ForecastPage --> Trainer --> Features --> Models --> Evaluator
    Trainer --> Predictor --> Repo
    InventoryPage --> Recommender --> SafetyStock
    Recommender --> ROP --> Repo
    ReportsPage --> ExcelGen --> Repo
```

---

### 2. Dual Inventory Workflow Architecture

The application implements two distinct inventory replenishment workflows to handle shops with different levels of technical record-keeping:

```mermaid
flowchart LR
    Start([Shopkeeper Uploads Data]) --> Check{Inventory Stock Levels Provided?}
    
    Check -- No --> WorkflowA["Workflow A: Sales Data Only"]
    WorkflowA --> ForecastA["Forecast Future Product Demand"]
    ForecastA --> BufferA["Apply Configurable Replenishment Buffer (15%)"]
    BufferA --> EstReq["Estimated Gross Requirements<br/>(Transparently reports stock unknown)"]
    
    Check -- Yes --> WorkflowB["Workflow B: Sales + Current Stock"]
    WorkflowB --> ForecastB["Forecast Future Horizon Demand"]
    WorkflowB --> InvPos["Calculate Inventory Position<br/>IP = OnHand + OnOrder - Backorders"]
    InvPos --> SS["Compute Safety Stock<br/>SS = z * σ_d * √L"]
    SS --> ROP_Calc["Compute Reorder Point<br/>ROP = D_L + SS"]
    ROP_Calc --> TargetS["Compute Order-up-to Target<br/>S = D_L+R + SS"]
    TargetS --> Constrain["Apply Supplier MOQ & Case Pack Rounding"]
    Constrain --> FinalOrder["Confirmed Reorder Recommendations & Alert Statuses"]
```

---

### 3. Database Entity Relationship (ER) Model

```mermaid
erDiagram
    shops ||--o{ products : "catalogs"
    shops ||--o{ uploads : "stores"
    shops ||--o{ sales_daily : "records"
    shops ||--o{ inventory_snapshots : "tracks"
    shops ||--o{ forecast_runs : "executes"
    
    products ||--o{ sales_daily : "measures"
    products ||--o{ inventory_snapshots : "snapshots"
    products ||--o{ forecast_results : "projects"
    products ||--o{ reorder_recommendations : "evaluates"

    uploads ||--o{ sales_daily : "originates"
    uploads ||--o{ forecast_runs : "triggers"

    forecast_runs ||--o{ forecast_results : "outputs"
    forecast_runs ||--o{ reorder_recommendations : "drives"

    shops {
        int shop_id PK
        string shop_name
        string shop_type
        string currency_symbol
        string currency_code
        datetime created_at
    }

    products {
        string product_id PK
        int shop_id FK
        string sku
        string product_name
        string category
        float unit_price
        int lead_time_days
        float minimum_order_quantity
        float case_pack_size
        boolean is_active
        datetime created_at
    }

    uploads {
        int upload_id PK
        int shop_id FK
        string file_name
        string file_hash
        string upload_type
        datetime uploaded_at
        string status
        int row_count
        json quality_summary
    }

    sales_daily {
        int sale_id PK
        int shop_id FK
        string product_id FK
        date sale_date
        float quantity_sold
        float revenue
        int upload_id FK
    }

    inventory_snapshots {
        int snapshot_id PK
        int shop_id FK
        string product_id FK
        datetime snapshot_date
        float on_hand_qty
        float on_order_qty
        float backorders
        int lead_time_days
    }

    forecast_runs {
        int run_id PK
        int shop_id FK
        int upload_id FK
        string model_name
        string model_version
        int horizon_days
        datetime created_at
        json validation_metrics
        json configuration
    }

    forecast_results {
        int result_id PK
        int run_id FK
        string product_id FK
        date forecast_date
        float predicted_demand
        float lower_bound
        float upper_bound
    }

    reorder_recommendations {
        int recommendation_id PK
        int run_id FK
        string product_id FK
        float current_stock
        float inventory_position
        float reorder_point
        float safety_stock
        float expected_lead_time_demand
        float order_up_to_target
        float suggested_qty
        string risk_status
        string inventory_mode
        text explanation
        datetime created_at
    }
```

---

### 4. Machine Learning & Forecasting Pipeline Details

1. **Chronological Splitting (No Data Leakage):**
   - The time series is never randomly shuffled.
   - For an observation series of $N$ days, the most recent $V = \min(14, \max(3, \text{int}(0.2 \times N)))$ days are reserved exclusively for out-of-sample holdout validation.
   - Training features are derived strictly from observations prior to the validation window.

2. **Causal Feature Engineering:**
   - **Lags:** $y_{t-1}, y_{t-7}, y_{t-14}, y_{t-28}$.
   - **Rolling Statistics:** Shifted by 1 so that period $t$'s actual sales cannot leak into features:
     $\text{rolling\_mean\_7}(t) = \frac{1}{7} \sum_{i=1}^7 y_{t-i}$.
   - **Calendar Determinants:** Day of week ($0\dots 6$), Weekend indicator ($0/1$), Day of month ($1\dots 31$), Month of year ($1\dots 12$), ISO week of year ($1\dots 53$).

3. **Multi-Step Recursive Prediction:**
   - To project $H$ periods into the future ($7, 15, 30$ days), predictions are generated step-by-step.
   - Step $t+1$ is predicted, appended to the sequence, and lags/rolling features are recalculated dynamically for step $t+2$ through $t+H$.
   - Negative model predictions are floored at $0.0$ units.
   - Prediction intervals are computed using the validation holdout residual standard deviation:
     $$\hat{y} \pm 1.645 \times \sigma_{\text{residual}}$$

---

### 5. Inventory Optimization & Periodic Review Formulation

The inventory engine evaluates a **$(R, s, S)$ Periodic Review Policy**:

1. **Inventory Position ($IP$):**
   $$IP = \text{On-Hand Stock} + \text{On-Order Units} - \text{Backorders}$$

2. **Expected Lead Time Demand ($D_L$):**
   $$D_L = \sum_{t=1}^{L} \hat{y}_t$$

3. **Safety Stock ($SS$):**
   - **Variability Method:**
     $$SS = \lceil z \times \sigma_d \times \sqrt{L} \rceil$$
     Where $z$ is the standard normal deviate for the target cycle service level (e.g., $z = 1.645$ for 95%), $\sigma_d$ is the standard deviation of daily demand, and $L$ is supplier lead time in days.
   - **Buffer Fallback Method (used when historical demand is sparse):**
     $$SS = \lceil \text{Buffer\%} \times \bar{d} \times L \rceil$$

4. **Reorder Point ($ROP$):**
   $$ROP = D_L + SS$$

5. **Order-up-to Target ($S$):**
   $$S = D_{L + R} + SS$$
   Where $R$ is the store review cycle period (e.g., 7 days).

6. **Preliminary Order Quantity ($O_{\text{prelim}}$):**
   $$O_{\text{prelim}} = \begin{cases} \max(0, S - IP) & \text{if } IP \le ROP \\ 0 & \text{if } IP > ROP \end{cases}$$

7. **Packaging & Supplier Constraints:**
   - If $0 < O_{\text{prelim}} < \text{MOQ}$, order is rounded up to $\text{MOQ}$.
   - If $\text{Case Pack Size} > 1$, order is rounded up to the nearest multiple:
     $$O_{\text{final}} = \lceil \frac{O_{\text{prelim}}}{\text{Pack Size}} \rceil \times \text{Pack Size}$$

---

### 6. Security & Safe Data Handling

- **Formula Injection Prevention:** Excel uploads are parsed with openpyxl in `data_only=True` mode, ensuring only cached calculated cell values are ingested. Dynamic macro execution, DDE links, and script bombs are disarmed.
- **File Upload Limits:** Strict 25 MB payload threshold prevents memory exhaustion and zip-bomb attacks.
- **SQL Parameterization:** All database read/write queries are mediated through SQLAlchemy ORM parameter binding, preventing SQL injection vulnerabilities.
- **Data Isolation:** Every record in `sales_daily`, `products`, `uploads`, and `inventory_snapshots` is partitioned by `shop_id`.
