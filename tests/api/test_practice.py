"""Integration tests for the practice API endpoints (via TestClient)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from bridge.api.db import Base, get_db
from bridge.api.main import app
from bridge.api.practice.state import clear_all


@pytest.fixture(autouse=True)
def _clear_sessions() -> None:
    """Reset the in-memory session store between tests."""
    clear_all()


@pytest.fixture()
def db() -> Session:  # type: ignore[misc]
    """Fresh in-memory SQLite database for each test."""
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
    """TestClient wired to the test database."""

    def _override_get_db() -> Session:  # type: ignore[misc]
        return db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c  # type: ignore[misc]
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient) -> None:
    """Register a user so the client has auth cookies."""
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "secret123"},
    )


def _create_session(client: TestClient, seat: str = "S") -> str:
    """Create a practice session and return its ID."""
    resp = client.post("/api/practice", json={"seat": seat})
    assert resp.status_code == 201
    return resp.json()["id"]


# ── Create session ────────────────────────────────────────────


class TestCreateSession:
    def test_create_returns_id(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = _create_session(client)
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_create_unauthenticated(self, client: TestClient) -> None:
        resp = client.post("/api/practice", json={"seat": "S"})
        assert resp.status_code == 401

    def test_create_invalid_seat(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.post("/api/practice", json={"seat": "X"})
        assert resp.status_code == 422


# ── Get state ─────────────────────────────────────────────────


class TestGetState:
    def test_returns_full_state(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = _create_session(client)

        resp = client.get(f"/api/practice/{session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == session_id
        assert data["your_seat"] == "S"
        assert "spades" in data["hand"]
        assert "hcp" in data["hand_evaluation"]
        assert "dealer" in data["auction"]
        assert isinstance(data["legal_bids"], list)
        assert isinstance(data["is_my_turn"], bool)
        assert data["hand_number"] == 1

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.get("/api/practice/nonexistent")
        assert resp.status_code == 404

    def test_wrong_user(self, client: TestClient) -> None:
        """A different user can't access someone else's session."""
        _register_and_login(client)
        session_id = _create_session(client)

        # Register a second user (replaces cookies).
        client.post(
            "/api/auth/register",
            json={"username": "other", "password": "secret123"},
        )
        resp = client.get(f"/api/practice/{session_id}")
        assert resp.status_code == 403


# ── Place bid ─────────────────────────────────────────────────


class TestPlaceBid:
    def test_valid_bid(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = _create_session(client)

        # Get state to find a legal bid.
        state = client.get(f"/api/practice/{session_id}").json()
        assert state["is_my_turn"] is True
        legal = state["legal_bids"]
        assert len(legal) > 0

        # Place the first legal bid.
        resp = client.post(
            f"/api/practice/{session_id}/bid",
            json={"bid": legal[0]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matched_engine" in data
        assert "engine_bid" in data
        assert "engine_explanation" in data

    def test_illegal_bid(self, client: TestClient) -> None:
        """Bidding below the current contract should fail."""
        _register_and_login(client)
        session_id = _create_session(client)

        # First make a high bid so lower bids become illegal.
        state = client.get(f"/api/practice/{session_id}").json()
        if state["is_my_turn"]:
            client.post(
                f"/api/practice/{session_id}/bid",
                json={"bid": "7NT"},
            )
            # Refresh state -- computer may have bid, need our turn again.
            state = client.get(f"/api/practice/{session_id}").json()
            if state["is_my_turn"]:
                resp = client.post(
                    f"/api/practice/{session_id}/bid",
                    json={"bid": "1C"},
                )
                assert resp.status_code == 422

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.post(
            "/api/practice/nonexistent/bid",
            json={"bid": "Pass"},
        )
        assert resp.status_code == 404


# ── Advise ────────────────────────────────────────────────────


class TestAdvise:
    def test_returns_advice(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = _create_session(client)

        resp = client.get(f"/api/practice/{session_id}/advise")
        assert resp.status_code == 200

        data = resp.json()
        assert "recommended" in data
        assert "bid" in data["recommended"]
        assert "rule_name" in data["recommended"]
        assert "explanation" in data["recommended"]
        assert "alternatives" in data
        assert "thought_process" in data
        assert "steps" in data["thought_process"]
        assert "phase" in data

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.get("/api/practice/nonexistent/advise")
        assert resp.status_code == 404


# ── Redeal ────────────────────────────────────────────────────


class TestRedeal:
    def test_redeal_rotates_dealer(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = _create_session(client)

        state1 = client.get(f"/api/practice/{session_id}").json()
        dealer1 = state1["auction"]["dealer"]

        resp = client.post(f"/api/practice/{session_id}/redeal")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

        state2 = client.get(f"/api/practice/{session_id}").json()
        dealer2 = state2["auction"]["dealer"]

        # Dealer should have rotated clockwise.
        rotation = {"N": "E", "E": "S", "S": "W", "W": "N"}
        assert dealer2 == rotation[dealer1]
        assert state2["hand_number"] == 2

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.post("/api/practice/nonexistent/redeal")
        assert resp.status_code == 404


# ── Full lifecycle ────────────────────────────────────────────


class TestFullLifecycle:
    def test_bid_through_completion(self, client: TestClient) -> None:
        """Create -> bid Pass repeatedly -> auction completes -> all hands visible."""
        _register_and_login(client)
        session_id = _create_session(client)

        # Bid Pass until the auction completes (max 100 iterations as safety).
        for _ in range(100):
            state = client.get(f"/api/practice/{session_id}").json()
            if state["auction"]["is_complete"]:
                break
            if not state["is_my_turn"]:
                # Shouldn't happen (computer bids automatically), but guard.
                break
            client.post(
                f"/api/practice/{session_id}/bid",
                json={"bid": "Pass"},
            )

        # Auction should be complete now.
        state = client.get(f"/api/practice/{session_id}").json()
        assert state["auction"]["is_complete"] is True
        assert state["is_my_turn"] is False
        assert state["legal_bids"] == []

        # All hands should be revealed.
        assert state["all_hands"] is not None
        assert len(state["all_hands"]) == 4
        for seat in ["N", "E", "S", "W"]:
            assert seat in state["all_hands"]
            hand = state["all_hands"][seat]
            total_cards = (
                len(hand["spades"])
                + len(hand["hearts"])
                + len(hand["diamonds"])
                + len(hand["clubs"])
            )
            assert total_cards == 13
