"""Rule base class and result type for the bidding engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import TYPE_CHECKING, cast

from bridge.engine.condition import All, Any, CheckResult, Condition
from bridge.model.bid import Bid

if TYPE_CHECKING:
    from bridge.engine.context import AuctionContext, BiddingContext


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

    The engine evaluates rules through a three-step lifecycle:

    1. ``prerequisites`` — auction-state guards that determine whether this
       rule is even *relevant* to the current auction (e.g. "partner opened
       1 of a suit", "partner single-raised"). If prerequisites fail, the
       rule is silently skipped — it doesn't appear in the thought process.

    2. ``conditions`` — hand-evaluation predicates that determine whether the
       player's hand matches the rule (e.g. "15-17 HCP", "balanced shape").
       These are what the thought process displays to the user.

    3. ``select(ctx)`` — called only when both prerequisites and conditions
       passed. Produces the concrete bid along with metadata (explanation
       text, alert flags, forcing status).

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
    def prerequisites(self) -> Condition | None:
        """Auction-state guards checked before hand conditions.

        Return a Condition tree that tests auction state (e.g. "partner
        opened 1 of a suit"). If this returns None (the default), the
        rule has no prerequisites and is always considered.

        When prerequisites fail, the rule is silently skipped — it won't
        appear in the thought process at all.
        """
        return None

    @property
    @abstractmethod
    def conditions(self) -> Condition:
        """Hand-evaluation conditions checked after prerequisites pass."""

    def applies(self, ctx: BiddingContext) -> bool:
        """Check whether this rule is relevant for the given context."""
        return self.check(ctx).passed

    def check(self, ctx: BiddingContext) -> CheckResult:
        """Full condition evaluation with per-condition pass/fail details.

        Evaluates prerequisites first. If they fail, returns immediately
        with ``prerequisite_passed=False`` and no hand condition results.
        If they pass (or are None), evaluates hand conditions normally.
        """
        if not self.prerequisites_pass(ctx):
            return CheckResult(
                passed=False,
                prerequisite_passed=False,
                results=(),
            )

        conds = self.conditions
        if isinstance(conds, (All, Any)):
            result = conds.check_all(ctx)
        else:
            r = conds.check(ctx)
            result = CheckResult(
                passed=r.passed,
                prerequisite_passed=True,
                results=(r,),
            )
        return CheckResult(
            passed=result.passed,
            prerequisite_passed=True,
            results=result.results,
        )

    def prerequisites_pass(self, ctx: AuctionContext) -> bool:
        """Check whether this rule's auction-state prerequisites are met.

        Unlike ``check()``, this does not evaluate hand conditions --
        only the prerequisite guards.  Accepts ``AuctionContext`` because
        prerequisites only access auction-derived properties.

        The ``cast`` to ``BiddingContext`` is safe: prerequisites never
        access hand data.  This is an architectural invariant maintained
        by rule authors (prerequisites test auction state, conditions
        test the hand).
        """
        prereqs = self.prerequisites
        if prereqs is None:
            return True
        bc = cast("BiddingContext", ctx)
        if isinstance(prereqs, (All, Any)):
            return prereqs.check_all(bc).passed
        return prereqs.check(bc).passed

    @abstractmethod
    def possible_bids(self, ctx: AuctionContext) -> frozenset[Bid]:
        """The set of bids this rule could produce in the given auction state.

        Returns a frozenset of every bid this rule might select, considering
        the auction state but *not* the player's hand. Used to answer "what
        does bid X mean?" (filter rules that could produce X) and "what do
        we know about this player?" (collect promises from all rules whose
        possible bids include a player's actual bid).

        Callers must check prerequisites before calling this method.
        Implementations may assume prerequisites hold and use unsafe
        accessors (e.g. _opener_suit instead of _opener_suit_safe).
        """

    @abstractmethod
    def select(self, ctx: BiddingContext) -> RuleResult:
        """Produce the bid and metadata. Only called if applies() returned True."""
