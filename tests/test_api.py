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
    response = client.get("/api/reports/csv/sales")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert len(response.text) > 0

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
