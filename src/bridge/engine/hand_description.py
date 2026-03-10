"""Hand description types for the rule-promises system.

A HandDescription captures what we know (or can infer) about a hand from
the auction. Each dimension uses optional min/max bounds -- None means
unconstrained on that side.

Two descriptions combine in two ways:
- **intersect**: tighten bounds (both constraints hold). Used when
  accumulating knowledge across successive bids by the same player.
- **union**: widen bounds (weakest guarantee across candidates). Used
  when multiple rules could have produced the same bid and we don't
  know which one fired.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from bridge.model.card import Suit

logger = logging.getLogger(__name__)

# A single range bound: (min, max). None = unconstrained on that side.
Bound = tuple[int | None, int | None]

UNBOUNDED: Bound = (None, None)

# Suit lengths keyed by Suit enum. Missing keys are implicitly UNBOUNDED.
SuitLengths = dict[Suit, Bound]


@dataclass(frozen=True)
class HandDescription:
    """What we know about a hand from the auction.

    Each field is a Bound (min, max) or a dict of per-suit bounds.
    UNBOUNDED / empty dict = no information on that dimension.
    """

    hcp: Bound = UNBOUNDED
    total_pts: Bound = UNBOUNDED
    lengths: SuitLengths = field(default_factory=dict)
    balanced: bool | None = None

    def intersect(self, other: HandDescription) -> HandDescription:
        """Tighten: combine two descriptions where both must hold."""
        return HandDescription(
            hcp=_intersect_bounds(self.hcp, other.hcp),
            total_pts=_intersect_bounds(self.total_pts, other.total_pts),
            lengths=_intersect_lengths(self.lengths, other.lengths),
            balanced=_intersect_balanced(self.balanced, other.balanced),
        )

    def union(self, other: HandDescription) -> HandDescription:
        """Widen: keep only what every candidate guarantees."""
        return HandDescription(
            hcp=_union_bounds(self.hcp, other.hcp),
            total_pts=_union_bounds(self.total_pts, other.total_pts),
            lengths=_union_lengths(self.lengths, other.lengths),
            balanced=_union_balanced(self.balanced, other.balanced),
        )

    def negated(self) -> HandDescription:
        """Negate each bound: useful for Not.promises().

        One-sided bounds invert cleanly (e.g. "5+ Hearts" -> "0-4 Hearts").
        Two-sided bounds (e.g. "15-17 HCP") can't be expressed as a single
        range, so they become unconstrained.
        """
        new_lengths: SuitLengths = {}
        for suit, bound in self.lengths.items():
            neg = _negate_bound(bound)
            if neg != UNBOUNDED:
                new_lengths[suit] = neg

        neg_balanced: bool | None = None
        if self.balanced is True:
            neg_balanced = False
        elif self.balanced is False:
            neg_balanced = True

        return HandDescription(
            hcp=_negate_bound(self.hcp),
            total_pts=_negate_bound(self.total_pts),
            lengths=new_lengths,
            balanced=neg_balanced,
        )

    def __and__(self, other: HandDescription) -> HandDescription:
        return self.intersect(other)

    def __or__(self, other: HandDescription) -> HandDescription:
        return self.union(other)


def _negate_bound(bound: Bound) -> Bound:
    """Negate a bound by flipping the open side.

    One-sided bounds invert cleanly:
      (5, None)    "5+"   -> (None, 4)  "0-4"
      (None, 7)    "0-7"  -> (8, None)  "8+"

    Two-sided bounds and unconstrained bounds stay unconstrained:
      (15, 17)     "15-17" -> (None, None)  can't express as single range
      (None, None) "any"   -> (None, None)  still any
    """
    lo, hi = bound
    if lo is not None and hi is not None:
        return UNBOUNDED
    if lo is None and hi is None:
        return UNBOUNDED
    if lo is not None:
        return (None, lo - 1)
    assert hi is not None
    return (hi + 1, None)


def _intersect_bounds(a: Bound, b: Bound) -> Bound:
    """Tighten two bounds: raise min, lower max."""
    a_min, a_max = a
    b_min, b_max = b

    if a_min is None:
        lo = b_min
    elif b_min is None:
        lo = a_min
    else:
        lo = max(a_min, b_min)

    if a_max is None:
        hi = b_max
    elif b_max is None:
        hi = a_max
    else:
        hi = min(a_max, b_max)

    return (lo, hi)


def _union_bounds(a: Bound, b: Bound) -> Bound:
    """Widen two bounds: lower min, raise max."""
    a_min, a_max = a
    b_min, b_max = b

    lo = None if a_min is None or b_min is None else min(a_min, b_min)
    hi = None if a_max is None or b_max is None else max(a_max, b_max)

    return (lo, hi)


def _intersect_lengths(a: SuitLengths, b: SuitLengths) -> SuitLengths:
    """Intersect per-suit length bounds. Missing keys are UNBOUNDED."""
    all_suits = a.keys() | b.keys()
    result: SuitLengths = {}
    for suit in all_suits:
        merged = _intersect_bounds(a.get(suit, UNBOUNDED), b.get(suit, UNBOUNDED))
        if merged != UNBOUNDED:
            result[suit] = merged
    return result


def _union_lengths(a: SuitLengths, b: SuitLengths) -> SuitLengths:
    """Union per-suit length bounds. Missing keys are UNBOUNDED."""
    # A suit only in one dict unions with UNBOUNDED -> UNBOUNDED (dropped).
    common_suits = a.keys() & b.keys()
    result: SuitLengths = {}
    for suit in common_suits:
        merged = _union_bounds(a[suit], b[suit])
        if merged != UNBOUNDED:
            result[suit] = merged
    return result


def _intersect_balanced(a: bool | None, b: bool | None) -> bool | None:
    """Intersect balanced flags. Both must hold if set."""
    if a is None:
        return b
    if b is None:
        return a
    if a != b:
        logger.warning("Contradictory balanced intersection: %s vs %s", a, b)
    return a and b


def _union_balanced(a: bool | None, b: bool | None) -> bool | None:
    """Union balanced flags. Keep only if both candidates agree."""
    if a is None or b is None:
        return None
    if a == b:
        return a
    return None
