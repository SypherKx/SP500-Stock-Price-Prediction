import uvicorn
from fastapi.staticfiles import StaticFiles
from backend.main import app

# Mount static files for the frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    print("Starting S&P 500 Stock Price Prediction Platform server...")
    print("Access the dashboard at: http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
