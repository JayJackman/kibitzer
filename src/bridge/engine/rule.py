"""Rule base class and result type for the bidding engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import TYPE_CHECKING

from bridge.model.bid import Bid

if TYPE_CHECKING:
    from bridge.engine.context import BiddingContext


@unique
class Category(StrEnum):
    """Auction phases that rules belong to."""

    OPENING = "opening"
    RESPONSE = "response"
    COMPETITIVE_RESPONSE = "competitive_response"
    REBID_OPENER = "rebid_opener"
    REBID_RESPONDER = "rebid_responder"
    COMPETITIVE = "competitive"
    CONVENTION = "convention"
    SLAM = "slam"


@dataclass(frozen=True)
class RuleResult:
    """The output of a rule that matched."""

    bid: Bid
    rule_name: str
    explanation: str
    alerts: tuple[str, ...] = ()
    forcing: bool = False


class Rule(ABC):
    """A rule is the fundamental building block of the bidding engine.

    Each rule encodes a single bidding decision: given the current state of the
    auction and the player's hand, should a particular bid be made? Rules map
    directly to the entries you'd find in a bidding system reference — "open 1NT
    with 15-17 HCP and balanced shape", "respond 2H with 6-10 points and 3+
    card support", and so on.

    The engine evaluates rules through a two-step lifecycle:

    1. ``applies(ctx)`` — a cheap boolean filter that checks whether this rule
       is even relevant. Most rules gate on HCP range, shape, or auction state.
       This keeps evaluation fast: rules that can't possibly match are skipped
       without computing a full bid.

    2. ``select(ctx)`` — called only when ``applies()`` returned True. This
       method produces the concrete bid along with metadata (explanation text,
       alert flags, forcing status).

    Rules are organized by **category** (the auction phase they belong to, such
    as OPENING or RESPONSE) and **priority** (which rule wins when multiple
    rules apply). The ``BidSelector`` detects the current phase from the auction
    state, collects all rules for that phase plus CONVENTION and SLAM overlays,
    and walks them in priority order (highest first). The first rule whose
    ``applies()`` returns True wins.

    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique dotted identifier, e.g. 'opening.1nt'."""

    @property
    @abstractmethod
    def category(self) -> Category:
        """Auction phase this rule belongs to."""

    @property
    @abstractmethod
    def priority(self) -> int:
        """Higher wins. Bands: 0-99 fallback, 100-199 general,
        200-299 specific, 300-399 convention, 400-499 strong, 500+ slam.
        Must be unique within a category.
        """

    @abstractmethod
    def applies(self, ctx: BiddingContext) -> bool:
        """Fast boolean pre-filter. Should be cheap (HCP range, shape, etc.)."""

    @abstractmethod
    def select(self, ctx: BiddingContext) -> RuleResult:
        """Produce the bid and metadata. Only called if applies() returned True."""
