"""Declarative condition system for bidding rules.

Instead of imperative ``applies()`` methods that return True/False,
rules declare their preconditions as composable Condition objects.
Each condition can explain *why* it passed or failed for a given hand,
enabling structured thought-process generation.

The system has three layers:

1. **Base types** — ``Condition`` ABC, ``ConditionResult``, ``CheckResult``
2. **Combinators** — ``All`` (AND), ``Any`` (OR), ``Not`` (negation)
3. **Concrete conditions** — ``HcpRange``, ``Balanced``, ``Computed``, etc.

Typical usage in a rule::

    class Open1NT(Rule):
        @property
        def conditions(self) -> Condition:
            return All(HcpRange(15, 17), Balanced(strict=True))

The engine calls ``rule.check(ctx)`` which evaluates every condition
and returns a ``CheckResult`` with per-condition pass/fail details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bridge import evaluate
from bridge.model.card import Suit

if TYPE_CHECKING:
    from collections.abc import Callable

    from bridge.engine.context import BiddingContext


# ---------------------------------------------------------------------------
# Base types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConditionResult:
    """The outcome of evaluating a single condition.

    Attributes:
        passed: Whether the condition was satisfied.
        label: A static, human-readable name for the condition
               (e.g. "15-17 HCP"). Does not change between evaluations.
        detail: A contextual description that includes actual values
                from the hand (e.g. "16 HCP (15-17)"). Changes per hand.
    """

    passed: bool
    label: str
    detail: str


@dataclass(frozen=True)
class CheckResult:
    """Aggregate result from evaluating all conditions on a rule.

    Returned by ``All.check_all()`` and ``Any.check_all()``, and by
    ``Rule.check()``.  Contains the individual ``ConditionResult``
    for each condition that was evaluated.

    Attributes:
        passed: Whether all conditions (or at least one path) passed.
        prerequisite_passed: Whether the rule's auction-state prerequisites
            were satisfied.  When False, ``results`` is empty (hand
            conditions were never evaluated).  Defaults to True for
            backward compatibility with combinator internals.
        results: Individual results, in evaluation order.  For ``All``,
                 this stops at the first failure (short-circuit).
    """

    passed: bool
    prerequisite_passed: bool = True
    results: tuple[ConditionResult, ...] = ()


class Condition(ABC):
    """A single testable predicate about the hand and/or auction state.

    Every concrete condition implements two things:

    - ``label`` — a short static description (e.g. "15-17 HCP")
    - ``check(ctx)`` — evaluate against a ``BiddingContext`` and return
      a ``ConditionResult`` with contextual detail text.

    Conditions are composed using ``All``, ``Any``, and ``Not`` to build
    the full precondition tree for a rule.
    """

    @property
    @abstractmethod
    def label(self) -> str:
        """Short static description of what this condition tests."""

    @abstractmethod
    def check(self, ctx: BiddingContext) -> ConditionResult:
        """Evaluate this condition against the given context."""


# ---------------------------------------------------------------------------
# Combinators
# ---------------------------------------------------------------------------


class All(Condition):
    """AND combinator — all inner conditions must pass.

    Used by ~95% of rules.  ``check_all()`` evaluates each condition
    in order, collecting individual results.  It **short-circuits** on
    the first failure: remaining conditions are not evaluated.

    Example::

        All(HcpRange(15, 17), Balanced(strict=True))
        # Passes only if HCP is 15-17 AND shape is balanced.
    """

    def __init__(self, *conditions: Condition) -> None:
        self._conditions = conditions

    @property
    def label(self) -> str:
        return " AND ".join(c.label for c in self._conditions)

    def check(self, ctx: BiddingContext) -> ConditionResult:
        """Single-result interface required by the Condition ABC.

        For full per-condition detail, use ``check_all()`` instead.
        """
        result = self.check_all(ctx)
        return ConditionResult(
            passed=result.passed,
            label=self.label,
            detail="; ".join(r.detail for r in result.results),
        )

    def check_all(self, ctx: BiddingContext) -> CheckResult:
        """Evaluate all conditions, returning individual results.

        Short-circuits on the first failure — conditions after the
        failing one are not evaluated (and not included in results).
        """
        results: list[ConditionResult] = []
        for cond in self._conditions:
            r = cond.check(ctx)
            results.append(r)
            if not r.passed:
                return CheckResult(
                    passed=False,
                    results=tuple(results),
                )
        return CheckResult(
            passed=True,
            results=tuple(results),
        )


class Any(Condition):
    """OR combinator — at least one inner path must pass.

    Used by ~6 rules (e.g. Stayman with garbage vs regular path).
    Each path is typically an ``All(...)``.  Paths are tried in order;
    the first passing path's ``CheckResult`` is returned.

    Example::

        Any(
            All(SuitLength(Suit.HEARTS, min_len=4),
                SuitLength(Suit.SPADES, min_len=4)),  # Garbage path
            All(HcpRange(min_hcp=8), has_4_card_major),  # Regular path
        )
    """

    def __init__(self, *paths: Condition) -> None:
        self._paths = paths

    @property
    def label(self) -> str:
        return " OR ".join(c.label for c in self._paths)

    def check(self, ctx: BiddingContext) -> ConditionResult:
        """Single-result interface required by the Condition ABC."""
        result = self.check_all(ctx)
        return ConditionResult(
            passed=result.passed,
            label=self.label,
            detail="; ".join(r.detail for r in result.results),
        )

    def check_all(self, ctx: BiddingContext) -> CheckResult:
        """Try each path in order; return the first passing path's result.

        If no path passes, returns the last path's (failed) result so
        the caller can see why every option was rejected.
        """
        last_result: CheckResult | None = None
        for path in self._paths:
            if isinstance(path, (All, Any)):
                result = path.check_all(ctx)
            else:
                r = path.check(ctx)
                result = CheckResult(passed=r.passed, results=(r,))
            if result.passed:
                return result
            last_result = result
        # All paths failed — return the last one's result
        assert last_result is not None, "Any() requires at least one path"
        return last_result


class Not(Condition):
    """Negation — inverts the inner condition's result.

    The optional ``label`` parameter controls the thought-process text.
    Without it, the inner condition's label is reused with "No " / "Has "
    prefixes.  With it, "Not {label}" / "In {label}" is used instead.

    Examples::

        Not(has_5_plus_major)
        # Pass detail: "No 5+ card major"
        # Fail detail: "Has 5+ card major"

        Not(All(Balanced(strict=True), HcpRange(15, 17)),
            label="in 1NT range")
        # Pass detail: "Not in 1NT range"
        # Fail detail: "In 1NT range"
    """

    def __init__(self, inner: Condition, *, label: str | None = None) -> None:
        self._inner = inner
        self._label_override = label

    @property
    def label(self) -> str:
        if self._label_override is not None:
            return f"Not {self._label_override}"
        return f"No {self._inner.label}"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        inner_result = self._inner.check(ctx)
        passed = not inner_result.passed
        if self._label_override is not None:
            # Custom label: "Not in 1NT range" / "In 1NT range"
            if passed:
                detail = f"Not {self._label_override}"
            else:
                detail = self._label_override[0].upper() + self._label_override[1:]
        else:
            # Auto-generate from inner label
            detail = f"No {self._inner.label}" if passed else f"Has {self._inner.label}"
        return ConditionResult(
            passed=passed,
            label=self.label,
            detail=detail,
        )


# ---------------------------------------------------------------------------
# Computed condition
# ---------------------------------------------------------------------------


class Computed[T](Condition):
    """Compute a value, cache it, and pass/fail based on whether it is None.

    Solves the shared-state problem between ``applies()`` and ``select()``.
    About 30 rules call a suit-finding function in ``applies()`` to check if
    a result exists, then re-call it in ``select()`` to use the result.
    ``Computed`` runs the function once during condition checking and caches
    the result for ``select()`` to read via the ``.value`` property.

    The function receives a ``BiddingContext`` and returns ``T | None``:
    - If the result is not None: condition passes, value is cached.
    - If the result is None: condition fails.

    Each ``check()`` call overwrites the cache, so the value is always
    fresh for the current hand.

    Thread safety: ``Computed`` stores mutable state on the instance.
    Rules are singletons evaluated sequentially by ``BidSelector`` —
    this is safe for single-threaded use.

    Example::

        class Open1Major(Rule):
            def __init__(self) -> None:
                self._best_major = Computed(
                    lambda ctx: best_major(ctx.hand),
                    "5+ card major",
                )

            @property
            def conditions(self) -> Condition:
                return All(MeetsOpeningStrength(), self._best_major)

            def select(self, ctx: BiddingContext) -> RuleResult:
                suit = self._best_major.value  # Cached from check()
                return RuleResult(bid=SuitBid(1, suit), ...)
    """

    def __init__(
        self,
        func: Callable[[BiddingContext], T | None],
        label_text: str,
    ) -> None:
        self._func = func
        self._label_text = label_text
        self._cached: T | None = None

    @property
    def label(self) -> str:
        return self._label_text

    def check(self, ctx: BiddingContext) -> ConditionResult:
        result = self._func(ctx)
        self._cached = result
        if result is not None:
            return ConditionResult(
                passed=True,
                label=self._label_text,
                detail=f"Found {result} ({self._label_text})",
            )
        return ConditionResult(
            passed=False,
            label=self._label_text,
            detail=f"No {self._label_text} found",
        )

    @property
    def value(self) -> T:
        """Return the cached value from the last ``check()`` call.

        Only valid after ``check()`` returned a passing result.
        Asserts non-None — calling this when the condition failed
        (or before any check) is a programming error.
        """
        assert self._cached is not None
        return self._cached


# ---------------------------------------------------------------------------
# @condition decorator
# ---------------------------------------------------------------------------


class _PredicateCondition(Condition):
    """A Condition created by the ``@condition`` decorator.

    Wraps a ``(BiddingContext) -> bool`` function, making it both:

    - A ``Condition`` (usable in ``All``/``Any``/``Not`` combinators)
    - A callable (usable by other helper functions that need the bool)

    The ``__call__`` method allows decorated functions to still be called
    as regular functions by other helpers that compose on top of them::

        @condition("Partner bid a new suit")
        def partner_bid_new_suit(ctx: BiddingContext) -> bool:
            ...

        @condition("Partner bid new suit at 1-level")
        def partner_bid_new_suit_1_level(ctx: BiddingContext) -> bool:
            # Calls partner_bid_new_suit as a function (via __call__),
            # even though it's also a Condition object.
            return partner_bid_new_suit(ctx) and ...
    """

    def __init__(
        self,
        func: Callable[[BiddingContext], bool],
        label_text: str,
    ) -> None:
        self._func = func
        self._label_text = label_text

    @property
    def label(self) -> str:
        return self._label_text

    def check(self, ctx: BiddingContext) -> ConditionResult:
        passed = self._func(ctx)
        if passed:
            return ConditionResult(
                passed=True,
                label=self._label_text,
                detail=self._label_text,
            )
        return ConditionResult(
            passed=False,
            label=self._label_text,
            detail=f"Not: {self._label_text}",
        )

    def __call__(self, ctx: BiddingContext) -> bool:
        """Allow this condition to be called as a regular function.

        Needed because some decorated helpers call other decorated
        helpers as part of their logic.  Without ``__call__``, the
        call ``partner_bid_new_suit(ctx)`` would fail since the name
        refers to a ``_PredicateCondition`` instance, not a function.
        """
        return self._func(ctx)


def condition(
    label: str,
) -> Callable[[Callable[[BiddingContext], bool]], _PredicateCondition]:
    """Decorator that turns a ``(BiddingContext -> bool)`` function into a Condition.

    The decorated function becomes a ``_PredicateCondition`` instance that
    can be used in two ways:

    1. **As a condition in a rule** — passed directly to ``All``/``Any``/``Not``::

           @condition("Partner opened 1NT")
           def opened_1nt(ctx: BiddingContext) -> bool:
               ...

           class RespondStayman(Rule):
               @property
               def conditions(self) -> Condition:
                   return All(opened_1nt, HcpRange(min_hcp=8))

    2. **As a function in another helper** — via ``__call__``::

           opened_1nt(ctx)  # Returns bool

    Only the ~35 boolean helpers that appear directly in rule conditions
    should use ``@condition``.  Internal utility functions that return
    values (like ``_opening_bid(ctx) -> SuitBid``) stay as plain functions.
    """

    def decorator(
        func: Callable[[BiddingContext], bool],
    ) -> _PredicateCondition:
        return _PredicateCondition(func, label)

    return decorator


# ---------------------------------------------------------------------------
# Concrete condition classes
# ---------------------------------------------------------------------------


class HcpRange(Condition):
    """Test whether the hand's HCP falls within a range.

    Either bound can be omitted (None) for open-ended ranges.

    Examples::

        HcpRange(15, 17)       # 15-17 HCP (1NT opening)
        HcpRange(min_hcp=12)   # 12+ HCP
        HcpRange(max_hcp=11)   # 0-11 HCP
    """

    def __init__(
        self,
        min_hcp: int | None = None,
        max_hcp: int | None = None,
    ) -> None:
        self._min = min_hcp
        self._max = max_hcp

    @property
    def label(self) -> str:
        if self._min is not None and self._max is not None:
            return f"{self._min}-{self._max} HCP"
        if self._min is not None:
            return f"{self._min}+ HCP"
        if self._max is not None:
            return f"0-{self._max} HCP"
        return "Any HCP"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        hcp = ctx.hcp
        passed = True
        if self._min is not None and hcp < self._min:
            passed = False
        if self._max is not None and hcp > self._max:
            passed = False
        if passed:
            detail = f"{hcp} HCP ({self.label})"
        else:
            detail = f"{hcp} HCP (need {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class TotalPtsRange(Condition):
    """Test whether total points (HCP + length) fall within a range.

    Examples::

        TotalPtsRange(min_pts=22)       # 22+ total points (2C opening)
        TotalPtsRange(min_pts=6, max_pts=10)  # 6-10 total points
    """

    def __init__(
        self,
        min_pts: int | None = None,
        max_pts: int | None = None,
    ) -> None:
        self._min = min_pts
        self._max = max_pts

    @property
    def label(self) -> str:
        if self._min is not None and self._max is not None:
            return f"{self._min}-{self._max} total points"
        if self._min is not None:
            return f"{self._min}+ total points"
        if self._max is not None:
            return f"0-{self._max} total points"
        return "Any total points"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        pts = ctx.total_pts
        passed = True
        if self._min is not None and pts < self._min:
            passed = False
        if self._max is not None and pts > self._max:
            passed = False
        if passed:
            detail = f"{pts} total points ({self.label})"
        else:
            detail = f"{pts} total points (need {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class BergenPtsRange(Condition):
    """Test whether Bergen points fall within a range.

    Bergen points re-evaluate opener's hand after partner raises their
    suit.  Requires a trump suit from the auction (typically the opener's
    suit that was raised).

    The ``suit_fn`` extracts the trump suit from the context.  This is
    necessary because the suit varies by auction — it's whatever suit
    the opener bid that was then raised.

    Example::

        BergenPtsRange(suit_fn=_my_opening_suit, min_pts=16, max_pts=18)
    """

    def __init__(
        self,
        suit_fn: Callable[[BiddingContext], Suit],
        min_pts: int | None = None,
        max_pts: int | None = None,
    ) -> None:
        self._suit_fn = suit_fn
        self._min = min_pts
        self._max = max_pts

    @property
    def label(self) -> str:
        if self._min is not None and self._max is not None:
            return f"{self._min}-{self._max} Bergen points"
        if self._min is not None:
            return f"{self._min}+ Bergen points"
        if self._max is not None:
            return f"0-{self._max} Bergen points"
        return "Any Bergen points"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        suit = self._suit_fn(ctx)
        pts = evaluate.bergen_points(ctx.hand, suit)
        passed = True
        if self._min is not None and pts < self._min:
            passed = False
        if self._max is not None and pts > self._max:
            passed = False
        if passed:
            detail = f"{pts} Bergen points ({self.label})"
        else:
            detail = f"{pts} Bergen points (need {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class SupportPtsRange(Condition):
    """Test whether support points (HCP + shortness) fall within a range.

    Support points evaluate responder's hand for raising partner's suit.
    Like ``BergenPtsRange``, requires a ``suit_fn`` to determine the
    trump suit from the auction context.

    Example::

        SupportPtsRange(suit_fn=_opener_suit, min_pts=6, max_pts=10)
    """

    def __init__(
        self,
        suit_fn: Callable[[BiddingContext], Suit],
        min_pts: int | None = None,
        max_pts: int | None = None,
    ) -> None:
        self._suit_fn = suit_fn
        self._min = min_pts
        self._max = max_pts

    @property
    def label(self) -> str:
        if self._min is not None and self._max is not None:
            return f"{self._min}-{self._max} support points"
        if self._min is not None:
            return f"{self._min}+ support points"
        if self._max is not None:
            return f"0-{self._max} support points"
        return "Any support points"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        suit = self._suit_fn(ctx)
        pts = evaluate.support_points(ctx.hand, suit)
        passed = True
        if self._min is not None and pts < self._min:
            passed = False
        if self._max is not None and pts > self._max:
            passed = False
        if passed:
            detail = f"{pts} support points ({self.label})"
        else:
            detail = f"{pts} support points (need {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class Balanced(Condition):
    """Test whether the hand shape is balanced.

    With ``strict=True``, only truly balanced shapes qualify
    (4-3-3-3, 4-4-3-2, 5-3-3-2).  With ``strict=False`` (default),
    semi-balanced shapes (5-4-2-2, 6-3-2-2) also qualify.

    Examples::

        Balanced(strict=True)   # For 1NT/2NT openings
        Balanced()              # Semi-balanced also OK
    """

    def __init__(self, *, strict: bool = False) -> None:
        self._strict = strict

    @property
    def label(self) -> str:
        return "balanced" if self._strict else "semi-balanced"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        passed = ctx.is_balanced if self._strict else ctx.is_semi_balanced
        shape_str = "-".join(str(n) for n in ctx.sorted_shape)
        if passed:
            detail = f"Shape {shape_str} ({self.label})"
        else:
            detail = f"Shape {shape_str} (not {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class NoVoid(Condition):
    """Test that the hand has no void (zero-length) suit.

    Required for weak two openings — a void makes the hand
    too distributional for a disciplined weak two.
    """

    @property
    def label(self) -> str:
        return "no void"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        has_void = 0 in ctx.shape
        if not has_void:
            return ConditionResult(passed=True, label=self.label, detail="No void")
        return ConditionResult(passed=False, label=self.label, detail="Has void")


class ShapeNot(Condition):
    """Test that the hand's sorted shape does NOT match a pattern.

    Used to exclude specific shapes, e.g. 4-3-3-3 from Stayman
    (too flat to benefit from finding a 4-4 major fit).

    Example::

        ShapeNot((4, 3, 3, 3))
    """

    def __init__(self, pattern: tuple[int, ...]) -> None:
        self._pattern = pattern

    @property
    def label(self) -> str:
        shape_str = "-".join(str(n) for n in self._pattern)
        return f"not {shape_str} shape"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        shape_str = "-".join(str(n) for n in ctx.sorted_shape)
        pattern_str = "-".join(str(n) for n in self._pattern)
        if ctx.sorted_shape != self._pattern:
            return ConditionResult(
                passed=True,
                label=self.label,
                detail=f"Shape {shape_str} (not {pattern_str})",
            )
        return ConditionResult(
            passed=False,
            label=self.label,
            detail=f"Shape {shape_str} (is {pattern_str})",
        )


class SuitLength(Condition):
    """Test whether a specific suit has a length within a range.

    Examples::

        SuitLength(Suit.HEARTS, min_len=4)       # 4+ hearts
        SuitLength(Suit.SPADES, min_len=5, max_len=7)  # 5-7 spades
    """

    def __init__(
        self,
        suit: Suit,
        min_len: int | None = None,
        max_len: int | None = None,
    ) -> None:
        self._suit = suit
        self._min = min_len
        self._max = max_len

    @property
    def label(self) -> str:
        suit_name = self._suit.letter
        if self._min is not None and self._max is not None:
            return f"{self._min}-{self._max} {suit_name}"
        if self._min is not None:
            return f"{self._min}+ {suit_name}"
        if self._max is not None:
            return f"0-{self._max} {suit_name}"
        return f"any {suit_name}"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        length = ctx.hand.suit_length(self._suit)
        suit_name = self._suit.letter
        passed = True
        if self._min is not None and length < self._min:
            passed = False
        if self._max is not None and length > self._max:
            passed = False
        if passed:
            detail = f"{length} {suit_name} ({self.label})"
        else:
            detail = f"{length} {suit_name} (need {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class HasSuitFit(Condition):
    """Test whether the hand has enough cards in a dynamically-determined suit.

    The suit is extracted from the auction context via ``suit_fn`` — typically
    the opener's suit.  This is for checking trump support (e.g. "3+ cards
    in partner's major").

    Example::

        HasSuitFit(suit_fn=_opener_suit, min_len=3)
    """

    def __init__(
        self,
        suit_fn: Callable[[BiddingContext], Suit],
        min_len: int,
        max_len: int | None = None,
    ) -> None:
        self._suit_fn = suit_fn
        self._min_len = min_len
        self._max_len = max_len

    @property
    def label(self) -> str:
        if self._max_len is not None and self._max_len == self._min_len:
            return f"exactly {self._min_len}-card fit"
        if self._max_len is not None:
            return f"{self._min_len}-{self._max_len} card fit"
        return f"{self._min_len}+ card fit"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        suit = self._suit_fn(ctx)
        length = ctx.hand.suit_length(suit)
        passed = length >= self._min_len
        if self._max_len is not None:
            passed = passed and length <= self._max_len
        suit_name = suit.letter
        if passed:
            detail = f"{length} {suit_name} ({self.label})"
        else:
            detail = f"{length} {suit_name} (need {self.label})"
        return ConditionResult(passed=passed, label=self.label, detail=detail)


class MeetsOpeningStrength(Condition):
    """Test whether the hand meets opening strength requirements.

    Seat-dependent logic:
    - 1st/2nd/3rd seat: 12+ HCP or Rule of 20 (HCP + two longest >= 20)
    - 4th seat: 13+ HCP (clear opener) or Rule of 15 for borderline hands
    """

    @property
    def label(self) -> str:
        return "opening strength"

    def check(self, ctx: BiddingContext) -> ConditionResult:
        # Determine seat position relative to dealer
        seat_offset = (ctx.seat.value - ctx.auction.dealer.value) % 4
        if seat_offset == 3:
            # 4th seat: 13+ HCP opens regardless; borderline uses Rule of 15
            if ctx.hcp >= 13:
                passed = True
                detail = f"{ctx.hcp} HCP (13+ opens in any seat)"
            else:
                passed = evaluate.rule_of_15(ctx.hand, ctx.hcp)
                spades = ctx.hand.suit_length(Suit.SPADES)
                total = ctx.hcp + spades
                detail = (
                    f"Rule of 15: {ctx.hcp} HCP + {spades} spades"
                    f" = {total} ({'15+ required' if passed else 'need 15+'})"
                )
        else:
            # 1st/2nd/3rd seat: 12+ HCP or Rule of 20
            if ctx.hcp >= 12:
                passed = True
                detail = f"{ctx.hcp} HCP (12+ for opening)"
            else:
                lengths = sorted(ctx.shape, reverse=True)
                total = ctx.hcp + lengths[0] + lengths[1]
                passed = evaluate.rule_of_20(ctx.hand, ctx.hcp)
                if passed:
                    detail = (
                        f"Rule of 20: {ctx.hcp} HCP + {lengths[0]}"
                        f" + {lengths[1]} = {total} (20+ required)"
                    )
                else:
                    detail = (
                        f"{ctx.hcp} HCP (need 12+) and Rule of 20: {total} (need 20+)"
                    )
        return ConditionResult(passed=passed, label=self.label, detail=detail)
