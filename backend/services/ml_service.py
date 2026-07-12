import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
from backend.services.stock_service import fetch_stock_data_cached, generate_synthetic_data


def build_dataset(ticker_symbol: str) -> Tuple[pd.DataFrame, str]:
    """Fetch historical stock price data from cached service with fallback."""
    df, source = fetch_stock_data_cached(ticker_symbol, period="max")
    df = df.copy()
    for col in ["Dividends", "Stock Splits"]:
        if col in df.columns:
            del df[col]
    return df, source


def prepare_features(df: pd.DataFrame, horizons: List[int]) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Build features (rolling ratios, trend columns) and setup targets."""
    df = df.copy()
    
    # Target setup (1 if price goes up tomorrow, else 0)
    df["Tomorrow"] = df["Close"].shift(-1)
    df["Target"] = (df["Tomorrow"] > df["Close"]).astype(int)
    
    # Filter data from 1990-01-01 onwards as done in the notebook
    df = df.loc["1990-01-01":].copy()
    if len(df) < 200:
        # If dataset starts after 1990 and is too small, use whole dataset
        df = df.copy()
        
    base_predictors = ["Close", "Volume", "Open", "High", "Low"]
    new_predictors = []
    
    # Filter horizons to only keep those smaller than the dataset size
    dataset_length = len(df)
    valid_horizons = [h for h in horizons if h < dataset_length]
    
    for horizon in valid_horizons:
        rolling_averages = df.rolling(horizon).mean()
        
        # Close price / rolling average close
        ratio_column = f"Close_Ratio_{horizon}"
        df[ratio_column] = df["Close"] / rolling_averages["Close"]
        
        # Trend over horizon: sum of targets shifted by 1 day (prevents leakage)
        trend_column = f"Trend_{horizon}"
        df[trend_column] = df.shift(1).rolling(horizon).sum()["Target"]
        
        new_predictors.extend([ratio_column, trend_column])
        
    df = df.dropna()
    return df, base_predictors, new_predictors


def predict_model(train: pd.DataFrame, test: pd.DataFrame, predictors: List[str], model: RandomForestClassifier, threshold: float) -> pd.DataFrame:
    """Train the model on train data, predict on test data applying threshold."""
    model.fit(train[predictors], train["Target"])
    preds_proba = model.predict_proba(test[predictors])[:, 1]
    
    # Apply custom threshold
    preds = np.zeros_like(preds_proba)
    preds[preds_proba >= threshold] = 1
    preds[preds_proba < threshold] = 0
    
    preds_series = pd.Series(preds, index=test.index, name="Predictions")
    combined = pd.concat([test["Target"], preds_series], axis=1)
    combined["Probability"] = preds_proba
    return combined


def backtest_model(data: pd.DataFrame, model: RandomForestClassifier, predictors: List[str], threshold: float, start: int = 2500, step: int = 250) -> pd.DataFrame:
    """Implement chronological rolling window backtesting."""
    all_predictions = []
    
    # If the dataset is smaller than start, adjust start to fit
    actual_start = start
    if len(data) <= start:
        actual_start = min(1000, len(data) // 2)
    
    # Check if we have enough data to backtest at all
    if len(data) <= actual_start + step:
        step = max(20, (len(data) - actual_start) // 5)
        if step <= 0:
            train_idx = int(len(data) * 0.8)
            train = data.iloc[:train_idx]
            test = data.iloc[train_idx:]
            return predict_model(train, test, predictors, model, threshold)
            
    for i in range(actual_start, data.shape[0], step):
        train_chunk = data.iloc[0:i].copy()
        test_chunk = data.iloc[i:(i+step)].copy()
        predictions = predict_model(train_chunk, test_chunk, predictors, model, threshold)
        all_predictions.append(predictions)
        
    if not all_predictions:
        train_idx = int(len(data) * 0.8)
        train = data.iloc[:train_idx]
        test = data.iloc[train_idx:]
        return predict_model(train, test, predictors, model, threshold)
        
    return pd.concat(all_predictions)


def run_pipeline(ticker: str, n_estimators: int, min_samples_split: int, confidence_threshold: float, horizons: List[int], use_rolling_predictors: bool) -> Dict[str, Any]:
    """Train, backtest, and predict tomorrow's direction for a given ticker."""
    # Step 1: Fetch data
    df, source = build_dataset(ticker)
    
    # Step 2: Prepare features
    processed_df, base_predictors, rolling_predictors = prepare_features(df, horizons)
    
    # Choose predictor set based on request
    predictors = rolling_predictors if use_rolling_predictors else base_predictors
    
    # Ensure we have predictors
    if not predictors:
        raise ValueError("No valid predictors created. Make sure rolling horizons are smaller than data length.")
        
    # Step 3: Initialize Model (Set n_jobs=-1 to use all cores for training speedup!)
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        min_samples_split=min_samples_split,
        random_state=1,
        n_jobs=-1
    )
    
    # Step 4: Run Backtest to evaluate model performance
    backtest_results = backtest_model(
        processed_df,
        model,
        predictors,
        confidence_threshold
    )
    
    targets = backtest_results["Target"].values
    preds = backtest_results["Predictions"].values
    
    if np.sum(preds) > 0:
        precision = float(precision_score(targets, preds))
    else:
        precision = 0.0
        
    pred_counts = pd.Series(preds).value_counts().to_dict()
    bullish_count = int(pred_counts.get(1.0, 0) + pred_counts.get(1, 0))
    bearish_count = int(pred_counts.get(0.0, 0) + pred_counts.get(0, 0))
    
    baseline_precision = float(np.sum(targets) / len(targets))
    
    # Step 5: Make Tomorrow's Prediction
    model.fit(processed_df[predictors], processed_df["Target"])
    
    df_for_today = df.copy()
    dataset_length = len(df_for_today)
    valid_horizons = [h for h in horizons if h < dataset_length]
    
    for horizon in valid_horizons:
        rolling_averages = df_for_today.rolling(horizon).mean()
        
        ratio_column = f"Close_Ratio_{horizon}"
        df_for_today[ratio_column] = df_for_today["Close"] / rolling_averages["Close"]
        
        df_for_today["Up_Day"] = (df_for_today["Close"] > df_for_today["Close"].shift(1)).astype(int)
        trend_column = f"Trend_{horizon}"
        df_for_today[trend_column] = df_for_today["Up_Day"].rolling(horizon).sum()
        
    latest_row = df_for_today.iloc[[-1]]
    
    tomorrow_prob = float(model.predict_proba(latest_row[predictors])[0, 1])
    tomorrow_prediction = 1 if tomorrow_prob >= confidence_threshold else 0
    
    # Explainable AI: Identify why the model predicted Up/Down
    feature_importances = model.feature_importances_
    sorted_indices = np.argsort(feature_importances)[::-1]
    top_indices = sorted_indices[:5]  # Get top 5 factors
    
    reasons = []
    for idx in top_indices:
        feat_name = predictors[idx]
        importance = feature_importances[idx]
        current_val = float(latest_row[feat_name].iloc[0])
        
        if "Close_Ratio_" in feat_name:
            horizon = feat_name.replace("Close_Ratio_", "")
            pct_diff = (current_val - 1.0) * 100
            if pct_diff > 2:
                signal = "bullish"
                icon = "trending-up"
                explanation = f"Currently trading {pct_diff:.1f}% above its {horizon}-day moving average — a strong sign of upward momentum."
            elif pct_diff > 0:
                signal = "neutral-bullish"
                icon = "trending-up"
                explanation = f"Trading slightly ({pct_diff:.1f}%) above its {horizon}-day average, indicating mild positive momentum."
            elif pct_diff > -2:
                signal = "neutral-bearish"
                icon = "trending-down"
                explanation = f"Trading slightly ({abs(pct_diff):.1f}%) below its {horizon}-day average, indicating mild downward pressure."
            else:
                signal = "bearish"
                icon = "trending-down"
                explanation = f"Trading {abs(pct_diff):.1f}% below its {horizon}-day moving average — suggesting bearish momentum."
            
            reasons.append({
                "factor": f"{horizon}-Day Price Momentum",
                "importance": int(round(importance * 100)),
                "current_value": f"{current_val:.3f}",
                "signal": signal,
                "icon": icon,
                "explanation": explanation
            })
        elif "Trend_" in feat_name:
            horizon = feat_name.replace("Trend_", "")
            horizon_int = int(horizon)
            ratio = current_val / horizon_int if horizon_int > 0 else 0
            if ratio >= 0.65:
                signal = "bullish"
                icon = "bar-chart"
                explanation = f"Stock closed higher on {int(current_val)} of the last {horizon} trading days ({ratio*100:.0f}%) — a strong bullish trend signal."
            elif ratio >= 0.50:
                signal = "neutral-bullish"
                icon = "bar-chart"
                explanation = f"More up days than down over {horizon} sessions ({int(current_val)}/{horizon}, {ratio*100:.0f}%) — trend is leaning bullish."
            elif ratio >= 0.35:
                signal = "neutral-bearish"
                icon = "bar-chart"
                explanation = f"Only {int(current_val)} up days in {horizon} sessions ({ratio*100:.0f}%) — trend is consolidating with a bearish lean."
            else:
                signal = "bearish"
                icon = "bar-chart"
                explanation = f"Only {int(current_val)} of {horizon} days closed higher ({ratio*100:.0f}%) — sustained downward pressure detected."
                
            reasons.append({
                "factor": f"{horizon}-Day Trend Strength",
                "importance": int(round(importance * 100)),
                "current_value": f"{int(current_val)}/{horizon} days up",
                "signal": signal,
                "icon": icon,
                "explanation": explanation
            })
    
    history_sample = backtest_results.tail(250)
    history_sample = history_sample.reset_index()
    if "Date" in history_sample.columns:
        history_sample["DateStr"] = history_sample["Date"].dt.strftime('%Y-%m-%d')
    elif "index" in history_sample.columns:
        history_sample["DateStr"] = history_sample["index"].dt.strftime('%Y-%m-%d')
    else:
        history_sample["DateStr"] = history_sample.index.to_series().dt.strftime('%Y-%m-%d')
        
    history_data = []
    for _, row in history_sample.iterrows():
        history_data.append({
            "date": row["DateStr"],
            "actual": int(row["Target"]),
            "predicted": int(row["Predictions"]),
            "probability": float(row["Probability"])
        })
        
    return {
        "success": True,
        "ticker": ticker.upper(),
        "metrics": {
            "precision": precision,
            "baseline_precision": baseline_precision,
            "bullish_predictions": bullish_count,
            "bearish_predictions": bearish_count,
            "total_eval_days": len(backtest_results)
        },
        "forecast": {
            "prediction": tomorrow_prediction,
            "probability": tomorrow_prob,
            "confidence_threshold": confidence_threshold,
            "as_of_date": df_for_today.index[-1].strftime('%Y-%m-%d')
        },
        "reasons": reasons,
        "backtest_history": history_data,
        "predictors_used": predictors,
        "data_source": source
    }
