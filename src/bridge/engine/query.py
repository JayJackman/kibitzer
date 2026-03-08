"""Query functions for analyzing bids without hand information.

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
from bridge.model.auction import AuctionState
from bridge.model.bid import Bid

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
    pass and bid is in ``possible_bids``).  ``combined`` is the union of
    all matches' promises -- the weakest guarantee across all candidate
    explanations.  When there is exactly one match, ``combined`` equals
    that match's promise.
    """

    bid: Bid
    matches: tuple[RuleMatch, ...]
    combined: HandDescription


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
        A ``BidAnalysis`` with individual rule matches and their combined
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
        combined = HandDescription()
    elif len(matches) == 1:
        combined = matches[0].promise
    else:
        combined = matches[0].promise
        for match in matches[1:]:
            combined = combined | match.promise

    return BidAnalysis(
        bid=bid,
        matches=tuple(matches),
        combined=combined,
    )
