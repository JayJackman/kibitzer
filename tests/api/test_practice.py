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


def _create_session(client: TestClient, seat: str = "S") -> tuple[str, str]:
    """Create a practice session and return (session_id, join_code)."""
    resp = client.post("/api/practice", json={"seat": seat})
    assert resp.status_code == 201
    data = resp.json()
    return data["id"], data["join_code"]


# ── Create session ────────────────────────────────────────────


class TestCreateSession:
    def test_create_returns_id_and_join_code(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, join_code = _create_session(client)
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert isinstance(join_code, str)
        assert len(join_code) == 6

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
        session_id, join_code = _create_session(client)

        resp = client.get(f"/api/practice/{session_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == session_id
        assert data["mode"] == "practice"
        assert data["join_code"] == join_code
        assert data["your_seat"] == "S"
        assert "spades" in data["hand"]
        assert "hcp" in data["hand_evaluation"]
        assert "dealer" in data["auction"]
        assert isinstance(data["legal_bids"], list)
        assert isinstance(data["is_my_turn"], bool)
        assert data["hand_number"] == 1
        assert isinstance(data["players"], dict)
        assert data["players"]["S"] is not None  # Human seat

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.get("/api/practice/nonexistent")
        assert resp.status_code == 404

    def test_wrong_user(self, client: TestClient) -> None:
        """A different user can't access someone else's session."""
        _register_and_login(client)
        session_id, _ = _create_session(client)

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
        session_id, _ = _create_session(client)

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
        session_id, _ = _create_session(client)

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
        session_id, _ = _create_session(client)

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
        session_id, _ = _create_session(client)

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
        session_id, _ = _create_session(client)

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


# ── Session info ─────────────────────────────────────────────


class TestGetInfo:
    def test_returns_session_info(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, join_code = _create_session(client)

        resp = client.get(f"/api/practice/{session_id}/info")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == session_id
        assert data["mode"] == "practice"
        assert data["join_code"] == join_code
        assert isinstance(data["players"], dict)
        assert isinstance(data["available_seats"], list)
        # South is occupied, 3 seats available.
        assert len(data["available_seats"]) == 3
        assert "S" not in data["available_seats"]

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.get("/api/practice/nonexistent/info")
        assert resp.status_code == 404

    def test_accessible_by_non_seated_user(self, client: TestClient) -> None:
        """Any authenticated user can view session info (not just seated players)."""
        _register_and_login(client)
        session_id, _ = _create_session(client)

        # Register a second user (replaces cookies).
        client.post(
            "/api/auth/register",
            json={"username": "other", "password": "secret123"},
        )
        resp = client.get(f"/api/practice/{session_id}/info")
        assert resp.status_code == 200


# ── Join session ─────────────────────────────────────────────


class TestJoinSession:
    def test_join_available_seat(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_session(client)

        # Register a second user.
        client.post(
            "/api/auth/register",
            json={"username": "player2", "password": "secret123"},
        )
        resp = client.post(
            f"/api/practice/{session_id}/join",
            json={"seat": "N"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "N" not in data["available_seats"]
        assert data["players"]["N"] == "player2"

    def test_join_occupied_seat(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_session(client)

        client.post(
            "/api/auth/register",
            json={"username": "player2", "password": "secret123"},
        )
        resp = client.post(
            f"/api/practice/{session_id}/join",
            json={"seat": "S"},  # Already occupied by creator.
        )
        assert resp.status_code == 409

    def test_join_already_seated(self, client: TestClient) -> None:
        """A user already in the session can't join another seat."""
        _register_and_login(client)
        session_id, _ = _create_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/join",
            json={"seat": "N"},
        )
        assert resp.status_code == 409

    def test_joined_user_can_get_state(self, client: TestClient) -> None:
        """After joining, the user can fetch session state."""
        _register_and_login(client)
        session_id, _ = _create_session(client)

        client.post(
            "/api/auth/register",
            json={"username": "player2", "password": "secret123"},
        )
        client.post(
            f"/api/practice/{session_id}/join",
            json={"seat": "N"},
        )
        resp = client.get(f"/api/practice/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["your_seat"] == "N"

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.post(
            "/api/practice/nonexistent/join",
            json={"seat": "N"},
        )
        assert resp.status_code == 404


# ── Leave session ────────────────────────────────────────────


class TestLeaveSession:
    def test_leave_reverts_to_computer(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_session(client)

        # Join as second user, then leave.
        client.post(
            "/api/auth/register",
            json={"username": "player2", "password": "secret123"},
        )
        client.post(
            f"/api/practice/{session_id}/join",
            json={"seat": "N"},
        )
        resp = client.post(f"/api/practice/{session_id}/leave")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

        # After leaving, can't get state anymore.
        resp = client.get(f"/api/practice/{session_id}")
        assert resp.status_code == 403

    def test_leave_not_seated(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_session(client)

        client.post(
            "/api/auth/register",
            json={"username": "player2", "password": "secret123"},
        )
        resp = client.post(f"/api/practice/{session_id}/leave")
        assert resp.status_code == 403

    def test_not_found(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.post("/api/practice/nonexistent/leave")
        assert resp.status_code == 404


# ── Lookup by code ───────────────────────────────────────────


class TestLookupByCode:
    def test_lookup_returns_session_info(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, join_code = _create_session(client)

        resp = client.get(f"/api/practice/join/{join_code}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == session_id
        assert data["join_code"] == join_code

    def test_lookup_case_insensitive(self, client: TestClient) -> None:
        _register_and_login(client)
        _, join_code = _create_session(client)

        resp = client.get(f"/api/practice/join/{join_code.lower()}")
        assert resp.status_code == 200

    def test_lookup_invalid_code(self, client: TestClient) -> None:
        _register_and_login(client)
        resp = client.get("/api/practice/join/ZZZZZZ")
        assert resp.status_code == 404


# ── Helper mode endpoints ────────────────────────────────────

# Valid non-overlapping test hands (from deal(rng=Random(42))).
_HAND_W = "T9873.643.KT3.T3"
_HAND_N = "KJ5.AKQT85.A9.92"
_HAND_E = "Q62.7.Q7542.K765"
_HAND_S = "A4.J92.J86.AQJ84"


def _create_helper_session(
    client: TestClient, seat: str = "S", dealer: str = "N", vuln: str = "NS"
) -> tuple[str, str]:
    """Create a helper-mode session and return (session_id, join_code)."""
    resp = client.post(
        "/api/practice",
        json={"seat": seat, "mode": "helper", "dealer": dealer, "vulnerability": vuln},
    )
    assert resp.status_code == 201
    data = resp.json()
    return data["id"], data["join_code"]


class TestCreateHelperSession:
    def test_create_helper(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, join_code = _create_helper_session(client)
        assert isinstance(session_id, str)
        assert len(join_code) == 6

    def test_helper_state_has_null_hand(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        resp = client.get(f"/api/practice/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "helper"
        assert data["hand"] is None
        assert data["hand_evaluation"] is None
        assert data["auction"]["dealer"] == "N"
        assert data["auction"]["vulnerability"] == "NS"

    def test_helper_no_computer_bids(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        data = client.get(f"/api/practice/{session_id}").json()
        assert data["auction"]["bids"] == []
        assert data["computer_bids"] == []


class TestSetHandEndpoint:
    def test_set_hand(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_S, "seat": "S"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

        # Verify hand appears in state.
        data = client.get(f"/api/practice/{session_id}").json()
        assert data["hand"] is not None
        assert data["hand_evaluation"] is not None
        assert data["hand_evaluation"]["hcp"] >= 0

    def test_set_hand_any_seat(self, client: TestClient) -> None:
        """Can set another seat's hand (not just your own)."""
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_N, "seat": "N"},
        )
        assert resp.status_code == 200

    def test_set_hand_invalid_pbn(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": "not-valid", "seat": "S"},
        )
        assert resp.status_code == 422

    def test_set_hand_duplicate_cards(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        # Set North's hand first.
        client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_N, "seat": "N"},
        )
        # Try to give South the same hand.
        resp = client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_N, "seat": "S"},
        )
        assert resp.status_code == 409

    def test_set_hand_practice_mode_rejected(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_S, "seat": "S"},
        )
        assert resp.status_code == 409

    def test_set_hand_not_seated(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        # Register second user.
        client.post(
            "/api/auth/register",
            json={"username": "other", "password": "secret123"},
        )
        resp = client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_S, "seat": "S"},
        )
        assert resp.status_code == 403


class TestProxyBidEndpoint:
    def _setup_helper_with_hands(self, client: TestClient) -> str:
        """Create helper session and set all 4 hands. Returns session_id."""
        session_id, _ = _create_helper_session(client)
        hands = [("N", _HAND_N), ("E", _HAND_E), ("S", _HAND_S), ("W", _HAND_W)]
        for seat, pbn in hands:
            resp = client.post(
                f"/api/practice/{session_id}/hand",
                json={"hand_pbn": pbn, "seat": seat},
            )
            assert resp.status_code == 200
        return session_id

    def test_proxy_bid(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = self._setup_helper_with_hands(client)

        # Dealer is North (unoccupied). South can proxy bid.
        state = client.get(f"/api/practice/{session_id}").json()
        assert state["can_proxy_bid"] is True
        assert state["proxy_seat"] == "N"

        resp = client.post(
            f"/api/practice/{session_id}/bid",
            json={"bid": "Pass", "for_seat": "N"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matched_engine" in data

    def test_proxy_bid_wrong_seat(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id = self._setup_helper_with_hands(client)

        # Dealer is North, trying to proxy for East (not current seat).
        resp = client.post(
            f"/api/practice/{session_id}/bid",
            json={"bid": "Pass", "for_seat": "E"},
        )
        assert resp.status_code == 409

    def test_proxy_not_allowed_in_practice(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/bid",
            json={"bid": "Pass", "for_seat": "N"},
        )
        assert resp.status_code == 409


class TestHelperAdviseEndpoint:
    def test_advise_without_hand_returns_409(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        resp = client.get(f"/api/practice/{session_id}/advise")
        assert resp.status_code == 409

    def test_advise_after_set_hand(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_S, "seat": "S"},
        )
        resp = client.get(f"/api/practice/{session_id}/advise")
        assert resp.status_code == 200
        assert "recommended" in resp.json()


class TestHelperRedealEndpoint:
    def test_redeal_clears_hands(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        # Set a hand, then redeal.
        client.post(
            f"/api/practice/{session_id}/hand",
            json={"hand_pbn": _HAND_S, "seat": "S"},
        )
        resp = client.post(f"/api/practice/{session_id}/redeal")
        assert resp.status_code == 200

        data = client.get(f"/api/practice/{session_id}").json()
        assert data["hand"] is None
        assert data["hand_number"] == 2

    def test_redeal_with_overrides(self, client: TestClient) -> None:
        _register_and_login(client)
        session_id, _ = _create_helper_session(client)

        resp = client.post(
            f"/api/practice/{session_id}/redeal",
            json={"dealer": "W", "vulnerability": "Both"},
        )
        assert resp.status_code == 200

        data = client.get(f"/api/practice/{session_id}").json()
        assert data["auction"]["dealer"] == "W"
        assert data["auction"]["vulnerability"] == "Both"


class TestHelperLifecycleEndpoint:
    def test_full_helper_flow(self, client: TestClient) -> None:
        """Create -> set hands -> bid (with proxy) -> advise -> redeal."""
        _register_and_login(client)
        session_id, _ = _create_helper_session(client, dealer="N")

        # Set all four hands.
        hands = [("N", _HAND_N), ("E", _HAND_E), ("S", _HAND_S), ("W", _HAND_W)]
        for seat, pbn in hands:
            resp = client.post(
                f"/api/practice/{session_id}/hand",
                json={"hand_pbn": pbn, "seat": seat},
            )
            assert resp.status_code == 200

        # Get advice (should work now).
        resp = client.get(f"/api/practice/{session_id}/advise")
        assert resp.status_code == 200

        # Bid all passes: proxy for N, E, W; direct for S.
        for _ in range(4):  # 4 consecutive passes end the auction.
            state = client.get(f"/api/practice/{session_id}").json()
            if state["auction"]["is_complete"]:
                break
            current = state["auction"]["current_seat"]
            if current == "S":
                resp = client.post(
                    f"/api/practice/{session_id}/bid",
                    json={"bid": "Pass"},
                )
            else:
                resp = client.post(
                    f"/api/practice/{session_id}/bid",
                    json={"bid": "Pass", "for_seat": current},
                )
            assert resp.status_code == 200

        # Verify auction completed.
        state = client.get(f"/api/practice/{session_id}").json()
        assert state["auction"]["is_complete"] is True

        # Redeal.
        resp = client.post(f"/api/practice/{session_id}/redeal")
        assert resp.status_code == 200
        state = client.get(f"/api/practice/{session_id}").json()
        assert state["hand_number"] == 2
        assert state["hand"] is None
