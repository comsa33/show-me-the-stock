"""
Stock Dashboard FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Stock Dashboard API",
    description="AI-powered stock analysis dashboard backend with ML predictions",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Stock Dashboard API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "stock-dashboard-backend",
        "version": "2.0.0"
    }

@app.get("/api/v1/stocks")
async def get_stocks():
    """Get stock list"""
    return {
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc.", "price": 150.00},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 2800.00},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 300.00}
        ]
    }

@app.get("/api/v1/market/status")
async def get_market_status():
    """Get market status"""
    return {
        "status": "open",
        "next_close": "16:00 EST",
        "timezone": "America/New_York"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)