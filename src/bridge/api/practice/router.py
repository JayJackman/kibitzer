"""Practice session API endpoints.

Fifteen endpoints for the practice workflow:
- POST   /api/practice              Create a new session
- GET    /api/practice/join/{code}  Look up session by join code
- GET    /api/practice/{id}         Get current session state
- POST   /api/practice/{id}/bid     Place a bid
- GET    /api/practice/{id}/advise  Get engine advice
- POST   /api/practice/{id}/redeal  Deal new hands / reset (helper mode)
- POST   /api/practice/{id}/undo    Undo last round of bids
- POST   /api/practice/{id}/reset   Reset auction to initial state
- POST   /api/practice/{id}/hand    Set hand for a seat (helper mode only)
- GET    /api/practice/{id}/info    Lightweight session info (for join UI)
- POST   /api/practice/{id}/join    Join a session at a specific seat
- POST   /api/practice/{id}/leave   Leave a session
- POST   /api/practice/{id}/scoring/entry       Add/update/insert a scoring entry
- DELETE /api/practice/{id}/scoring/entry/{eid}  Remove a scoring entry
- POST   /api/practice/{id}/scoring/new-rubber   Start a new rubber
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from bridge.api.auth.models import User
from bridge.api.deps import get_current_user
from bridge.model.auction import IllegalBidError, Vulnerability
from bridge.model.card import Suit
from bridge.model.hand import Hand
from bridge.scoring.rubber import RubberTracker

from .schemas import (
    AdviceResponse,
    BidFeedbackResponse,
    CreatePracticeRequest,
    CreatePracticeResponse,
    JoinSessionRequest,
    PlaceBidRequest,
    PracticeStateResponse,
    RedealRequest,
    RubberStateResponse,
    ScoringEntryRequest,
    SessionInfoResponse,
    SetHandRequest,
    serialize_practice_state,
    serialize_rubber_state,
    serialize_session_info,
)
from .session import (
    AlreadySeatedError,
    AuctionCompleteError,
    DuplicateCardError,
    HandNotSetError,
    HelperModeOnlyError,
    NoBidsToUndoError,
    NotYourTurnError,
    PlayerNotFoundError,
    PracticeSession,
    SeatOccupiedError,
    SessionMode,
)
from .state import create_session, get_session, get_session_by_code

router = APIRouter(prefix="/api/practice", tags=["practice"])


# ── Dependencies ─────────────────────────────────────────────────


def _resolve_session(session_id: str) -> PracticeSession:
    """Resolve a session_id path parameter to a PracticeSession.

    Raises 404 if the session doesn't exist. Used as a FastAPI
    dependency so individual endpoints don't repeat this check.
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


def _require_seated(
    session: PracticeSession = Depends(_resolve_session),
    user: User = Depends(get_current_user),
) -> PracticeSession:
    """Like ``_resolve_session``, but also verifies the user is seated.

    Raises 403 if the user is not seated at this session. Use this
    instead of ``_resolve_session`` for endpoints that require a
    seated player (bid, advise, redeal, undo, reset, etc.).

    FastAPI caches dependency results per request, so ``_resolve_session``
    and ``get_current_user`` are not called twice when an endpoint also
    depends on them directly.
    """
    try:
        session.seat_for(user.id)
    except PlayerNotFoundError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You are not seated at this session",
        ) from None
    return session


# ── Routes with fixed path segments must come before /{session_id} ──
# Otherwise FastAPI would match "join" as a session_id.


@router.post(
    "",
    response_model=CreatePracticeResponse,
    status_code=201,
)
def create(
    body: CreatePracticeRequest,
    user: User = Depends(get_current_user),
) -> CreatePracticeResponse:
    """Create a new practice session.

    Practice mode: deals hands and runs computer bids until the human's turn.
    Helper mode: starts with empty hands; dealer and vulnerability can be
    specified in the request body.
    """
    vuln = Vulnerability.from_str(body.vulnerability) if body.vulnerability else None
    session = create_session(
        user.id,
        body.seat,
        mode=body.mode,
        username=user.username,
        dealer=body.dealer,
        vulnerability=vuln,
    )
    return CreatePracticeResponse(id=session.id, join_code=session.join_code)


