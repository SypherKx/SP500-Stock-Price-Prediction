from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.stock import router as stock_router
from backend.routes.predict import router as predict_router
from backend.services.stock_service import load_sp500_list

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Fetching S&P 500 list at startup...")
    load_sp500_list()
    yield

# Initialize FastAPI application
app = FastAPI(title="S&P 500 Stock Price Prediction API", lifespan=lifespan)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stock_router)
app.include_router(predict_router)
