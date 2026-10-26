# Data Dictionary & Schema Specification

## Retail Sales Forecasting & Inventory Optimization System

---

### 1. Database Schema Specifications

#### Table 1: `shops`
Stores shop identity, retail classification, and currency configuration.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `shop_id` | INTEGER | PK | No | Auto | Unique internal store identifier |
| `shop_name` | VARCHAR(150) | - | No | 'Kirana & Retail Hub' | Business legal or trade name |
| `shop_type` | VARCHAR(80) | - | No | 'General Store' | Classification (Kirana, Supermarket, Apparel, Stationery) |
| `currency_symbol` | VARCHAR(10) | - | No | '₹' | Display symbol (₹, $, €, £) |
| `currency_code` | VARCHAR(10) | - | No | 'INR' | 3-letter ISO currency code |
| `created_at` | DATETIME | - | No | UTC Now | Timestamp of registration |

---

#### Table 2: `products`
Master catalog of distinct items, pricing, and supplier fulfillment parameters.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | VARCHAR(100) | PK | No | - | Unique product code / SKU / barcode |
| `shop_id` | INTEGER | FK (`shops.shop_id`) | No | 1 | Associated shop identifier |
| `sku` | VARCHAR(100) | - | Yes | NULL | Stock Keeping Unit code |
| `product_name` | VARCHAR(255) | - | No | - | Human-readable product description |
| `category` | VARCHAR(100) | - | No | 'General' | Department / aisle classification |
| `unit_price` | FLOAT | - | No | 0.0 | Selling price per unit |
| `lead_time_days` | INTEGER | - | No | 7 | Replenishment delivery days from supplier |
| `minimum_order_quantity`| FLOAT | - | No | 1.0 | Minimum order threshold enforced by supplier |
| `case_pack_size` | FLOAT | - | No | 1.0 | Batch pack size (must order in multiples of this) |
| `is_active` | BOOLEAN | - | No | True | Active listing flag |
| `created_at` | DATETIME | - | No | UTC Now | Record creation timestamp |

---

#### Table 3: `uploads`
Audit log of all uploaded CSV and Excel files.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `upload_id` | INTEGER | PK | No | Auto | Unique upload identifier |
| `shop_id` | INTEGER | FK (`shops.shop_id`) | No | 1 | Associated shop identifier |
| `file_name` | VARCHAR(255) | - | No | - | Original uploaded filename |
| `file_hash` | VARCHAR(64) | - | Yes | NULL | SHA-256 content checksum |
| `upload_type` | VARCHAR(50) | - | No | 'sales' | Type: 'sales', 'inventory', 'combined' |
| `uploaded_at` | DATETIME | - | No | UTC Now | Ingestion timestamp |
| `status` | VARCHAR(50) | - | No | 'completed' | Status: 'completed', 'partial', 'failed' |
| `row_count` | INTEGER | - | No | 0 | Raw row count of uploaded file |
| `quality_summary` | JSON | - | Yes | NULL | Audit summary JSON (accepted, flagged, excluded) |

---

