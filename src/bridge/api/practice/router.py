"""Practice session API endpoints.

Five endpoints for the solo practice workflow:
- POST   /api/practice              Create a new session
- GET    /api/practice/{id}         Get current session state
- POST   /api/practice/{id}/bid     Place a bid
- GET    /api/practice/{id}/advise  Get engine advice
- POST   /api/practice/{id}/redeal  Deal new hands
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from bridge.api.auth.models import User
from bridge.api.deps import get_current_user
from bridge.model.auction import IllegalBidError, Seat

from .schemas import (
    AdviceResponse,
    BidFeedbackResponse,
    CreatePracticeRequest,
    CreatePracticeResponse,
    PlaceBidRequest,
    PracticeStateResponse,
    serialize_practice_state,
)
from .session import (
    AuctionCompleteError,
    NotYourTurnError,
    PlayerNotFoundError,
)
from .state import create_session, get_session

router = APIRouter(prefix="/api/practice", tags=["practice"])


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

    Deals hands, runs computer bids until it's the human's turn,
    and returns the session ID. The frontend redirects to
    /practice/{id} to fetch the full state.
    """
    seat = Seat.from_str(body.seat)
    session = create_session(user.id, seat)
    return CreatePracticeResponse(id=session.id)


@router.get(
    "/{session_id}",
    response_model=PracticeStateResponse,
)
def get_state(
    session_id: str,
    user: User = Depends(get_current_user),
) -> PracticeStateResponse:
    """Get the current session state (hand, auction, legal bids, etc.).

    Only shows the requesting user's hand. All hands are revealed
    once the auction is complete.
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    try:
        state = session.get_state(user.id)
    except PlayerNotFoundError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You are not seated at this session",
        ) from None
    return serialize_practice_state(state)


@router.post(
    "/{session_id}/bid",
    response_model=BidFeedbackResponse,
)
def place_bid(
    session_id: str,
    body: PlaceBidRequest,
    user: User = Depends(get_current_user),
) -> BidFeedbackResponse:
    """Place a bid and get feedback (matched engine or not).

    After the bid is placed, computer seats bid automatically.
    The frontend re-runs the loader to get the updated state.
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    try:
        result = session.place_bid(user.id, body.bid)
    except PlayerNotFoundError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You are not seated at this session",
        ) from None
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
    session_id: str,
    user: User = Depends(get_current_user),
) -> AdviceResponse:
    """Get the engine's bid recommendation for the current position.

    Returns the recommended bid, alternatives considered, and
    the full thought process (condition traces for each rule).
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    try:
        advice = session.get_advice(user.id)
    except PlayerNotFoundError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You are not seated at this session",
        ) from None
    return AdviceResponse.model_validate(advice)


@router.post(
    "/{session_id}/redeal",
    status_code=200,
)
def redeal(
    session_id: str,
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    """Deal new hands, rotate dealer, pick random vulnerability.

    The frontend revalidates the loader to get the new state.
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    # Verify the user is seated (only the host can redeal for now).
    try:
        session.seat_for(user.id)
    except PlayerNotFoundError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You are not seated at this session",
        ) from None
    session.redeal()
    return {"ok": True}
