# S&P 500 Stock Price Prediction (A Learning Journey) 📈🧠

Hi! I built this project to learn the fundamentals of **data cleaning**, **feature engineering**, and **machine learning model validation**. Instead of building a complex system I didn't understand, I wanted to learn how things work under the hood.

This project uses historical S&P 500 index data, cleans it, engineers custom rolling indicators, trains a **Random Forest Classifier**, and validates predictions using a realistic chronological backtesting process.

---

## 🎯 What I Wanted to Learn
1. **Data Cleaning**: How to handle financial time-series data, deal with missing records, and avoid the ultimate trap: **data leakage** (accidentally giving the model tomorrow's data to predict tomorrow's price).
2. **Feature Engineering**: Creating custom rolling predictors instead of using raw prices (which are highly non-stationary and hard for models to learn).
3. **Realistic Validation**: Why simple random splits (`train_test_split`) fail on time-series data, and how to build a rolling-window backtest.

---

## 🧹 How the Data is Cleaned & Prepared

The pipeline starts with raw historical data from `yfinance` and cleans it step-by-step:
1. **Removing Noise**: Dropped columns like `Dividends` and `Stock Splits` since index data doesn't require individual stock corporate action tracking.
2. **Creating the Target**:
   * Created a `Tomorrow` column by shifting the `Close` price back by 1 day (`df["Close"].shift(-1)`).
   * Created a binary `Target` column: `1` if tomorrow's price is higher than today's, `0` if it's lower or equal.
3. **Filtering History**: Filtered data from `1990-01-01` onwards. Very old market structures (like the 1920s or 70s) behave differently from modern computerized markets, so focusing on post-1990 data keeps the model relevant.
4. **Handling NaNs**: Removed rows with missing values (`dropna()`) caused by rolling averages and shifts.

---

## 🛠️ Feature Engineering (Under the Hood)

Instead of feeding raw price numbers to the model, I engineered custom indicators over various horizons ($2, 5, 60, 250, 1000$ trading days):
* **Close Price Ratio**: Today's close price divided by the rolling average close over the last $N$ days. This tells the model if the price is historically high or low.
* **Trend Score**: The number of days the stock closed higher over the last $N$ days, shifted by 1 day (using `.shift(1)`) to ensure the model doesn't peak into the target it is trying to predict.

---

## 🌲 The Machine Learning Model

* **Algorithm**: `RandomForestClassifier`. I chose Random Forest because it is robust against overfitting, handles non-linear patterns, and is composed of simple decision trees that make it easy to understand how decisions are reached.
* **Retraining**: The FastAPI backend allows real-time tuning of hyper-parameters (like the number of trees `n_estimators` and node split requirements `min_samples_split`) to see how model precision reacts to settings.

---

## 🔄 Rolling-Window Backtesting (Preventing Leakage)

If you randomly split stock data, your model will train on data from 2024 to predict prices in 2023, which is impossible in the real world. 
To validate it properly, I wrote a chronological backtesting script:
* It trains on the first $2,500$ days (approx. 10 years).
* It predicts the next $250$ days (approx. 1 year).
* It then rolls forward: adding the predicted year to the training set, training again, and predicting the following year.
* This ensures the model *only* predicts the future using past data.

---

## 📊 Measuring Success (Model vs. Baseline)
* **Model Precision**: Out of all the days the model predicted the stock would go up (Bullish), how many times did it actually go up?
* **Baseline (Buy & Hold)**: The percentage of days the market naturally went up over the same period.
* **The Goal**: Beat the baseline! If the market goes up $54\%$ of the time, and our model has a precision of $58\%$, it has successfully extracted a predictive signal.

---

## 📁 Repository Structure

```
├── backend/                       # Python FastAPI backend
│   ├── routes/                    # API Endpoints (Predict & Stock info)
│   ├── services/                  # Business Logic (ML pipeline & Stock fetches)
│   ├── config.py                  # CACHE & Session settings
│   ├── main.py                    # Server initiation
│   └── models.py                  # Pydantic schemas
│
├── frontend/                      # Web Client (Vanilla HTML/CSS/JS)
│   ├── app.js                     # Chart.js rendering & API calls
│   ├── index.html                 # UI structure (restructured to premium bands)
│   └── style.css                  # Revolut-style theme custom properties & shapes
│
├── notebooks/                     # Interactive Notebook sandbox where I started
│   └── Stock_Market_Predcition.ipynb
│
├── main.py                        # Root launcher script
├── requirements.txt               # Required Python packages
└── .gitignore                     # Git filter for caches & temp files
```

---

## 🚀 Run it Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the local server:
   ```bash
   python main.py
   ```
3. Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

---

## 👔 Corporate Humour Disclaimer
> [!IMPORTANT]
> **Legal Notice**: If this model makes a prediction and you lose money, please note that we are legally protected by our disclaimer. If you do make money, please schedule a meeting with the development team (which could have been an email) to discuss profit-sharing models.
