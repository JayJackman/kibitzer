"""FastAPI application entry point.

Run with:  pdm run uvicorn bridge.api.main:app --reload --port 8000

The `lifespan` context manager runs setup code (create database tables)
when the server starts, before any requests are handled.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bridge.logging_config import setup_logging

from .analyze.router import router as analyze_router
from .auth.router import router as auth_router
from .config import settings
from .db import create_tables
from .practice.router import router as practice_router

logger = logging.getLogger(__name__)

# Path to the built frontend assets. In the Docker image, the Dockerfile
# copies the Vite build output into this directory. During development,
# this directory won't exist (the Vite dev server handles the frontend
# instead), so we check for it before mounting.
#
# We resolve relative to the current working directory (where uvicorn is
# launched from), which is /app in Docker and the project root in dev.
_STATIC_DIR = Path.cwd() / "static"


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


# ---------------------------------------------------------------------------
# CORS middleware -- only needed during development
# ---------------------------------------------------------------------------
# In development, the frontend runs on a different origin (Vite dev server
# at port 5173) than the API (port 8000). Browsers block cross-origin
# requests by default (the "same-origin policy"), so we need CORS headers
# to allow them.
#
# In production, the Dockerfile builds the frontend into static files and
# FastAPI serves them directly -- everything is the same origin, so no
# CORS is needed. When cors_origins is empty, we skip the middleware
# entirely to avoid unnecessary processing.
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # allow_credentials=True is required for cookies to be sent
        # cross-origin. Without it, the browser won't include the
        # auth cookies in API requests from the Vite dev server.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount the auth router (register, login, logout, refresh, me)
app.include_router(auth_router)

# Mount the practice router (create, state, bid, advise, redeal)
app.include_router(practice_router)

# Mount the analyze router (bid analysis, auction analysis, all-bids batch)
app.include_router(analyze_router)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
# A lightweight endpoint that returns 200 OK when the server is running.
# Used by:
#   - Docker HEALTHCHECK to monitor container health
#   - Load balancers to decide if this instance can receive traffic
#   - Monitoring tools to detect outages
#   - Deployment systems to know when a new version is ready
#
# Keep it simple -- no database checks, no external dependencies. If the
# Python process is alive and can handle HTTP, it's "healthy". More
# sophisticated checks (database connectivity, etc.) can be added later
# as separate endpoints if needed.
@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Return 200 OK if the server is alive."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve the frontend (production only)
# ---------------------------------------------------------------------------
# In production, the built React app lives in the "static" directory.
# We need to serve two things:
#   1. Static assets (JS, CSS, images) -- files in static/assets/ with
#      content-hashed filenames (e.g. index-B5gpXRns.js)
#   2. The SPA (Single Page Application) shell -- index.html
#
# The SPA catch-all is the trickiest part: React Router handles client-side
# routing, so URLs like /practice/abc123 don't correspond to real files on
# disk. When the browser requests /practice/abc123, we need to return
# index.html and let React Router figure out what to render. But we also
# need /api/* routes to still reach FastAPI. The solution:
#   - API routes are registered first (above), so they take priority
#   - Static assets are mounted at /assets (exact file matches)
#   - Everything else falls through to the catch-all and gets index.html
#
# This block only runs if the static directory exists. During development,
# it doesn't -- the Vite dev server handles the frontend on port 5173.
if (_STATIC_DIR / "index.html").exists():
    # Mount the assets directory. StaticFiles serves files directly --
    # when the browser requests /assets/index-B5gpXRns.js, it returns
    # the file from static/assets/index-B5gpXRns.js.
    app.mount(
        "/assets",
        StaticFiles(directory=str(_STATIC_DIR / "assets")),
        name="static-assets",
    )

    # SPA catch-all: any route not matched by the API or /assets returns
    # index.html. React Router (running in the browser) then reads the URL
    # and renders the correct page.
    @app.get("/{path:path}")
    async def spa_catch_all(path: str) -> FileResponse:
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        return FileResponse(str(_STATIC_DIR / "index.html"))
