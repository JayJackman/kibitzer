"""Pydantic schemas for practice session request/response bodies.

Translates domain objects (frozen dataclasses, enums) into JSON-friendly
shapes for the API layer. Most response models use ``from_attributes=True``
to read directly from domain dataclasses, with ``Annotated`` types handling
enum-to-string conversions automatically -- no manual serialize function
needed for leaf-level models.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field

from bridge.model.auction import AuctionState
from bridge.model.hand import Hand

from .session import PracticeState

# ── Reusable annotated types ─────────────────────────────────────
# BeforeValidators run during model_validate(), converting domain
# enums to plain strings so Pydantic models store str values.
# When the value is already a str (e.g. constructing from a dict),
# the validator passes it through unchanged.


def _seat_to_str(v: Any) -> str:
    return v if isinstance(v, str) else str(v)


def _bid_to_str(v: Any) -> str:
    return v if isinstance(v, str) else str(v)


def _suit_to_str(v: Any) -> str:
    return v if isinstance(v, str) else v.letter


SeatStr = Annotated[str, BeforeValidator(_seat_to_str)]
BidStr = Annotated[str, BeforeValidator(_bid_to_str)]
SuitStr = Annotated[str, BeforeValidator(_suit_to_str)]


# ── Request schemas ───────────────────────────────────────────────


class CreatePracticeRequest(BaseModel):
    """POST /api/practice request body."""

    seat: str = Field(
        description="Seat to occupy: N, E, S, or W",
        pattern=r"^[NESW]$",
    )


class PlaceBidRequest(BaseModel):
    """POST /api/practice/{id}/bid request body."""

    bid: str = Field(
        description="Bid string: e.g. '1S', 'Pass', 'X', 'XX'",
        min_length=1,
    )


# ── Response schemas ──────────────────────────────────────────────


class CreatePracticeResponse(BaseModel):
    """Response from creating a new practice session."""

    id: str


class HandResponse(BaseModel):
    """Cards grouped by suit, each as a list of rank strings."""

    spades: list[str]
    hearts: list[str]
    diamonds: list[str]
    clubs: list[str]


class HandEvalResponse(BaseModel):
    """Pre-computed hand metrics.

    Reads directly from a HandEvaluation dataclass; extra fields
    (sorted_shape, is_semi_balanced, longest_suit) are ignored.
    """

    hcp: int
    length_points: int
    total_points: int
    distribution_points: int
    controls: int
    quick_tricks: float
    losers: int
    shape: list[int]
    is_balanced: bool

    model_config = {"from_attributes": True}


class ContractResponse(BaseModel):
    """Final contract of a completed auction.

    SuitStr/SeatStr handle Suit->letter and Seat->letter conversion.
    """

    level: int
    suit: SuitStr
    declarer: SeatStr
    doubled: bool
    redoubled: bool
    passed_out: bool

    model_config = {"from_attributes": True}


class AuctionBidResponse(BaseModel):
    """A single bid in the auction history."""

    seat: str
    bid: str
    explanation: str | None = None
    matched_engine: bool | None = None


class AuctionResponse(BaseModel):
    """Full auction state."""

    dealer: str
    vulnerability: str
    bids: list[AuctionBidResponse]
    is_complete: bool
    current_seat: str | None
    contract: ContractResponse | None = None


class ComputerBidResponse(BaseModel):
    """A bid placed by a computer-controlled seat."""

    seat: SeatStr
    bid: BidStr
    explanation: str

    model_config = {"from_attributes": True}


class BidFeedbackResponse(BaseModel):
    """Feedback from placing a bid (did it match the engine?)."""

    matched_engine: bool
    engine_bid: str
    engine_explanation: str

    model_config = {"from_attributes": True}


class ConditionResponse(BaseModel):
    """A single condition evaluation result."""

    label: str
    detail: str
    passed: bool

    model_config = {"from_attributes": True}


class ThoughtStepResponse(BaseModel):
    """One rule evaluated during the thought process.

    The domain ThoughtStep stores conditions as ``condition_results``;
    validation_alias maps that attribute to the ``conditions`` field.
    """

    rule_name: str
    passed: bool
    bid: BidStr | None
    conditions: list[ConditionResponse] = Field(
        validation_alias="condition_results",
    )

    model_config = {"from_attributes": True}


class ThoughtProcessResponse(BaseModel):
    """Full trace of how the engine reached its decision."""

    steps: list[ThoughtStepResponse]

    model_config = {"from_attributes": True}


class RuleResultResponse(BaseModel):
    """A single rule's bid recommendation."""

    bid: BidStr
    rule_name: str
    explanation: str
    forcing: bool
    alerts: list[str]

    model_config = {"from_attributes": True}