#### Table 4: `sales_daily`
Normalized daily sales aggregated by product and date.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sale_id` | INTEGER | PK | No | Auto | Unique daily sales record identifier |
| `shop_id` | INTEGER | FK (`shops.shop_id`) | No | 1 | Associated shop identifier |
| `product_id` | VARCHAR(100) | FK (`products.product_id`) | No | - | Foreign key to product catalog |
| `sale_date` | DATE | - | No | - | Sales calendar date |
| `quantity_sold`| FLOAT | - | No | 0.0 | Net daily units sold (floored at 0.0) |
| `revenue` | FLOAT | - | No | 0.0 | Daily total sales revenue |
| `upload_id` | INTEGER | FK (`uploads.upload_id`) | Yes | NULL | Upload record origin |

**Constraints:** Unique constraint on `(shop_id, product_id, sale_date)`.

---

#### Table 5: `inventory_snapshots`
Time-series log of physical stock counts, incoming shipments, and backorders.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `snapshot_id` | INTEGER | PK | No | Auto | Unique snapshot identifier |
| `shop_id` | INTEGER | FK (`shops.shop_id`) | No | 1 | Associated shop identifier |
| `product_id` | VARCHAR(100) | FK (`products.product_id`) | No | - | Target catalog item |
| `snapshot_date`| DATETIME | - | No | UTC Now | Date and time stock count was taken |
| `on_hand_qty` | FLOAT | - | No | 0.0 | Physical stock verified on store shelves |
| `on_order_qty`| FLOAT | - | No | 0.0 | Confirmed purchase order units in transit |
| `backorders` | FLOAT | - | No | 0.0 | Unfilled customer backorders |
| `lead_time_days`| INTEGER | - | No | 7 | Active supplier lead time in days |

---

#### Table 6: `forecast_runs`
Metadata and holdout evaluation scores for each forecasting run.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `run_id` | INTEGER | PK | No | Auto | Unique forecast run identifier |
| `shop_id` | INTEGER | FK (`shops.shop_id`) | No | 1 | Target shop |
| `upload_id` | INTEGER | FK (`uploads.upload_id`) | Yes | NULL | Linked upload session |
| `model_name` | VARCHAR(100) | - | No | - | Selected algorithm (XGBoost, MA, SES) |
| `model_version`| VARCHAR(50) | - | No | '1.0.0' | Pipeline release version |
| `horizon_days` | INTEGER | - | No | 15 | Horizon length in days (7, 15, 30) |
| `created_at` | DATETIME | - | No | UTC Now | Execution timestamp |
| `validation_metrics` | JSON | - | Yes | NULL | Out-of-sample scores (MAE, RMSE, WAPE, Bias) |
| `configuration` | JSON | - | Yes | NULL | Run parameters and preferences |

---

#### Table 7: `forecast_results`
Individual day-level demand predictions and confidence bands.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `result_id` | INTEGER | PK | No | Auto | Unique result row identifier |
| `run_id` | INTEGER | FK (`forecast_runs.run_id`) | No | - | Linked run identifier |
| `product_id` | VARCHAR(100) | FK (`products.product_id`) | No | - | Forecasted item SKU |
| `forecast_date`| DATE | - | No | - | Projected future calendar date |
| `predicted_demand`| FLOAT | - | No | 0.0 | Expected unit demand ($\ge 0.0$) |
| `lower_bound` | FLOAT | - | Yes | 0.0 | Lower 90% confidence bound |
| `upper_bound` | FLOAT | - | Yes | 0.0 | Upper 90% confidence bound |

---

#### Table 8: `reorder_recommendations`
Supply chain optimization outputs, ROP values, and order instructions.

| Field Name | Type | PK / FK | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `recommendation_id` | INTEGER | PK | No | Auto | Unique recommendation identifier |
| `run_id` | INTEGER | FK (`forecast_runs.run_id`) | No | - | Linked forecast run |
| `product_id` | VARCHAR(100) | FK (`products.product_id`) | No | - | Catalog product |
| `current_stock` | FLOAT | - | Yes | NULL | On-hand units at evaluation |
| `inventory_position`| FLOAT | - | Yes | NULL | $IP = \text{On-Hand} + \text{On-Order} - \text{Backorders}$ |
| `reorder_point` | FLOAT | - | Yes | NULL | $ROP = D_L + SS$ |
| `safety_stock` | FLOAT | - | Yes | NULL | Safety buffer units |
| `expected_lead_time_demand`| FLOAT | - | Yes | NULL | Projected demand during lead time ($D_L$) |
| `order_up_to_target`| FLOAT | - | Yes | NULL | Target inventory level ($S$) |
| `suggested_qty` | FLOAT | - | No | 0.0 | Recommended order units (post-MOQ/pack rounding) |
| `risk_status` | VARCHAR(50) | - | No | - | Alert category |
| `inventory_mode` | VARCHAR(20) | - | No | - | 'inventory_mode' or 'estimated_mode' |
| `explanation` | TEXT | - | No | - | Human-readable mathematical justification |
| `created_at` | DATETIME | - | No | UTC Now | Recommendation generation timestamp |

---

### 2. Standard Column Mapping Synonyms Catalog

The ingestion engine normalizes arbitrary user spreadsheet headers using this target mapping dictionary:

| Standard Target | Recognized Common Column Headers & Synonyms |
| :--- | :--- |
| `date` | `date`, `sale_date`, `order_date`, `transaction_date`, `invoice_date`, `bill_date`, `timestamp` |
| `product_id` | `product_id`, `item_id`, `sku`, `item_code`, `product_code`, `barcode`, `code` |
| `product_name` | `product_name`, `product`, `item`, `item_name`, `description`, `title`, `product_title` |
| `category` | `category`, `product_category`, `item_category`, `dept`, `department`, `group` |
| `quantity` | `quantity`, `qty`, `units_sold`, `sales_quantity`, `volume`, `sold_qty`, `count` |
| `unit_price` | `unit_price`, `price`, `selling_price`, `rate`, `mrp`, `item_price`, `unit_cost` |
| `revenue` | `revenue`, `sales_amount`, `total_sales`, `amount`, `total_amount`, `sales`, `net_amount` |
| `stock` | `stock`, `current_stock`, `inventory_level`, `stock_available`, `on_hand`, `quantity_on_hand` |
| `on_order` | `on_order`, `pending_stock`, `units_on_order`, `incoming_stock`, `qty_on_order` |
| `lead_time` | `lead_time`, `supplier_lead_time`, `delivery_days`, `lead_time_days` |
| `min_order_qty`| `moq`, `minimum_order_quantity`, `min_order_qty`, `min_order` |
| `case_pack` | `case_pack`, `case_pack_size`, `pack_size`, `batch_size` |

---

### 3. Inventory Alert Status Definitions

| Status Label | Operational Condition | Action Required by Shopkeeper |
| :--- | :--- | :--- |
| **Stock Risk** | Physical on-hand stock is 0, or inventory position is below safety buffer while expected lead-time demand exceeds position. | Immediate emergency reorder required to avert stockout. |
| **Reorder Review**| Inventory Position $\le$ Reorder Point ($IP \le ROP$). | Place routine replenishment order equal to suggested quantity. |
| **Adequate Stock** | Inventory Position is comfortably above Reorder Point and below excess threshold. | No order required at this review cycle. |
| **Potential Excess Stock** | Inventory Position $> 2.5 \times (D_L + SS)$ and inventory position $> 10$ units. | Surplus inventory. Avoid ordering; consider promotional discounting. |
| **Insufficient Inventory Information** | Current physical stock and pending orders are unknown (Mode A). | Conduct a physical inventory count or upload stock snapshot to enable Mode B. |
