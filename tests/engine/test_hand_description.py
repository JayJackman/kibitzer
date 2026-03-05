"""Tests for HandDescription and bound operations."""

import logging

import pytest

from bridge.engine.hand_description import (
    UNBOUNDED,
    HandDescription,
)
from bridge.engine.hand_description import (
    _intersect_bounds as intersect_bounds,
)
from bridge.engine.hand_description import (
    _union_bounds as union_bounds,
)
from bridge.model.card import Suit


class TestIntersectBounds:
    def test_both_unbounded(self) -> None:
        assert intersect_bounds(UNBOUNDED, UNBOUNDED) == UNBOUNDED

    def test_one_unbounded(self) -> None:
        assert intersect_bounds((10, 14), UNBOUNDED) == (10, 14)
        assert intersect_bounds(UNBOUNDED, (10, 14)) == (10, 14)

    def test_tightens_min(self) -> None:
        assert intersect_bounds((5, 14), (10, 18)) == (10, 14)

    def test_tightens_max(self) -> None:
        assert intersect_bounds((5, 18), (5, 14)) == (5, 14)

    def test_tightens_both(self) -> None:
        assert intersect_bounds((5, 18), (10, 14)) == (10, 14)

    def test_open_min(self) -> None:
        assert intersect_bounds((None, 14), (10, None)) == (10, 14)

    def test_open_max(self) -> None:
        assert intersect_bounds((10, None), (5, None)) == (10, None)

    def test_contradictory_produces_inverted(self) -> None:
        # min > max: the caller can check for this if needed
        assert intersect_bounds((15, 17), (10, 12)) == (15, 12)


class TestUnionBounds:
    def test_both_unbounded(self) -> None:
        assert union_bounds(UNBOUNDED, UNBOUNDED) == UNBOUNDED

    def test_one_unbounded(self) -> None:
        assert union_bounds((10, 14), UNBOUNDED) == UNBOUNDED
        assert union_bounds(UNBOUNDED, (10, 14)) == UNBOUNDED

    def test_widens_min(self) -> None:
        assert union_bounds((10, 14), (5, 14)) == (5, 14)

    def test_widens_max(self) -> None:
        assert union_bounds((10, 14), (10, 18)) == (10, 18)

    def test_widens_both(self) -> None:
        assert union_bounds((10, 14), (5, 18)) == (5, 18)

    def test_open_min_stays_open(self) -> None:
        assert union_bounds((None, 14), (10, 18)) == (None, 18)

    def test_open_max_stays_open(self) -> None:
        assert union_bounds((10, None), (5, 14)) == (5, None)


class TestHandDescriptionIntersect:
    def test_empty_with_empty(self) -> None:
        a = HandDescription()
        b = HandDescription()
        assert a.intersect(b) == HandDescription()

    def test_tightens_hcp(self) -> None:
        a = HandDescription(hcp=(12, None))
        b = HandDescription(hcp=(10, 18))
        assert a.intersect(b) == HandDescription(hcp=(12, 18))

    def test_tightens_total_pts(self) -> None:
        a = HandDescription(total_pts=(None, 16))
        b = HandDescription(total_pts=(10, None))
        assert a.intersect(b) == HandDescription(total_pts=(10, 16))

    def test_intersects_suit_lengths(self) -> None:
        a = HandDescription(lengths={Suit.SPADES: (5, None)})
        b = HandDescription(lengths={Suit.SPADES: (4, 7)})
        assert a.intersect(b) == HandDescription(lengths={Suit.SPADES: (5, 7)})

    def test_intersect_disjoint_suits(self) -> None:
        a = HandDescription(lengths={Suit.SPADES: (5, None)})
        b = HandDescription(lengths={Suit.CLUBS: (4, None)})
        assert a.intersect(b) == HandDescription(
            lengths={Suit.SPADES: (5, None), Suit.CLUBS: (4, None)}
        )

    def test_intersect_balanced(self) -> None:
        a = HandDescription(balanced=True)
        b = HandDescription(balanced=None)
        assert a.intersect(b) == HandDescription(balanced=True)

    def test_intersect_balanced_disagree_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        a = HandDescription(balanced=True)
        b = HandDescription(balanced=False)
        with caplog.at_level(logging.WARNING):
            assert a.intersect(b) == HandDescription(balanced=False)
        assert "Contradictory balanced intersection" in caplog.text

    def test_full_intersection(self) -> None:
        """1S opening intersected with Q2 asking about 4S response."""
        north = HandDescription(hcp=(12, None), lengths={Suit.SPADES: (5, None)})
        response = HandDescription(hcp=(12, None), lengths={Suit.SPADES: (3, None)})
        result = north.intersect(response)
        assert result == HandDescription(
            hcp=(12, None), lengths={Suit.SPADES: (5, None)}
        )


