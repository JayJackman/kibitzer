"""Rule base class and result type for the bidding engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import TYPE_CHECKING

from bridge.engine.condition import All, Any, CheckResult, Condition
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


class Priority:
    """Universal semantic priority bands for all rule categories.

    Higher priority = checked first by the selector.  Within a band, higher
    values denote more specific rules.  Rules in mutually exclusive sections
    (different guards) may share the same numeric value.

    Convention sections (NT/2C/preempt responses and rebids) already use
    high-priority schemes that fit FORCED/CONVENTION naturally.
    """

    FORCED = 500
    """500+: Convention completions (completing transfers, Stayman response)."""

    CONVENTION = 440
    """440-499: Convention initiations, slam tries (Blackwood, Jacoby)."""

    GAME = 300
    """300-439: Game-level natural bids (3NT, game raises)."""

    INVITE = 220
    """220-299: Invitational (limit raises, 2NT invites, new suits)."""

    MINIMUM = 100
    """100-219: Minimum/constructive (single raises, 1NT, own suit rebid)."""

    SIGNOFF = 40
    """40-99: Pass, sign-off."""


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

    1. ``conditions`` — a declarative ``Condition`` tree that determines
       whether this rule is relevant. The ``applies(ctx)`` method evaluates
       these conditions and returns a boolean.

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
        """Higher wins. See ``Priority`` for band definitions."""

    @property
    @abstractmethod
    def conditions(self) -> Condition:
        """Declarative preconditions checked before ``select()``."""

    def applies(self, ctx: BiddingContext) -> bool:
        """Check whether this rule is relevant for the given context."""
        return self.check(ctx).passed

    def check(self, ctx: BiddingContext) -> CheckResult:
        """Full condition evaluation with per-condition pass/fail details."""
        conds = self.conditions
        if isinstance(conds, (All, Any)):
            return conds.check_all(ctx)
        r = conds.check(ctx)
        return CheckResult(passed=r.passed, results=(r,))

    @abstractmethod
    def select(self, ctx: BiddingContext) -> RuleResult:
        """Produce the bid and metadata. Only called if applies() returned True."""