@router.get(
    "/join/{code}",
    response_model=SessionInfoResponse,
)
def lookup_by_code(
    code: str,
    user: User = Depends(get_current_user),
) -> SessionInfoResponse:
    """Look up a session by its 6-character join code.

    Returns session info so the frontend can redirect to the join flow.
    """
    session = get_session_by_code(code)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No session found for that code")
    return serialize_session_info(session)


# ── Session-specific routes (use {session_id} path parameter) ────────


@router.get(
    "/{session_id}",
    response_model=PracticeStateResponse,
)
def get_state(
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> PracticeStateResponse:
    """Get the current session state (hand, auction, legal bids, etc.).

    Only shows the requesting user's hand. All hands are revealed
    once the auction is complete.
    """
    return serialize_practice_state(session.get_state(user.id))


@router.post(
    "/{session_id}/bid",
    response_model=BidFeedbackResponse,
)
def place_bid(
    body: PlaceBidRequest,
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> BidFeedbackResponse:
    """Place a bid and get feedback (matched engine or not).

    In helper mode, ``for_seat`` enables proxy bidding: a seated player
    can bid on behalf of an unoccupied seat.

    After the bid is placed, computer seats bid automatically (practice
    mode only). The frontend re-runs the loader to get the updated state.
    """
    try:
        result = session.place_bid(user.id, body.bid, for_seat=body.for_seat)
    except NotYourTurnError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "It is not your turn to bid",
        ) from None
    except AuctionCompleteError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The auction is already complete",
        ) from None
    except HelperModeOnlyError as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            str(e),
        ) from None
    except IllegalBidError as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            str(e),
        ) from None
    return BidFeedbackResponse.model_validate(result)


@router.get(
    "/{session_id}/advise",
    response_model=AdviceResponse,
)
def advise(
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> AdviceResponse:
    """Get the engine's bid recommendation for the current position.

    Returns the recommended bid, alternatives considered, and
    the full thought process (condition traces for each rule).
    In helper mode, the hand must be entered first via POST /{id}/hand.
    """
    try:
        advice = session.get_advice(user.id)
    except HandNotSetError as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            str(e),
        ) from None
    return AdviceResponse.model_validate(advice)


@router.post(
    "/{session_id}/redeal",
    status_code=200,
)
def redeal(
    body: RedealRequest | None = None,
    session: PracticeSession = Depends(_require_seated),
) -> dict[str, bool]:
    """Start a new hand.

    Practice mode: deals new random hands, rotates dealer, picks random vulnerability.
    Helper mode: clears all hands (re-enter via POST /{id}/hand),
    resets auction. Optionally specify ``dealer`` and ``vulnerability``
    in the request body (helper mode only; ignored in practice mode).
    """
    dealer = body.dealer if body else None
    vuln_str = body.vulnerability if body else None
    vuln = Vulnerability.from_str(vuln_str) if vuln_str else None
    session.redeal(dealer=dealer, vulnerability=vuln)
    return {"ok": True}


@router.post(
    "/{session_id}/undo",
    status_code=200,
)
def undo_bid(
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> dict[str, bool | int]:
    """Undo the last round of bids.

    Practice mode: removes the last human bid and all computer bids
    that followed it, restoring the auction to before the last bid.
    Helper mode: removes exactly one bid.
    """
    try:
        removed = session.undo_bid(user.id)
    except NoBidsToUndoError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No bids to undo",
        ) from None
    return {"ok": True, "removed": removed}


@router.post(
    "/{session_id}/reset",
    status_code=200,
)
def reset_auction(
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    """Reset the auction to its initial state.

    Removes all human-placed bids (and their computer follow-ups).
    Keeps hands, dealer, vulnerability, and initial computer bids intact.
    """
    session.reset_auction(user.id)
    return {"ok": True}


@router.post(
    "/{session_id}/hand",
    status_code=200,
)
def set_hand(
    body: SetHandRequest,
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    """Set the hand for a seat (helper mode only).

    Accepts a hand in PBN format (e.g. 'AKJ52.KQ3.84.A73' for
    S.H.D.C). Any seated player can set any seat's hand.
    Validates 13 cards, no internal duplicates, and no cards
    duplicated across seats.
    """
    try:
        hand = Hand.from_pbn(body.hand_pbn)
    except ValueError as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Invalid PBN hand: {e}",
        ) from None
    try:
        session.set_hand(user.id, body.seat, hand)
    except HelperModeOnlyError as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            str(e),
        ) from None
    except DuplicateCardError as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            str(e),
        ) from None
    return {"ok": True}


