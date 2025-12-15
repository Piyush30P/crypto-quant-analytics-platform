"""
Main FastAPI application for Crypto Analytics Platform
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.api.routes import router
from backend.api.alert_routes import router as alert_router
from backend.alerts.monitor import start_alert_monitoring, stop_alert_monitoring
from config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="Crypto Analytics Platform API",
    description="""
    Professional cryptocurrency analytics API for quantitative trading

    ## Features

    * **Basic Statistics**: Comprehensive price, volume, and volatility metrics
    * **Pair Analysis**: Correlation, cointegration, and trading signals
    * **OHLC Data**: Historical candlestick data with VWAP
    * **Tick Data**: Raw tick-level price data
    * **Trading Signals**: Z-score based mean reversion signals

    ## Analytics Capabilities

    * Pearson & Spearman correlation
    * Hedge ratio calculation (OLS regression)
    * Cointegration testing (ADF test)
    * Spread and Z-score analysis
    * VWAP calculation
    * Volatility metrics (annualized)
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(alert_router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "Crypto Analytics Platform API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "health": "GET /api/health",
            "statistics": "GET /api/stats/{symbol}",
            "ohlc": "GET /api/ohlc/{symbol}",
            "ticks": "GET /api/ticks/{symbol}",
            "pair_analysis": "POST /api/pairs/analyze",
            "symbols": "GET /api/symbols",
            "timeframes": "GET /api/timeframes/{symbol}",
            "alerts": {
                "create_rule": "POST /api/alerts/rules",
                "get_rules": "GET /api/alerts/rules",
                "get_history": "GET /api/alerts/history",
                "monitor_status": "GET /api/alerts/monitor/status",
                "manual_check": "POST /api/alerts/monitor/check"
            }
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    logger.info("=" * 60)
    logger.info("Crypto Analytics Platform API")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info("=" * 60)
    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("=" * 60)

    # Start alert monitoring service
    try:
        start_alert_monitoring(check_interval_seconds=60)
        logger.info("Alert monitoring service started (check interval: 60s)")
    except Exception as e:
        logger.warning(f"Could not start alert monitoring: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown
    """
    logger.info("Shutting down Crypto Analytics Platform API")

    # Stop alert monitoring service
    try:
        stop_alert_monitoring()
        logger.info("Alert monitoring service stopped")
    except Exception as e:
        logger.warning(f"Could not stop alert monitoring: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level="info"
    )
