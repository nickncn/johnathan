"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_instruments,
    routes_llm,
    routes_pnl,
    routes_positions,
    routes_reports,
    routes_risk,
    routes_trades,
)
from app.core.config import get_settings
from app.db.session import engine
from app.ws.stream import router as ws_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    logger.info("Starting Risk Dashboard API")
    
    # Startup logic here
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        
    yield
    
    # Shutdown logic here
    logger.info("Shutting down Risk Dashboard API")


# Create FastAPI application
app = FastAPI(
    title="Risk Dashboard API",
    description="AI-Driven Risk Management Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "ok",
            "service": "risk-dashboard-api",
            "version": "0.1.0"
        }
    )


@app.get("/metrics")
async def metrics() -> JSONResponse:
    """Basic metrics endpoint."""
    # In production, integrate with Prometheus/monitoring system
    return JSONResponse(content={"requests_total": 0, "errors_total": 0})


# Include API routers
app.include_router(routes_instruments.router, prefix="/api", tags=["instruments"])
app.include_router(routes_trades.router, prefix="/api", tags=["trades"])
app.include_router(routes_positions.router, prefix="/api", tags=["positions"])
app.include_router(routes_pnl.router, prefix="/api", tags=["pnl"])
app.include_router(routes_risk.router, prefix="/api", tags=["risk"])
app.include_router(routes_reports.router, prefix="/api", tags=["reports"])
app.include_router(routes_llm.router, prefix="/api", tags=["llm"])

# Include WebSocket router
app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )