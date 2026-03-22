"""FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, predictions, search
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    logger.info("Starting Flight Price Agent API (env=%s)", settings.environment)
    yield
    logger.info("Shutting down Flight Price Agent API")
    # Close aggregator HTTP clients if they were initialised
    from app.api.dependencies import _get_aggregator_instance
    try:
        agg = _get_aggregator_instance()
        await agg.close()
    except Exception:
        pass


app = FastAPI(
    title="Flight Price Agent",
    description="AI-powered flight price agent that finds better deals than Skyscanner",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")


@app.get("/", summary="API root")
async def root() -> dict[str, Any]:
    """Return basic API info."""
    return {
        "message": "Flight Price Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "environment": settings.environment,
    }


@app.get("/health", summary="Health check")
async def health() -> dict[str, Any]:
    """Return API health status."""
    return {"status": "healthy", "environment": settings.environment}
