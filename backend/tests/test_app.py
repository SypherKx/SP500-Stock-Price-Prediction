import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_default_params():
    """Verify that default params are successfully returned."""
    response = client.get("/api/default-params")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "^GSPC"
    assert "n_estimators" in data
    assert "confidence_threshold" in data

def test_stock_info():
    """Verify live quote fetching for S&P 500."""
    response = client.get("/api/stock-info?ticker=^GSPC")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "^GSPC"
    assert "current_price" in data
    assert "change" in data
    assert "high" in data
    assert "volume" in data

def test_stock_data():
    """Verify stock history retrieval."""
    response = client.get("/api/stock-data?ticker=^GSPC&period=1mo")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "^GSPC"
    assert "prices" in data
    assert len(data["prices"]) > 0
    assert "close" in data["prices"][0]
    assert "date" in data["prices"][0]

def test_predict_endpoint():
    """Test full training, backtesting and forecasting pipeline on a small test model."""
    payload = {
        "ticker": "^GSPC",
        "n_estimators": 10,  # Small value for fast test execution
        "min_samples_split": 100,
        "confidence_threshold": 0.55,
        "horizons": [2, 5],  # Short horizons to minimize NA rows
        "use_rolling_predictors": True
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ticker"] == "^GSPC"
    assert "metrics" in data
    assert "forecast" in data
    assert "precision" in data["metrics"]
    assert "prediction" in data["forecast"]
    assert "probability" in data["forecast"]
    assert len(data["backtest_history"]) > 0
