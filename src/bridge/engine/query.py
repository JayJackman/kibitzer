"""Query functions for analyzing bids without hand information.

Q1: "What do we know about each player's hand?" -- walk an auction's
bids, collecting and intersecting promises to build a HandDescription
per player.

Q2: "What would bid X mean here?" -- given an auction state and a
candidate bid, find all rules that could produce that bid and collect
their promises (what the bid guarantees about the hand).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bridge.engine.context import AuctionContext
from bridge.engine.hand_description import HandDescription
from bridge.engine.registry import RuleRegistry
from bridge.engine.selector import collect_rules
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import Bid, is_pass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleMatch:
    """A single rule that could produce the analyzed bid."""

    rule_name: str
    explanation: str
    promise: HandDescription


@dataclass(frozen=True)
class BidAnalysis:
    """Result of analyzing what a bid means in a given auction state.

    ``matches`` lists every rule that could produce the bid (prerequisites
    pass and bid is in ``possible_bids``).  ``promise`` is the union of
    all matches' promises -- the weakest guarantee across all candidate
    explanations.  When there is exactly one match, ``promise`` equals
    that match's promise.
    """

    bid: Bid
    matches: tuple[RuleMatch, ...]
    promise: HandDescription


def analyze_bid(
    auction: AuctionState,
    bid: Bid,
    registry: RuleRegistry,
) -> BidAnalysis:
    """Analyze what a bid would mean in the current auction state.

    Finds all rules whose prerequisites pass and whose ``possible_bids``
    include the candidate bid, then collects their promises.

    Args:
        auction: The current auction state (before the candidate bid).
        bid: The candidate bid to analyze.
        registry: The rule registry to search.

    Returns:
        A ``BidAnalysis`` with individual rule matches and their promise
        (unioned) promise.
    """
    ctx = AuctionContext(auction, auction.current_seat)
    rules = collect_rules(registry, ctx)
    matches: list[RuleMatch] = []

    for rule in rules:
        if not rule.prerequisites_pass(ctx):
            continue

        if bid not in rule.possible_bids(ctx):
            continue

        promise = rule.conditions.promises(ctx, bid)
        matches.append(
            RuleMatch(
                rule_name=rule.name,
                explanation=rule.conditions.label,
                promise=promise,
            )
        )
        logger.debug("Rule %s matches bid %s: %s", rule.name, bid, promise)

    if not matches:
        promise = HandDescription()
    elif len(matches) == 1:
        promise = matches[0].promise
    else:
        promise = matches[0].promise
        for match in matches[1:]:
            promise = promise | match.promise

    return BidAnalysis(
        bid=bid,
        matches=tuple(matches),
        promise=promise,
    )


@dataclass(frozen=True)
class AuctionAnalysis:
    """What we know about every player's hand from the auction so far.

    ``players`` maps each seat to a ``HandDescription`` built by
    intersecting the promises of all non-pass bids that player made.
    ``bid_analyses`` contains the per-bid breakdown (non-pass bids only,
    in auction order).
    """

    players: dict[Seat, HandDescription]
    bid_analyses: tuple[BidAnalysis, ...]


def analyze_auction(
    auction: AuctionState,
    registry: RuleRegistry,
) -> AuctionAnalysis:
    """Analyze what we know about every player's hand from the auction.

    Walks the auction bid by bid, replaying into a partial auction state.
    For each non-pass bid, calls ``analyze_bid`` on the state *before*
    that bid to find matching rules and their promises.  Successive bids
    by the same player are intersected (narrowing what we know).

    Args:
        auction: The full auction to analyze.
        registry: The rule registry to search.

    Returns:
        An ``AuctionAnalysis`` with per-player hand descriptions and
        per-bid breakdowns.
    """
    descriptions: dict[Seat, HandDescription] = {
        seat: HandDescription() for seat in Seat
    }
    partial = AuctionState(
        dealer=auction.dealer,
        vulnerability=auction.vulnerability,
    )
    analyses: list[BidAnalysis] = []

    for seat, bid in auction.bids:
        if not is_pass(bid):
            analysis = analyze_bid(partial, bid, registry)
            descriptions[seat] = descriptions[seat] & analysis.promise
            analyses.append(analysis)
        partial.add_bid(bid)

    return AuctionAnalysis(
        players=descriptions,
        bid_analyses=tuple(analyses),
    )
