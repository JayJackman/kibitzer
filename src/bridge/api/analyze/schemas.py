"""Pydantic schemas for bid/auction analysis endpoints.

Translates the engine's query results (HandDescription, BidAnalysis,
AuctionAnalysis) into JSON-friendly shapes. Reuses SeatInput from the
practice schemas for seat string parsing.
"""

from __future__ import annotations

from functools import cache

from pydantic import BaseModel, Field

from bridge.engine.hand_description import Bound, HandDescription
from bridge.engine.query import AuctionAnalysis, BidAnalysis, RuleMatch
from bridge.engine.registry import RuleRegistry
from bridge.engine.sayc import create_sayc_registry
from bridge.model.auction import AuctionState, Vulnerability
from bridge.model.bid import parse_bid
from bridge.model.card import Suit

from ..practice.schemas import SeatInput
from ..practice.session import compute_legal_bids

# ── Suit label mapping ───────────────────────────────────────────
# Maps Suit enum to human-readable suit names for JSON keys.
_SUIT_LABELS: dict[Suit, str] = {
    Suit.CLUBS: "clubs",
    Suit.DIAMONDS: "diamonds",
    Suit.HEARTS: "hearts",
    Suit.SPADES: "spades",
    Suit.NOTRUMP: "notrump",
}


@cache
def get_registry() -> RuleRegistry:
    """Return a cached SAYC registry (created once, reused across requests)."""
    return create_sayc_registry()


# ── Request schemas ──────────────────────────────────────────────


class AnalyzeBidRequest(BaseModel):
    """Analyze what a single bid means in a given auction position."""

    dealer: SeatInput
    vulnerability: str = Field(default="None")
    bids: list[str] = Field(default_factory=list)
    bid: str = Field(description="The bid to analyze, e.g. '1S', '2N'")


class AnalyzeAuctionRequest(BaseModel):
    """Analyze the full auction: what do we know about each player?"""

    dealer: SeatInput
    vulnerability: str = Field(default="None")
    bids: list[str] = Field(default_factory=list)


class AnalyzeAllBidsRequest(BaseModel):
    """Analyze all legal bids at the current auction position."""

    dealer: SeatInput
    vulnerability: str = Field(default="None")
    bids: list[str] = Field(default_factory=list)


# ── Response schemas ─────────────────────────────────────────────


class BoundResponse(BaseModel):
    """A min/max range. None means unconstrained on that side."""

    min: int | None
    max: int | None


class HandDescriptionResponse(BaseModel):
    """What we know about a hand: HCP, total points, suit lengths, shape, aces/kings."""

    hcp: BoundResponse
    total_pts: BoundResponse
    lengths: dict[str, BoundResponse]
    balanced: bool | None
    aces: BoundResponse
    kings: BoundResponse


class RuleMatchResponse(BaseModel):
    """A single rule that matched a bid."""

    rule_name: str
    explanation: str
    promise: HandDescriptionResponse


class BidAnalysisResponse(BaseModel):
    """Analysis of what a single bid means (Q2 result)."""

    bid: str
    matches: list[RuleMatchResponse]
    promise: HandDescriptionResponse


class AllBidsAnalysisResponse(BaseModel):
    """Analysis of all legal bids at the current position."""

    analyses: dict[str, BidAnalysisResponse]


class AuctionAnalysisResponse(BaseModel):
    """Full auction analysis: per-player hand descriptions + bid breakdown."""

    players: dict[str, HandDescriptionResponse]
    bid_analyses: list[BidAnalysisResponse]
    legal_bids: list[str]
    current_seat: str | None


# ── Serialization helpers ────────────────────────────────────────


def _serialize_bound(bound: Bound) -> BoundResponse:
    return BoundResponse(min=bound[0], max=bound[1])


def serialize_hand_description(desc: HandDescription) -> HandDescriptionResponse:
    """Convert a HandDescription to its API response shape."""
    return HandDescriptionResponse(
        hcp=_serialize_bound(desc.hcp),
        total_pts=_serialize_bound(desc.total_pts),
        lengths={
            _SUIT_LABELS[suit]: _serialize_bound(bound)
            for suit, bound in desc.lengths.items()
        },
        balanced=desc.balanced,
        aces=_serialize_bound(desc.aces),
        kings=_serialize_bound(desc.kings),
    )


def serialize_rule_match(match: RuleMatch) -> RuleMatchResponse:
    """Convert a RuleMatch to its API response shape."""
    return RuleMatchResponse(
        rule_name=match.rule_name,
        explanation=match.explanation,
        promise=serialize_hand_description(match.promise),
    )


def serialize_bid_analysis(analysis: BidAnalysis) -> BidAnalysisResponse:
    """Convert a BidAnalysis to its API response shape."""
    return BidAnalysisResponse(
        bid=str(analysis.bid),
        matches=[serialize_rule_match(m) for m in analysis.matches],
        promise=serialize_hand_description(analysis.promise),
    )


def serialize_auction_analysis(
    analysis: AuctionAnalysis,
    auction: AuctionState,
) -> AuctionAnalysisResponse:
    """Convert an AuctionAnalysis to its API response shape.

    Also includes legal_bids and current_seat derived from the auction
    state, so the frontend has everything it needs in one response.
    """
    return AuctionAnalysisResponse(
        players={
            str(seat): serialize_hand_description(desc)
            for seat, desc in analysis.players.items()
        },
        bid_analyses=[serialize_bid_analysis(ba) for ba in analysis.bid_analyses],
        legal_bids=compute_legal_bids(auction) if not auction.is_complete else [],
        current_seat=str(auction.current_seat) if not auction.is_complete else None,
    )


def build_auction(
    dealer: SeatInput,
    vulnerability_str: str,
    bid_strings: list[str],
) -> AuctionState:
    """Reconstruct an AuctionState from request parameters.

    Parses vulnerability and each bid string, adding them to a fresh
    AuctionState. Raises ValueError / IllegalBidError on bad input.
    """
    vuln = Vulnerability.from_str(vulnerability_str)
    auction = AuctionState(dealer=dealer, vulnerability=vuln)
    for bid_str in bid_strings:
        auction.add_bid(parse_bid(bid_str))
    return auction
