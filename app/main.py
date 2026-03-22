"""FastAPI application entrypoint."""
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

# Mount frontend static files
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/frontend", StaticFiles(directory=_frontend_dir), name="frontend")


@app.get("/", summary="Web UI")
async def root() -> FileResponse:
    """Serve the frontend SPA."""
    index_path = os.path.join(_frontend_dir, "index.html")
    return FileResponse(index_path)


@app.get("/health", summary="Health check")
async def health() -> dict[str, Any]:
    """Return API health status."""
    return {"status": "healthy", "environment": settings.environment}
