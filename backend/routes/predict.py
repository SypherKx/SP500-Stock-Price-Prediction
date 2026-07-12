from fastapi import APIRouter, HTTPException
from backend.models import PredictRequest
from backend.services.stock_service import resolve_ticker, SP500_TICKERS
from backend.services.ml_service import run_pipeline

router = APIRouter(prefix="/api")


@router.get("/default-params")
def get_default_params():
    """Return default parameters for model training."""
    return {
        "ticker": "^GSPC",
        "n_estimators": 200,
        "min_samples_split": 50,
        "confidence_threshold": 0.6,
        "horizons": [2, 5, 60, 250, 1000],
        "use_rolling_predictors": True
    }


@router.post("/predict")
def run_prediction(req: PredictRequest):
    """Retrain the model, execute backtesting and predict tomorrow's direction."""
    # Resolve ticker name to symbol first
    resolved = resolve_ticker(req.ticker)
    req.ticker = resolved

    # --- S&P 500 validation ---
    # Allow ^GSPC (the index itself) plus all cached constituents
    if resolved.upper() not in SP500_TICKERS and resolved.upper() != "^GSPC":
        raise HTTPException(
            status_code=400,
            detail=f"'{resolved}' is not an S&P 500 constituent. Please search for an S&P 500 stock."
        )

    try:
        results = run_pipeline(
            ticker=req.ticker,
            n_estimators=req.n_estimators,
            min_samples_split=req.min_samples_split,
            confidence_threshold=req.confidence_threshold,
            horizons=req.horizons,
            use_rolling_predictors=req.use_rolling_predictors
        )
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")
