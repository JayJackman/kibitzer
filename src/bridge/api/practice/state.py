"""In-memory session store for practice sessions."""

from __future__ import annotations

from functools import cache

from bridge.model.auction import Seat
from bridge.service.advisor import BiddingAdvisor

from .session import PracticeSession, SessionMode

# Module-level dict: session_id -> PracticeSession.
# Lives only in server memory. Restarting the server clears all sessions.
_sessions: dict[str, PracticeSession] = {}

# Join code -> session_id index for quick lookup.
_join_codes: dict[str, str] = {}


@cache
def _get_advisor() -> BiddingAdvisor:
    """Lazily create and cache the shared BiddingAdvisor.

    Expensive to construct (builds the full SAYC rule registry), so we
    create once and reuse across all sessions.
    """
    return BiddingAdvisor()


def create_session(
    user_id: int,
    seat: Seat,
    *,
    mode: SessionMode = SessionMode.PRACTICE,
    username: str = "",
) -> PracticeSession:
    """Create a new practice session and store it."""
    session = PracticeSession(
        user_id, seat, _get_advisor(), mode=mode, username=username
    )
    _sessions[session.id] = session
    _join_codes[session.join_code] = session.id
    return session


def get_session(session_id: str) -> PracticeSession | None:
    """Look up a session by ID. Returns None if not found."""
    return _sessions.get(session_id)


def get_session_by_code(code: str) -> PracticeSession | None:
    """Look up a session by its 6-character join code."""
    session_id = _join_codes.get(code.upper())
    if session_id is None:
        return None
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """Remove a session from the store (idempotent)."""
    session = _sessions.pop(session_id, None)
    if session is not None:
        _join_codes.pop(session.join_code, None)


def clear_all() -> None:
    """Remove all sessions. Useful for testing."""
    _sessions.clear()
    _join_codes.clear()
