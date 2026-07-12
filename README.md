# 🧠 ML-Powered S&P 500 Stock Price Prediction Platform

An enterprise-grade, machine-learning forecasting dashboard designed to predict next-day price movements of S&P 500 constituents. The platform combines a FastAPI backend running a real-time **Random Forest Classifier** with a premium, high-contrast user interface for interactive parameter tuning and signal explainability.

---

## 🏛️ Project Goal & Key Focus
Unlike naive models that predict absolute stock prices (which are highly non-stationary and prone to lag), this project focuses on **binary classification of direction**: predicting whether the stock close price tomorrow will be higher than today's close.

$$Target_t = \begin{cases} 1 & \text{if } Close_{t+1} > Close_t \\ 0 & \text{otherwise} \end{cases}$$

---

## 🔬 Machine Learning Pipeline

### 1. Feature Engineering
The model improves on raw OHLCV inputs by generating rolling statistical metrics across multiple historical horizons ($H \in \{2, 5, 60, 250, 1000\}$ days) to capture both short-term momentum and long-term macro trends:
* **Close Price Ratio**: Today's close price divided by the rolling average close price over horizon $H$. Indicates whether the stock is relatively overbought or oversold compared to its history.
  $$Ratio_{t, H} = \frac{Close_t}{\frac{1}{H}\sum_{i=0}^{H-1} Close_{t-i}}$$
* **Trend Score**: The number of days the stock closed higher over the last $H$ days, shifted by 1 day to prevent forward data leakage.
  $$Trend_{t, H} = \sum_{i=1}^{H} Target_{t-i}$$

### 2. Random Forest Classifier
* **Bootstrapped Decision Trees**: Combines predictions from multiple randomized decision trees to reduce variance and avoid overfitting.
* **Real-time FastAPI retrains**: Hyperparameters (`n_estimators`, `min_samples_split`, and horizons) are exposed to the UI, triggering on-demand retraining of the scikit-learn model in parallel cores (`n_jobs=-1`).

### 3. Chronological Rolling-Window Backtesting
To ensure realistic evaluation and prevent **look-ahead bias/data leakage**, we implement a chronological rolling backtest:
* **Initial Train Pool**: First $2,500$ trading days (approx. 10 years).
* **Step Size**: $250$ trading days (approx. 1 year).
* The model trains on all data up to year $Y$, predicts year $Y+1$, adds year $Y+1$ to training data, and repeats.

---

## 📈 Precision & Decision Threshold Tuning

### Custom Decision Threshold
Instead of the default $50\%$ binary split, we introduce a custom **Decision Threshold** (configurable in the UI, e.g., $60\%$):
* The model only triggers a **BULLISH (BUY)** signal if the random forest probability is $\ge Threshold$.
* If the probability is $\le (1 - Threshold)$, it triggers a **BEARISH (SELL/AVOID)** signal.
* Everything in-between is marked as **NEUTRAL (HOLD)**.

> [!NOTE]
> Increasing the threshold (e.g. to $70\%$) yields fewer bullish signals but significantly increases the **Precision Rate** of the signals it does generate.

### Metric Evaluation
* **Model Precision**: $\frac{\text{True Bullish Predictions}}{\text{Total Bullish Predictions}}$. Tells you how often the model was correct when it actually predicted a price rise.
* **Baseline Precision**: The buy-and-hold success rate over the test period.
* **Beat Rate**: The margin by which the model outpaces a standard passive investment strategy.

---

## 📂 Project Architecture

```
├── backend/                       # FastAPI Server Code
│   ├── routes/                    # API Routing Layer
│   │   ├── predict.py             # Re-runs ML pipeline, training & prediction
│   │   └── stock.py               # Serves real-time OHLCV data & S&P suggestions
│   ├── services/                  # Business Logic Layer
│   │   ├── ml_service.py          # Random Forest training, rolling window evaluation
│   │   └── stock_service.py       # Caching, session setups, Wikipedia scraping
│   ├── tests/                     # Automated unit testing suite
│   ├── config.py                  # Caching parameters and browser request agents
│   ├── main.py                    # Server config
│   └── models.py                  # Pydantic validation schemas
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
└── .gitignore                     # Git filter configuration
```

---

## 🚀 Setting Up the Repository

### Prerequisites
* Python **3.8 - 3.11**

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/SypherKx/SP500-Stock-Price-Prediction.git
cd SP500-Stock-Price-Prediction
pip install -r requirements.txt
```

### 2. Run the platform
Start the local FastAPI server:
```bash
python main.py
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🏛️ Disclaimer
This project is an academic and engineering exploration of machine learning applications in quantitative finance. It is not financial advice. Past performance of random forest classification does not guarantee future market returns.
