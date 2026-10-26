# User Guide & Operational Manual

## Retail Sales Forecasting & Inventory Optimization System
*Designed for Kirana Stores, Supermarkets, Apparel Shops, and Small Retail Businesses*

---

### 1. Introduction

Welcome to the **Retail Sales Forecasting & Inventory Optimization System**! This application is designed to help small business owners and shopkeepers eliminate two common, costly retail problems:
1. **Stockouts:** Running out of popular goods and losing loyal customers.
2. **Overstocking:** Tying up hard-earned capital in slow-moving inventory that occupies valuable shelf space.

The system does not require you to be a computer scientist or data expert. You can use your own existing sales receipts, Excel notebooks, or CSV files without having to reformat your spreadsheets.

---

### 2. Navigating the Application

The application consists of 9 integrated pages accessible from the left sidebar:

1. **Home Dashboard:** High-level summary of store revenues, units sold, top-selling items, and quick action buttons.
2. **Upload Data:** Upload your sales transactions or stock sheets in CSV or Excel format.
3. **Data Quality:** Review the health of your uploaded files, see detected customer returns, and inspect cleaning audit logs.
4. **Sales Analytics:** Explore interactive sales charts, day-of-week trends, category revenue shares, and slow-moving items.
5. **Demand Forecasting:** Run AI machine learning models to predict how many units of each product will sell over the next 7, 15, or 30 days.
6. **Inventory Optimization:** Receive clear recommendations on which items to reorder, exact quantities to buy, and safety stock levels.
7. **Product Management:** Add or edit products, record physical stock counts, and view inventory history.
8. **Reports & Downloads:** Download a multi-tab Excel workbook or individual CSV tables to share with suppliers and accountants.
9. **Settings:** Customize your shop name, store type, currency (defaults to ₹ INR), and default supplier lead times.

---

### 3. Step-by-Step Walkthrough

#### Step 1: Loading Initial Data
- If you are opening the app for the first time, you will see a **Welcome Onboarding Screen**.
- You can immediately click **"Load Built-in Kirana Store Dataset"** to populate the system with 12 popular retail items across 90 days.
- Alternatively, go to the **Upload Data** page to upload your own spreadsheet.

#### Step 2: Uploading Your Own Spreadsheet
1. Go to **Upload Data**.
2. Drag and drop your `.csv` or `.xlsx` file.
3. If using an Excel workbook with multiple tabs, select the sheet containing sales records.
4. Review the **Column Mapping** table:
   - The system automatically detects common column titles (e.g., matching "Date", "Transaction Date", "Bill Date" to the Date column).
   - Confirm or correct any column using the dropdown menus.
5. Click **"Process, Clean & Save Dataset"**.

#### Step 3: Understanding Customer Returns & Data Health
- On the **Data Quality** page, you can see how many records were accepted, flagged, or excluded.
- **Customer Returns:** If a customer returned an item (indicated by a negative quantity, e.g., -2), the system deducts this from daily demand rather than deleting it. This ensures your future reorder recommendations are based on *true net sales*.

#### Step 4: Generating Demand Forecasts
1. Go to **Demand Forecasting**.
2. Select your planning horizon: **7 Days**, **15 Days**, or **30 Days**.
3. Choose an algorithm (we recommend **"Best Model (Auto-select)"**, which automatically picks the most accurate model based on recent sales patterns).
4. Click **"Train & Generate Forecast"** (or use **"Forecast All Store Products"** to run all items at once).
5. The system displays an interactive chart showing historical sales alongside the future prediction with 90% confidence bands.

#### Step 5: Managing Inventory & Replenishment
Go to **Inventory Optimization**. The system supports two workflows:

- **Workflow A (Sales Data Only):**
  Use this if you haven't entered your current stock yet. The app calculates estimated product demand for your planning window plus a safety buffer. It clearly reminds you that actual stock is unknown, preventing accidental over-ordering.

- **Workflow B (Sales + Current Stock):**
  Use this when current shelf stock is known. The app calculates:
  - **Inventory Position ($IP$):** What you have on hand plus incoming orders.
  - **Reorder Point ($ROP$):** The stock level where you must place an order so you don't run out before the supplier delivers.
  - **Safety Stock ($SS$):** A calculated cushion to protect against unexpected sales spikes.
  - **Order Quantity:** Suggested order rounded up to the supplier's Minimum Order Quantity (MOQ) and case pack sizes.

#### Step 6: Reviewing and Editing Orders
- In the **Inventory Optimization** table, you can click directly on the **"Suggested Order Qty"** cell to modify any number based on your personal supplier relationships or cash flow constraints before downloading reports.

#### Step 7: Exporting to Excel
- Go to **Reports & Downloads**.
- Click **"Download Master Retail Analytics & Inventory Workbook (.xlsx)"**.
- This generates a formatted multi-tab spreadsheet ready to be emailed to suppliers or kept for monthly store audits.