@router.get(
    "/{session_id}/info",
    response_model=SessionInfoResponse,
)
def get_info(
    session: PracticeSession = Depends(_resolve_session),
    user: User = Depends(get_current_user),
) -> SessionInfoResponse:
    """Lightweight session info for the join UI.

    Returns mode, join code, player names, and available seats.
    Accessible to any authenticated user (not just seated players).
    """
    return serialize_session_info(session)


@router.post(
    "/{session_id}/join",
    status_code=200,
)
def join_session(
    body: JoinSessionRequest,
    session: PracticeSession = Depends(_resolve_session),
    user: User = Depends(get_current_user),
) -> SessionInfoResponse:
    """Join a session at a specific seat.

    Returns updated session info after joining.
    """
    try:
        session.join(user.id, body.seat, username=user.username)
    except SeatOccupiedError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Seat {body.seat} is already occupied",
        ) from None
    except AlreadySeatedError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "You are already seated at this session",
        ) from None
    return serialize_session_info(session)


@router.post(
    "/{session_id}/leave",
    status_code=200,
)
def leave_session(
    session: PracticeSession = Depends(_require_seated),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    """Leave a session (seat reverts to computer control)."""
    session.leave(user.id)
    return {"ok": True}


# ── Scoring endpoints (helper mode only) ──────────────────────────


def _ensure_rubber(session: PracticeSession) -> RubberTracker:
    """Lazy-initialize the rubber tracker on first scoring use."""
    if session.rubber is None:
        if session.mode != SessionMode.HELPER:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Scoring is only available in helper mode",
            )
        session.rubber = RubberTracker()
    return session.rubber


@router.post(
    "/{session_id}/scoring/entry",
    response_model=RubberStateResponse,
)
def scoring_entry(
    body: ScoringEntryRequest,
    session: PracticeSession = Depends(_require_seated),
) -> RubberStateResponse:
    """Add, update, or insert a scoring entry.

    - If ``entry_id`` is set, updates that entry.
    - If ``position`` is set (without ``entry_id``), inserts at that index.
    - Otherwise, appends a new manual entry at the end.
    """
    rubber = _ensure_rubber(session)
    suit = Suit.from_letter(body.suit) if body.suit != "NT" else Suit.NOTRUMP

    if body.entry_id is not None:
        # Update existing entry.
        try:
            rubber.update_entry(
                body.entry_id,
                contract_level=body.level,
                contract_suit=suit,
                declarer=body.declarer,
                doubled=body.doubled,
                redoubled=body.redoubled,
                tricks_taken=body.tricks_taken,
            )
        except KeyError:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"No scoring entry with id {body.entry_id}",
            ) from None
    else:
        # Add new entry (at position or appended).
        rubber.add_entry(
            contract_level=body.level,
            contract_suit=suit,
            declarer=body.declarer,
            doubled=body.doubled,
            redoubled=body.redoubled,
            tricks_taken=body.tricks_taken,
            position=body.position,
        )

    return serialize_rubber_state(rubber.get_state())


@router.delete(
    "/{session_id}/scoring/entry/{entry_id}",
    response_model=RubberStateResponse,
)
def scoring_delete_entry(
    entry_id: int,
    session: PracticeSession = Depends(_require_seated),
) -> RubberStateResponse:
    """Remove a scoring entry by id."""
    rubber = _ensure_rubber(session)
    try:
        rubber.remove_entry(entry_id)
    except KeyError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"No scoring entry with id {entry_id}",
        ) from None
    return serialize_rubber_state(rubber.get_state())


@router.post(
    "/{session_id}/scoring/new-rubber",
    response_model=RubberStateResponse,
)
def scoring_new_rubber(
    session: PracticeSession = Depends(_require_seated),
) -> RubberStateResponse:
    """Start a new rubber (resets all scoring state)."""
    rubber = _ensure_rubber(session)
    rubber.new_rubber()
    return serialize_rubber_state(rubber.get_state())
