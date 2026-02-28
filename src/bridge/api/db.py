"""SQLAlchemy database setup.

Provides the engine, session factory, and declarative Base class used by
all SQLAlchemy models. The `create_tables` function is called once at
application startup (in the FastAPI lifespan) to ensure the schema exists.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# `connect_args` is needed for SQLite to allow usage from multiple threads
# (FastAPI handles requests concurrently). The `check_same_thread=False`
# flag is safe because SQLAlchemy's session management handles thread safety.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

# Each request gets its own session via the `get_db` dependency (see deps.py).
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models (User, etc.)."""


def create_tables() -> None:
    """Create all tables that don't exist yet. Called once at startup."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, ensuring it's closed after the request.

    Used as a FastAPI dependency:  db = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
