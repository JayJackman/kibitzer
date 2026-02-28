"""Tests for the auth API endpoints (register, login, logout, refresh, me)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from bridge.api.auth.models import User
from bridge.api.db import Base, get_db
from bridge.api.main import app


@pytest.fixture()
def db() -> Session:  # type: ignore[misc]
    """Create a fresh in-memory SQLite database for each test.

    Uses StaticPool so the same in-memory database is shared across
    the test (in-memory SQLite databases are per-connection by default).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """TestClient wired to the in-memory test database.

    Overrides the `get_db` dependency so all requests hit the test DB
    instead of the real SQLite file.
    """

    def _override_get_db() -> Session:  # type: ignore[misc]
        return db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c  # type: ignore[misc]
    app.dependency_overrides.clear()


# -- Registration --


def test_register_success(client: TestClient, db: Session) -> None:
    """Register a new user -- should return 201 with user info and set cookies."""
    resp = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert "id" in data

    # Should have set auth cookies
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies

    # User should exist in the database
    user = db.query(User).filter(User.username == "alice").first()
    assert user is not None
    assert user.username == "alice"


def test_register_duplicate_username(client: TestClient) -> None:
    """Registering with an existing username should return 409."""
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )
    resp = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "different"},
    )
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"]


def test_register_short_password(client: TestClient) -> None:
    """Password must be at least 6 characters."""
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "12345"},
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_register_empty_username(client: TestClient) -> None:
    """Username must not be empty."""
    resp = client.post(
        "/api/auth/register",
        json={"username": "", "password": "secret123"},
    )
    assert resp.status_code == 422


# -- Login --


def test_login_success(client: TestClient) -> None:
    """Login with correct credentials -- should return user info and set cookies."""
    # First register
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )

    # Then login
    resp = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"
    assert "access_token" in resp.cookies


def test_login_wrong_password(client: TestClient) -> None:
    """Login with wrong password should return 401."""
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "wrongpass"},
    )
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]


def test_login_nonexistent_user(client: TestClient) -> None:
    """Login with a username that doesn't exist should return 401."""
    resp = client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "secret123"},
    )
    assert resp.status_code == 401


# -- Me --


def test_me_authenticated(client: TestClient) -> None:
    """GET /me with a valid cookie should return user info."""
    # Register (auto-login sets cookies on the client)
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_me_unauthenticated(client: TestClient) -> None:
    """GET /me without cookies should return 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


# -- Logout --


def test_logout(client: TestClient) -> None:
    """Logout should clear cookies, and /me should then return 401."""
    # Register + auto-login
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )

    # Verify we're logged in
    assert client.get("/api/auth/me").status_code == 200

    # Logout
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"

    # Should no longer be authenticated
    assert client.get("/api/auth/me").status_code == 401


# -- Refresh --


def test_refresh_token(client: TestClient) -> None:
    """Refresh should issue a new access token using the refresh cookie."""
    # Register (sets both cookies)
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )

    # Save the original access token
    original_access = client.cookies.get("access_token")
    assert original_access is not None

    # Call refresh
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Token refreshed"

    # The access token cookie should have been updated
    # (We can verify /me still works with the new token)
    assert client.get("/api/auth/me").status_code == 200


def test_refresh_without_token(client: TestClient) -> None:
    """Refresh without a refresh token cookie should return 401."""
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401
