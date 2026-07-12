from pydantic import BaseModel, Field
from typing import List

class PredictRequest(BaseModel):
    ticker: str = Field(default="^GSPC", description="Yahoo Finance Ticker symbol")
    n_estimators: int = Field(default=200, ge=10, le=500, description="Number of trees in forest")
    min_samples_split: int = Field(default=50, ge=2, le=200, description="Minimum samples to split a node")
    confidence_threshold: float = Field(default=0.6, ge=0.5, le=0.9, description="Confidence threshold to predict upward trend")
    horizons: List[int] = Field(default=[2, 5, 60, 250, 1000], description="Rolling average horizons")
    use_rolling_predictors: bool = Field(default=True, description="Whether to use rolling averages/trends as features")
