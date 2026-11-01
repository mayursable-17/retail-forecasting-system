"""
Tests for FastAPI application endpoints (api/index.py) used in Vercel deployment.
"""

import pytest
from fastapi.testclient import TestClient
from api.index import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Retail Sales Forecasting" in response.text

def test_vercel_rewrite_paths_serve_html(client):
    for path in ["/api/index.py", "/api/index", "/index.html", "/inventory"]:
        resp = client.get(path)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "Retail Sales Forecasting" in resp.text

def test_unknown_api_endpoint_returns_404(client):
    resp = client.get("/api/unknown_route_123")
    assert resp.status_code == 404
    assert "not found" in resp.text.lower()

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "retail-forecasting-api"
    assert "version" in data

def test_api_shop(client):
    response = client.get("/api/shop")
    assert response.status_code == 200
    data = response.json()
    assert "shop_id" in data
    assert data["shop_id"] == 1
    assert "shop_name" in data

def test_api_dashboard(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["has_data"] is True
    assert "kpis" in data
    assert "daily_trend" in data
    assert "category_breakdown" in data
    assert "alerts" in data

def test_api_products(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "product_id" in data[0]

def test_api_inventory_recommendations_endpoint(client):
    response = client.get("/api/inventory/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "has_recommendations" in data

def test_api_csv_export(client):
    for rtype in ["sales", "products", "forecast", "purchase_order"]:
        response = client.get(f"/api/reports/csv/{rtype}")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

def test_api_excel_export(client):
    response = client.get("/api/reports/excel")
    assert response.status_code == 200
    assert "openxmlformats" in response.headers.get("content-type", "")
    assert len(response.content) > 0

def test_api_products_add_and_batch(client):
    add_payload = {
        "product_id": "TEST-SKU-99",
        "product_name": "Test SKU Item",
        "category": "Snacks",
        "unit_price": 50.0,
        "lead_time_days": 5,
        "minimum_order_quantity": 10.0,
        "case_pack_size": 2.0,
        "initial_stock": 25.0
    }
    res = client.post("/api/products/add", json=add_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Check that product is present
    prods = client.get("/api/products").json()
    assert any(p["product_id"] == "TEST-SKU-99" for p in prods)

    # Batch update
    batch_payload = {
        "products": [
            {
                "product_id": "TEST-SKU-99",
                "unit_price": 55.0,
                "lead_time_days": 6,
                "minimum_order_quantity": 12.0,
                "case_pack_size": 3.0
            }
        ]
    }
    b_res = client.post("/api/products/batch", json=batch_payload)
    assert b_res.status_code == 200
    assert b_res.json()["updated"] >= 1

def test_api_shop_defaults_update(client):
    payload = {
        "lead_time_days": 4,
        "review_period_days": 7,
        "service_level": 0.95,
        "safety_stock_method": "variability",
        "replenishment_buffer_pct": 0.20
    }
    response = client.post("/api/shop/defaults", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verify updated values in get_shop
    shop_resp = client.get("/api/shop")
    assert shop_resp.json()["default_lead_time_days"] == 4


def test_api_demo_seed(client):
    response = client.post("/api/demo/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "demo dataset" in data["message"].lower()

    # Verify dashboard and alerts are populated after demo seed
    dash_resp = client.get("/api/dashboard")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["has_data"] is True
    assert dash_data["kpis"]["total_products"] > 0
    assert dash_data["alerts"]["has_forecast"] is True


def test_api_upload_preview_with_nan(client):
    # CSV with missing values which causes NaN in pandas
    csv_content = b"Date,Product_ID,Quantity,Revenue\n2026-10-01,P1,,500.0\n2026-10-02,P2,10,\n"
    response = client.post(
        "/api/upload/preview",
        files={"file": ("test_nan.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "detected_mapping" in data
    assert "sample_rows" in data
    assert len(data["sample_rows"]) == 2
    # Ensure NaN values are serialized cleanly as None / null in JSON
    assert data["sample_rows"][0]["Quantity"] is None
    assert data["sample_rows"][1]["Revenue"] is None


def test_api_upload_process_sales(client):
    import json
    csv_content = (
        b"Date,Product_ID,Product_Name,Category,Quantity,Unit_Price,Revenue\n"
        b"2026-10-01,SKU-1,Item 1,Groceries,10,50,500\n"
        b"2026-10-02,SKU-1,Item 1,Groceries,12,50,600\n"
    )
    mapping = {
        "date": "Date",
        "product_id": "Product_ID",
        "product_name": "Product_Name",
        "category": "Category",
        "quantity": "Quantity",
        "unit_price": "Unit_Price",
        "revenue": "Revenue"
    }
    response = client.post(
        "/api/upload/process",
        files={"file": ("sales_test.csv", csv_content, "text/csv")},
        data={
            "dataset_type": "sales",
            "allow_returns": "true",
            "mapping_json": json.dumps(mapping)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["rows_cleaned"] == 2


def test_api_upload_process_inventory(client):
    import json
    csv_content = (
        b"Product_ID,Product_Name,Stock,On_Order,Lead_Time\n"
        b"SKU-1,Item 1,50,10,5\n"
    )
    mapping = {
        "product_id": "Product_ID",
        "product_name": "Product_Name",
        "stock": "Stock",
        "on_order": "On_Order",
        "lead_time": "Lead_Time"
    }
    response = client.post(
        "/api/upload/process",
        files={"file": ("inventory_test.csv", csv_content, "text/csv")},
        data={
            "dataset_type": "inventory",
            "allow_returns": "true",
            "mapping_json": json.dumps(mapping)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["products_count"] == 1
