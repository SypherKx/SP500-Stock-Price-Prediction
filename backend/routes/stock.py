import requests
import pandas as pd
from fastapi import APIRouter
from backend.services.stock_service import (
    SP500_TICKERS,
    resolve_ticker,
    fetch_stock_data_cached,
    generate_synthetic_data
)

router = APIRouter(prefix="/api")


@router.get("/sp500-tickers")
def get_sp500_tickers():
    """Return the full cached S&P 500 constituent list."""
    return {
        "count": len(SP500_TICKERS),
        "tickers": [{"symbol": sym, "name": name} for sym, name in sorted(SP500_TICKERS.items())]
    }


@router.get("/search-suggest")
def search_suggest(q: str = ""):
    """
    Return typeahead suggestions filtered to S&P 500 constituents only.
    Matches against ticker symbol AND company name.
    """
    q = q.strip().upper()
    if not q or len(q) < 1:
        return {"suggestions": []}

    suggestions = []
    # First: exact symbol prefix matches (highest priority)
    for sym, name in SP500_TICKERS.items():
        if sym.startswith(q):
            suggestions.append({"symbol": sym, "name": name, "match_type": "symbol"})

    # Second: company name contains query (case-insensitive)
    q_lower = q.lower()
    for sym, name in SP500_TICKERS.items():
        if q_lower in name.lower() and sym not in [s["symbol"] for s in suggestions]:
            suggestions.append({"symbol": sym, "name": name, "match_type": "name"})

    # Sort: symbol prefix matches first, then alphabetically
    suggestions.sort(key=lambda x: (0 if x["match_type"] == "symbol" else 1, x["symbol"]))
    return {"suggestions": suggestions[:8]}


@router.get("/stock-info")
def get_stock_info(ticker: str = "^GSPC"):
    """Fetch live quote information for the given ticker with simulation fallback."""
    resolved = resolve_ticker(ticker)
    
    try:
        # Use cache for stock info fetch
        hist, source = fetch_stock_data_cached(resolved, period="1y")
        is_simulation = (source == "simulation")
        
        latest = hist.iloc[-1]
        prev_close = hist.iloc[-2]["Close"]
        change = latest["Close"] - prev_close
        pct_change = (change / prev_close) * 100
        
        # 52-week high and low
        week52_high = float(hist["High"].max())
        week52_low = float(hist["Low"].min())
        
        display_name = resolved.upper()
        currency = "USD"
        market_cap = None
        
        if not is_simulation:
            try:
                # Import yfinance locally to fetch ticker info
                import yfinance as yf
                from backend.config import get_yfinance_session
                t = yf.Ticker(resolved, session=get_yfinance_session())
                info = t.info
                display_name = info.get("longName", info.get("shortName", resolved))
                if display_name is None or display_name == "None":
                    display_name = resolved.upper()
                currency = info.get("currency", "USD")
                market_cap = info.get("marketCap")
            except Exception:
                pass
            
        if is_simulation:
            display_name = f"{resolved.upper()} (Simulation)"
            
        return {
            "symbol": resolved.upper(),
            "name": display_name,
            "current_price": float(latest["Close"]),
            "change": float(change),
            "pct_change": float(pct_change),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "volume": int(latest["Volume"]),
            "week52_high": week52_high,
            "week52_low": week52_low,
            "market_cap": market_cap,
            "currency": currency,
            "market": "Simulation" if is_simulation else "Live",
            "data_source": source
        }
    except Exception as e:
        print(f"Stock info error: {e}")
        # Synthetic fallback
        synthetic_df = generate_synthetic_data(resolved, period="1y")
        latest = synthetic_df.iloc[-1]
        prev_close = synthetic_df.iloc[-2]["Close"]
        change = latest["Close"] - prev_close
        pct_change = (change / prev_close) * 100
        week52_high = float(synthetic_df["High"].max())
        week52_low = float(synthetic_df["Low"].min())
        return {
            "symbol": resolved.upper(),
            "name": f"{resolved.upper()} (Simulation)",
            "current_price": float(latest["Close"]),
            "change": float(change),
            "pct_change": float(pct_change),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "volume": int(latest["Volume"]),
            "week52_high": week52_high,
            "week52_low": week52_low,
            "market_cap": None,
            "currency": "USD",
            "market": "Simulation",
            "data_source": "simulation"
        }


@router.get("/stock-data")
def get_stock_data(ticker: str = "^GSPC", period: str = "1y"):
    """Fetch historical stock price data with simulation fallback."""
    resolved = resolve_ticker(ticker)
    
    try:
        df, source = fetch_stock_data_cached(resolved, period=period)
        df = df.reset_index()
        
        if "Date" in df.columns:
            df["DateStr"] = df["Date"].dt.strftime('%Y-%m-%d')
        elif "index" in df.columns:
            df["DateStr"] = df["index"].dt.strftime('%Y-%m-%d')
        else:
            df["DateStr"] = df.index.to_series().dt.strftime('%Y-%m-%d')
            
        data_points = []
        for _, row in df.iterrows():
            data_points.append({
                "date": row["DateStr"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        return {
            "symbol": resolved.upper(),
            "period": period,
            "prices": data_points,
            "data_source": source
        }
    except Exception as e:
        print(f"Stock data error: {e}")
        df = generate_synthetic_data(resolved, period=period)
        df = df.reset_index()
        if "Date" in df.columns:
            df["DateStr"] = df["Date"].dt.strftime('%Y-%m-%d')
        else:
            df["DateStr"] = df.index.to_series().dt.strftime('%Y-%m-%d')
        data_points = []
        for _, row in df.iterrows():
            data_points.append({
                "date": row["DateStr"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        return {
            "symbol": resolved.upper(),
            "period": period,
            "prices": data_points,
            "data_source": "simulation"
        }
