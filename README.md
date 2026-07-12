# S&P 500 Stock Price Prediction Platform 📈🚀

Welcome to **StockPredict AI** — a premium, enterprise-grade, machine-learning-powered forecasting system that tries to predict S&P 500 stock directions so you can make data-driven decisions (or justify your speculative market calls to your manager). 

Now redesigned with an editorial, high-contrast **Revolut-style marketing canvas** that alternates true black storytelling bands (`#000000`) and pure white catalogue bands (`#ffffff`) for that magazine-spread rhythm your stakeholders love.

---

## 🏛️ Corporate Disclaimer (Or: Why Legal Wrote This)
> [!WARNING]
> **This is not financial advice.** All predictions are simulated mathematical models based on historical Yahoo Finance data. If the model says "Active Buy" and the stock crashes tomorrow, scikit-learn's `RandomForestClassifier` is legally shielded, and our server logs will silently "rotate." Past performance is merely a statistical suggestion.

---

## 🏗️ Architecture & Folder Structure
We believe in clean codebases that survive developer churn. Here is the structure of the platform:

```
├── backend/                       # FastAPI Backend (Python)
│   ├── routes/                    # API Endpoints
│   │   ├── predict.py             # Re-runs ML pipeline, training & prediction
│   │   └── stock.py               # Serves real-time OHLCV data & S&P suggestions
│   ├── services/                  # Business Logic Layer
│   │   ├── ml_service.py          # Random Forest training, rolling window evaluation
│   │   └── stock_service.py       # Caching, session setups, Wikipedia scraping
│   ├── tests/                     # Automated unit testing suite
│   ├── config.py                  # Global variables & headers (prevents yfinance bans)
│   ├── main.py                    # App router initialization
│   └── models.py                  # Pydantic schemas (fintech WCAG touched)
│
├── frontend/                      # Web Client (Vanilla Stack)
│   ├── app.js                     # Chart.js rendering, reveal triggers, pipeline calls
│   ├── index.html                 # Restructured layout in alternating dark/light bands
│   └── style.css                  # Revolut design system custom tokens, buttons & transitions
│
├── notebooks/                     # Exploratory Data Analysis (Data Science sandbox)
│   └── Stock_Market_Predcition.ipynb
│
├── main.py                        # Root execution script
├── requirements.txt               # Documented python dependencies
└── .gitignore                     # Keeps junk (and your API keys) out of Git
```

---

## 🧠 Behind the AI (Under the Hood)
1. **Bootstrap Aggregating**: We use a `RandomForestClassifier` (by default with 200 estimators). Why? Because decision trees are easier to explain to managers than neural networks.
2. **Feature Engineering**: Calculates rolling average ratios and trend vectors across horizons (`2d`, `5d`, `60d`, `250d`, `1000d`) to feed the forest.
3. **Rolling-Window Backtesting**: Evaluates model precision chronologically on a 250-day test set using the previous 2,500 days for training. **Zero data leakage** (we do not look into the future, unlike some hedge funds).
4. **Decision Threshold**: Adjust the confidence threshold (e.g., `60%`).
   * *Tip*: Bumping this to `90%` will result in zero Buy signals, which is mathematically the safest portfolio strategy known to mankind.

---

## 🚀 Getting Started (How to Run it)

### Prerequisites
* Python **3.8 - 3.11**
* A functioning internet connection (Yahoo Finance API rate-limiters are watching us).

### 1. Installation
Clone the repository and install the requirements:
```bash
git clone https://github.com/SypherKx/SP500-Stock-Price-Prediction.git
cd SP500-Stock-Price-Prediction
pip install -r requirements.txt
```

### 2. Launch the Application
Run the root launcher:
```bash
python main.py
```
Uvicorn will spin up, and you can access the dashboard at:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🛠️ GitHub Guidelines (For Future Contributors)
* **Code Styling**: Keep body type in Inter and display headers clamped to lineHeight `1.0` with negative tracking. Do not introduce drop shadows on cards. Elevation is canvas + surface-luminance shifts only.
* **Scraper Etiquette**: Don't flood Yahoo Finance without our custom user-agent config. We don't want to get our corporate IP range banned.
* **Local environment**: Put your secret configurations in a `.env` file; it is ignored by our `.gitignore` to prevent database keys leaking on Reddit.

---

## 📉 Known Gaps & Roadmap
* [ ] Support for non-S&P 500 stocks (e.g., meme coins and obscure penny stocks).
* [ ] Real-time trade executions (so you can automate your financial ruin).
* [ ] Add a "Blame Legal" button that instantly redirects to a random page in the SEC regulatory filings database.

Made with ☕ by the StockPredict AI Development Team. For support, please schedule a meeting that could have been an email.