class TestHandDescriptionUnion:
    def test_empty_with_empty(self) -> None:
        a = HandDescription()
        b = HandDescription()
        assert a.union(b) == HandDescription()

    def test_widens_hcp(self) -> None:
        a = HandDescription(hcp=(12, 14))
        b = HandDescription(hcp=(10, 18))
        assert a.union(b) == HandDescription(hcp=(10, 18))

    def test_unbounded_hcp_wins(self) -> None:
        a = HandDescription(hcp=(12, 14))
        b = HandDescription()
        assert a.union(b) == HandDescription()

    def test_union_suit_lengths_common(self) -> None:
        a = HandDescription(lengths={Suit.SPADES: (5, None)})
        b = HandDescription(lengths={Suit.SPADES: (6, None)})
        assert a.union(b) == HandDescription(lengths={Suit.SPADES: (5, None)})

    def test_union_suit_lengths_disjoint_dropped(self) -> None:
        """A suit only constrained in one candidate gets dropped."""
        a = HandDescription(lengths={Suit.SPADES: (5, None)})
        b = HandDescription(lengths={Suit.CLUBS: (4, None)})
        assert a.union(b) == HandDescription()

    def test_union_balanced_agree(self) -> None:
        a = HandDescription(balanced=True)
        b = HandDescription(balanced=True)
        assert a.union(b) == HandDescription(balanced=True)

    def test_union_balanced_disagree(self) -> None:
        a = HandDescription(balanced=True)
        b = HandDescription(balanced=False)
        assert a.union(b) == HandDescription(balanced=None)

    def test_union_balanced_one_unknown(self) -> None:
        a = HandDescription(balanced=True)
        b = HandDescription(balanced=None)
        assert a.union(b) == HandDescription(balanced=None)

    def test_rebid_union_washes_out_points(self) -> None:
        """From the end-to-end example: union of two candidates for 2S rebid.

        RebidSuitAfter2Over1 has no points constraint.
        RebidOwnSuit has total_pts=(None, 16).
        Union should wash out to UNBOUNDED.
        """
        candidate_1 = HandDescription()  # no constraints
        candidate_2 = HandDescription(total_pts=(None, 16))
        assert candidate_1.union(candidate_2) == HandDescription()


class TestOperators:
    def test_and_is_intersect(self) -> None:
        a = HandDescription(hcp=(12, None))
        b = HandDescription(hcp=(10, 18))
        assert (a & b) == a.intersect(b) == HandDescription(hcp=(12, 18))

    def test_or_is_union(self) -> None:
        a = HandDescription(hcp=(12, 14))
        b = HandDescription(hcp=(10, 18))
        assert (a | b) == a.union(b) == HandDescription(hcp=(10, 18))

    def test_chained_intersect(self) -> None:
        """Accumulate knowledge across three bids."""
        opening = HandDescription(hcp=(12, None), lengths={Suit.SPADES: (5, None)})
        rebid_pts = HandDescription(hcp=(12, 16))
        rebid_suit = HandDescription(lengths={Suit.SPADES: (6, None)})
        result = opening & rebid_pts & rebid_suit
        assert result == HandDescription(hcp=(12, 16), lengths={Suit.SPADES: (6, None)})

    def test_chained_union(self) -> None:
        """Multiple candidates for the same bid."""
        c1 = HandDescription(hcp=(12, 14))
        c2 = HandDescription(hcp=(15, 17))
        c3 = HandDescription(hcp=(10, 12))
        result = c1 | c2 | c3
        assert result == HandDescription(hcp=(10, 17))
