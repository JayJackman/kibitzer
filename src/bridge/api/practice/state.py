"""In-memory session store for practice sessions."""

from __future__ import annotations

from functools import cache

from bridge.model.auction import Seat
from bridge.service.advisor import BiddingAdvisor

from .session import PracticeSession

# Module-level dict: session_id -> PracticeSession.
# Lives only in server memory. Restarting the server clears all sessions.
_sessions: dict[str, PracticeSession] = {}


@cache
def _get_advisor() -> BiddingAdvisor:
    """Lazily create and cache the shared BiddingAdvisor.

    Expensive to construct (builds the full SAYC rule registry), so we
    create once and reuse across all sessions.
    """
    return BiddingAdvisor()


def create_session(user_id: int, seat: Seat) -> PracticeSession:
    """Create a new practice session and store it."""
    session = PracticeSession(user_id, seat, _get_advisor())
    _sessions[session.id] = session
    return session


def get_session(session_id: str) -> PracticeSession | None:
    """Look up a session by ID. Returns None if not found."""
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """Remove a session from the store (idempotent)."""
    _sessions.pop(session_id, None)


def clear_all() -> None:
    """Remove all sessions. Useful for testing."""
    _sessions.clear()
