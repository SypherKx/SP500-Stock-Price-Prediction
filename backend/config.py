import requests
from typing import Dict

# Caching Configuration
CACHE_TTL = 300  # 5 minutes in seconds

# Session setup with a custom browser agent to avoid Yahoo Finance blocks
def get_yfinance_session() -> requests.Session:
    """Create a requests Session with a browser User-Agent to prevent yfinance rate-limiting/blocking."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

# Fallback S&P 500 constituents if Wikipedia scraping fails
FALLBACK_SP500_TICKERS: Dict[str, str] = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corp.",
    "GOOGL": "Alphabet Inc. Class A",
    "GOOG": "Alphabet Inc. Class C",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "BRK-B": "Berkshire Hathaway B",
    "UNH": "UnitedHealth Group",
    "XOM": "Exxon Mobil Corp.",
    "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "PG": "Procter & Gamble Co.",
    "MA": "Mastercard Inc.",
    "HD": "Home Depot Inc.",
    "CVX": "Chevron Corp.",
    "MRK": "Merck & Co.",
    "ABBV": "AbbVie Inc.",
    "LLY": "Eli Lilly and Co.",
    "PEP": "PepsiCo Inc.",
    "KO": "Coca-Cola Co.",
    "AVGO": "Broadcom Inc.",
    "COST": "Costco Wholesale Corp.",
    "TMO": "Thermo Fisher Scientific",
    "MCD": "McDonald's Corp.",
    "ACN": "Accenture PLC",
    "WMT": "Walmart Inc.",
    "ABT": "Abbott Laboratories",
    "DHR": "Danaher Corp.",
    "CSCO": "Cisco Systems Inc.",
    "NKE": "Nike Inc.",
    "VZ": "Verizon Communications",
    "ADBE": "Adobe Inc.",
    "NEE": "NextEra Energy Inc.",
    "TXN": "Texas Instruments Inc.",
    "CRM": "Salesforce Inc.",
    "QCOM": "Qualcomm Inc.",
    "WFC": "Wells Fargo & Co.",
    "AMD": "Advanced Micro Devices",
    "MS": "Morgan Stanley",
    "BAC": "Bank of America Corp.",
    "GS": "Goldman Sachs Group",
    "INTC": "Intel Corp.",
    "IBM": "International Business Machines",
    "CAT": "Caterpillar Inc.",
    "GE": "General Electric Co.",
    "BA": "Boeing Co.",
    "MMM": "3M Co.",
    "^GSPC": "S&P 500 Index"
}