class AdviceResponse(BaseModel):
    """Engine recommendation with thought process.

    Use ``AdviceResponse.model_validate(advice)`` to convert a
    BiddingAdvice dataclass; nested models handle their own
    from_attributes conversion recursively.
    """

    recommended: RuleResultResponse
    alternatives: list[RuleResultResponse]
    thought_process: ThoughtProcessResponse
    phase: str

    model_config = {"from_attributes": True}


class PracticeStateResponse(BaseModel):
    """Full session state for the practice page."""

    id: str
    your_seat: str
    hand: HandResponse
    hand_evaluation: HandEvalResponse
    auction: AuctionResponse
    computer_bids: list[ComputerBidResponse]
    is_my_turn: bool
    legal_bids: list[str]
    last_feedback: BidFeedbackResponse | None = None
    all_hands: dict[str, HandResponse] | None = None
    hand_number: int


# ── Serialization helpers ─────────────────────────────────────────
# Only functions with real logic (structural reshaping, conditional
# fields, or cross-object assembly). Leaf-level conversions are
# handled by from_attributes + BeforeValidator on the models above.


def serialize_hand(hand: Hand) -> HandResponse:
    """Convert a domain Hand to the API response shape.

    Hand stores cards as a frozenset; this groups them by suit
    and extracts rank strings.
    """
    return HandResponse(
        spades=[str(c.rank) for c in hand.spades],
        hearts=[str(c.rank) for c in hand.hearts],
        diamonds=[str(c.rank) for c in hand.diamonds],
        clubs=[str(c.rank) for c in hand.clubs],
    )


def serialize_auction(
    auction: AuctionState,
) -> AuctionResponse:
    """Convert an AuctionState to the API response shape.

    AuctionState stores bids as (Seat, Bid) tuples and derives
    contract/current_seat as properties, so this can't be a simple
    from_attributes conversion.
    """
    bids = [
        AuctionBidResponse(
            seat=str(seat),
            bid=str(bid),
            explanation=None,
        )
        for seat, bid in auction.bids
    ]
    contract = (
        ContractResponse.model_validate(auction.contract) if auction.contract else None
    )
    return AuctionResponse(
        dealer=str(auction.dealer),
        vulnerability=str(auction.vulnerability),
        bids=bids,
        is_complete=auction.is_complete,
        current_seat=(str(auction.current_seat) if not auction.is_complete else None),
        contract=contract,
    )


def serialize_practice_state(
    state: PracticeState,
) -> PracticeStateResponse:
    """Convert a PracticeState to the full API response shape.

    Handles auction with injected computer bid explanations,
    conditional hand reveals, and feedback assembly.
    """
    auction_resp = serialize_auction(state.auction)

    # Inject engine explanations and match status into auction entries by
    # bid index. Covers both computer bids and player bids.
    for i, abid in enumerate(auction_resp.bids):
        if i in state.bid_explanations:
            abid.explanation = state.bid_explanations[i]
        if i in state.bid_matched:
            abid.matched_engine = state.bid_matched[i]

    all_hands: dict[str, HandResponse] | None = None
    if state.all_hands is not None:
        all_hands = {
            str(seat): serialize_hand(hand) for seat, hand in state.all_hands.items()
        }

    last_feedback: BidFeedbackResponse | None = None
    if state.last_feedback is not None:
        last_feedback = BidFeedbackResponse.model_validate(state.last_feedback)

    return PracticeStateResponse(
        id=state.id,
        your_seat=str(state.your_seat),
        hand=serialize_hand(state.hand),
        hand_evaluation=HandEvalResponse.model_validate(state.hand_evaluation),
        auction=auction_resp,
        computer_bids=[
            ComputerBidResponse.model_validate(cb) for cb in state.computer_bids
        ],
        is_my_turn=state.is_my_turn,
        legal_bids=state.legal_bids,
        last_feedback=last_feedback,
        all_hands=all_hands,
        hand_number=state.hand_number,
    )
