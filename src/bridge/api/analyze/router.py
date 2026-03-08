"""Bid and auction analysis endpoints.

Three endpoints for the Q1/Q2 query system:
- POST /api/analyze/bid       Analyze what a single bid means (Q2)
- POST /api/analyze/auction   Analyze full auction: per-player knowledge (Q1)
- POST /api/analyze/all-bids  Analyze all legal bids at current position (batch Q2)

These endpoints are stateless -- they reconstruct the auction from the
request body each time. No session needed; the frontend can call them
from any page (practice mode trial bids, standalone analyzer, etc.).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from bridge.api.practice.session import compute_legal_bids
from bridge.engine.query import analyze_auction, analyze_bid
from bridge.model.auction import AuctionState, IllegalBidError, Seat
from bridge.model.bid import parse_bid

from .schemas import (
    AllBidsAnalysisResponse,
    AnalyzeAllBidsRequest,
    AnalyzeAuctionRequest,
    AnalyzeBidRequest,
    AuctionAnalysisResponse,
    BidAnalysisResponse,
    build_auction,
    get_registry,
    serialize_auction_analysis,
    serialize_bid_analysis,
)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


def _build_auction_or_422(
    dealer: Seat,
    vulnerability: str,
    bids: list[str],
) -> AuctionState:
    """Build an AuctionState from request params, raising 422 on bad input."""
    try:
        return build_auction(dealer, vulnerability, bids)
    except (ValueError, IllegalBidError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from None


@router.post("/bid", response_model=BidAnalysisResponse)
def analyze_single_bid(body: AnalyzeBidRequest) -> BidAnalysisResponse:
    """Analyze what a single bid would mean in the given auction position.

    Reconstructs the auction from dealer + vulnerability + prior bids,
    then finds all rules whose prerequisites pass and whose possible_bids
    include the candidate bid. Returns each matching rule's promise and
    the union (weakest guarantee) across all matches.
    """
    auction = _build_auction_or_422(body.dealer, body.vulnerability, body.bids)

    try:
        bid = parse_bid(body.bid)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from None

    result = analyze_bid(auction, bid, get_registry())
    return serialize_bid_analysis(result)


@router.post("/auction", response_model=AuctionAnalysisResponse)
def analyze_full_auction(body: AnalyzeAuctionRequest) -> AuctionAnalysisResponse:
    """Analyze the full auction: what do we know about each player's hand?

    Walks the auction bid by bid, finding matching rules for each non-pass
    bid and intersecting promises per player. Also returns the current
    legal bids and whose turn it is, so the frontend can drive a
    step-by-step analyzer UI.
    """
    auction = _build_auction_or_422(body.dealer, body.vulnerability, body.bids)
    result = analyze_auction(auction, get_registry())
    return serialize_auction_analysis(result, auction)


@router.post("/all-bids", response_model=AllBidsAnalysisResponse)
def analyze_all_legal_bids(body: AnalyzeAllBidsRequest) -> AllBidsAnalysisResponse:
    """Analyze all legal bids at the current auction position.

    For each legal bid (suit bids, pass, double, redouble as applicable),
    runs analyze_bid to find matching rules and their promises. Returns
    a dict mapping bid strings to their analysis. Used by the practice
    page to batch-fetch all trial bid previews when it's the player's turn.
    """
    auction = _build_auction_or_422(body.dealer, body.vulnerability, body.bids)

    if auction.is_complete:
        return AllBidsAnalysisResponse(analyses={})

    registry = get_registry()
    legal = compute_legal_bids(auction)
    analyses: dict[str, BidAnalysisResponse] = {}

    for bid_str in legal:
        bid = parse_bid(bid_str)
        result = analyze_bid(auction, bid, registry)
        analyses[bid_str] = serialize_bid_analysis(result)

    return AllBidsAnalysisResponse(analyses=analyses)
