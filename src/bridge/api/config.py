"""Application configuration loaded from environment variables.

Uses pydantic-settings to read from environment variables with sensible
defaults for local development. In production, set SECRET_KEY to a real
random value (e.g. `openssl rand -hex 32`).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Secret key for signing JWT tokens. MUST be changed in production.
    secret_key: str = "dev-secret-change-in-production"

    # SQLite connection string. Relative paths are relative to the working
    # directory where uvicorn is launched.
    database_url: str = "sqlite:///./bridge.db"

    # How long an access token stays valid before the client must refresh.
    access_token_expire_minutes: int = 1440  # 24 hours

    # How long a refresh token stays valid. After this, the user must log in
    # again. 7 days means "7 days of total inactivity" before re-login.
    refresh_token_expire_days: int = 7

    # Origins allowed to make cross-origin requests. In development, the Vite
    # dev server runs on port 5173. In production (single-origin serving),
    # this list can be empty.
    cors_origins: list[str] = ["http://localhost:5173"]

    # Logging level for the bridge.* logger hierarchy. Set to DEBUG to see
    # engine rule evaluation traces; INFO (default) covers requests and
    # business events.
    log_level: str = "INFO"


# Singleton instance -- import this wherever config is needed.
settings = Settings()

# Cookie names used for auth tokens. Defined here so that the router
# (which sets/deletes them) and deps (which reads them) stay in sync.
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_PATH = "/api/auth/refresh"
