"""FastAPI application entry point.

Run with:  pdm run uvicorn bridge.api.main:app --reload --port 8000

The `lifespan` context manager runs setup code (create database tables)
when the server starts, before any requests are handled.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from bridge.logging_config import setup_logging

from .auth.router import router as auth_router
from .config import settings
from .db import create_tables
from .practice.router import router as practice_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle for the FastAPI app.

    Startup: configure logging, create database tables.
    Shutdown: nothing needed for now (SQLite handles cleanup).
    """
    setup_logging(settings.log_level)
    logger.info("Starting Bridge Bidding Assistant API")
    create_tables()
    yield


app = FastAPI(title="Bridge Bidding Assistant", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Log every HTTP request with method, path, status, and duration."""
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# CORS middleware allows the Vite dev server (port 5173) to call the API
# (port 8000). Without this, the browser blocks cross-origin requests.
# `allow_credentials=True` is required for cookies to be sent cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the auth router (register, login, logout, refresh, me)
app.include_router(auth_router)

# Mount the practice router (create, state, bid, advise, redeal)
app.include_router(practice_router)
