import io
import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Tuple, Optional
from backend.config import get_yfinance_session, FALLBACK_SP500_TICKERS, CACHE_TTL

# Global S&P 500 constituent store
SP500_TICKERS: Dict[str, str] = {}

# In-memory cache for historical stock data
# Key: (ticker_symbol, period) -> Value: (timestamp, dataframe)
_STOCK_CACHE: Dict[Tuple[str, str], Tuple[float, pd.DataFrame]] = {}


def load_sp500_list():
    """Fetch the current S&P 500 constituent list from Wikipedia and cache it."""
    global SP500_TICKERS
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        session = get_yfinance_session()
        resp = session.get(url, timeout=10)
        tables = pd.read_html(io.StringIO(resp.text))
        df = tables[0]  # First table is the constituent list
        
        tickers_dict = {}
        for _, row in df.iterrows():
            sym = str(row.get("Symbol", "")).strip().replace(".", "-")
            name = str(row.get("Security", sym)).strip()
            if sym:
                tickers_dict[sym.upper()] = name
                
        # Always allow the index itself
        tickers_dict["^GSPC"] = "S&P 500 Index"
        SP500_TICKERS.clear()
        SP500_TICKERS.update(tickers_dict)
        print(f"[S&P 500] Loaded {len(SP500_TICKERS)} tickers from Wikipedia.")
    except Exception as e:
        print(f"[S&P 500] Failed to load from Wikipedia: {e}. Using hardcoded fallback.")
        SP500_TICKERS.clear()
        SP500_TICKERS.update(FALLBACK_SP500_TICKERS)


def resolve_ticker(query: str) -> str:
    """Resolve a company name or query to a valid ticker symbol using Yahoo Finance Search API."""
    query = query.strip()
    if not query:
        return "^GSPC"
        
    # If query is already a typical ticker (e.g. starts with ^, or is short uppercase letters)
    # try it directly first.
    if len(query) <= 5 and query.isalpha():
        return query.upper()
    if query.startswith("^"):
        return query.upper()
        
    try:
        session = get_yfinance_session()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={requests.utils.quote(query)}"
        res = session.get(url, timeout=5)
        if res.status_code == 200:
            results = res.json()
            quotes = results.get("quotes", [])
            if quotes:
                # Find the first equity or index symbol
                for quote in quotes:
                    quote_type = quote.get("quoteType", "")
                    symbol = quote.get("symbol", "")
                    # Accept Equities, Indices, ETFs
                    if symbol and (quote_type in ["EQUITY", "INDEX", "ETF"] or quote.get("typeDisp") in ["Equity", "Index", "ETF"]):
                        print(f"Resolved search query '{query}' to ticker '{symbol}' ({quote.get('shortname')})")
                        return symbol
                # Fallback to first symbol found
                return quotes[0].get("symbol", query.upper())
    except Exception as e:
        print(f"Ticker resolution failed for query '{query}': {str(e)}")
        
    return query.upper()


def generate_synthetic_data(symbol: str, period: str = "max") -> pd.DataFrame:
    """Generate realistic synthetic stock data for fallback if yfinance is blocked/rate-limited."""
    print(f"Warning: Generating synthetic simulation data for ticker {symbol} (period={period}).")
    np.random.seed(42) # Deterministic for consistent backtests
    
    # Determine length based on period
    if period == "1mo":
        days = 30
    elif period == "6mo":
        days = 180
    elif period == "1y":
        days = 252 # Trading days
    elif period == "5y":
        days = 252 * 5
    else: # max or 10y
        days = 252 * 15 # 15 years of trading days (~3780 points)
        
    # Generate dates (business days ending today)
    end_date = pd.Timestamp.now()
    dates = pd.date_range(end=end_date, periods=days, freq='B')
    
    # Geometric Brownian Motion parameters tailored to typical stock markets
    S0 = 100.0
    if symbol.upper() == "^GSPC":
        S0 = 4000.0
    elif symbol.upper() in ["AAPL", "MSFT", "GOOG"]:
        S0 = 150.0
        
    mu = 0.09 / 252 # 9% annual return drift
    sigma = 0.16 / np.sqrt(252) # 16% annual volatility
    
    returns = np.random.normal(mu, sigma, len(dates))
    price_paths = S0 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame(index=dates)
    df["Close"] = price_paths
    df["Open"] = df["Close"] * (1 + np.random.normal(0, 0.002, len(dates)))
    df["High"] = df[["Open", "Close"]].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.004, len(dates))))
    df["Low"] = df[["Open", "Close"]].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.004, len(dates))))
    df["Volume"] = np.random.randint(1000000, 10000000, len(dates))
    df.index.name = "Date"
    return df


def fetch_stock_data_cached(ticker_symbol: str, period: str) -> Tuple[pd.DataFrame, str]:
    """
    Fetch stock history from yfinance using an in-memory cache to prevent Yahoo Finance rate-limiting.
    Returns a tuple: (DataFrame, data_source) where data_source is 'live' or 'simulation'.
    """
    now = time.time()
    cache_key = (ticker_symbol.upper(), period)
    
    # Try cache first
    if cache_key in _STOCK_CACHE:
        timestamp, cached_df = _STOCK_CACHE[cache_key]
        if now - timestamp < CACHE_TTL:
            print(f"[CACHE HIT] Returning cached data for {ticker_symbol} ({period})")
            return cached_df, "live"
            
    # Cache miss or expired -> Fetch from yfinance
    print(f"[CACHE MISS] Fetching from yfinance for {ticker_symbol} ({period})")
    try:
        session = get_yfinance_session()
        ticker = yf.Ticker(ticker_symbol, session=session)
        df = ticker.history(period=period)
        
        if df.empty or len(df) < 5:
            raise ValueError("Empty or tiny dataframe returned from yfinance")
            
        # Success -> cache it and return
        _STOCK_CACHE[cache_key] = (now, df)
        return df, "live"
    except Exception as e:
        print(f"yfinance fetch failed for {ticker_symbol} ({period}): {e}")
        
        # Fallback 1: Return expired cached data if available
        if cache_key in _STOCK_CACHE:
            print(f"[CACHE FALLBACK] Returning expired/stale cache data for {ticker_symbol}")
            return _STOCK_CACHE[cache_key][1], "live"
            
        # Fallback 2: Generate synthetic data
        synthetic_df = generate_synthetic_data(ticker_symbol, period=period)
        return synthetic_df, "simulation"
