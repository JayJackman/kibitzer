"""FastAPI application entry point.

Run with:  pdm run uvicorn bridge.api.main:app --reload --port 8000

The `lifespan` context manager runs setup code (create database tables)
when the server starts, before any requests are handled.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .config import settings
from .db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle for the FastAPI app.

    Startup: create database tables if they don't exist yet.
    Shutdown: nothing needed for now (SQLite handles cleanup).
    """
    create_tables()
    yield


app = FastAPI(title="Bridge Bidding Assistant", lifespan=lifespan)

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
