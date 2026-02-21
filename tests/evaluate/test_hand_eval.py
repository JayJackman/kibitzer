"""Tests for hand evaluation functions."""

from bridge.evaluate import (
    controls,
    distribution_points,
    hcp,
    length_points,
    losing_trick_count,
    quick_tricks,
    total_points,
)
from bridge.model.card import Suit
from bridge.model.hand import Hand

# Reusable test hands (pre-parsed at module level)
# S:AKJ52 H:KQ3 D:84 C:A73 — shape 5-3-2-3, HCP 17
BALANCED = Hand.from_pbn("AKJ52.KQ3.84.A73")
# S:87654 H:432 D:T98 C:65 — shape 5-3-3-2, HCP 0
YARBOROUGH = Hand.from_pbn("87654.432.T98.65")
# S:AKQJ H:AKQ D:AKQ C:A32 — shape 4-3-3-3, HCP 32
MONSTER = Hand.from_pbn("AKQJ.AKQ.AKQ.A32")
# S:AKQJ5 H:KQJT9 D:- C:A32 — shape 5-5-0-3, HCP 19
VOID_HAND = Hand.from_pbn("AKQJ5.KQJT9..A32")
# S:T987 H:J654 D:Q32 C:K8 — shape 4-4-3-2, HCP 6
FLAT_WEAK = Hand.from_pbn("T987.J654.Q32.K8")


class TestHcp:
    def test_balanced(self) -> None:
        # A(4)+K(3)+J(1) + K(3)+Q(2) + 0 + A(4) = 17
        assert hcp(BALANCED) == 17

    def test_yarborough(self) -> None:
        assert hcp(YARBOROUGH) == 0

    def test_monster(self) -> None:
        # S: A+K+Q+J=10, H: A+K+Q=9, D: A+K+Q=9, C: A=4 → 32
        assert hcp(MONSTER) == 32

    def test_flat_weak(self) -> None:
        # S: 0, H: J=1, D: Q=2, C: K=3 → 6
        assert hcp(FLAT_WEAK) == 6

    def test_void_hand(self) -> None:
        # S: A+K+Q+J=10, H: K+Q+J=6, D: 0, C: A=4 → 20
        assert hcp(VOID_HAND) == 20


class TestLengthPoints:
    def test_balanced(self) -> None:
        # 5-card spade suit: 5-4 = 1
        assert length_points(BALANCED) == 1

    def test_yarborough(self) -> None:
        # 5-card spade suit: 5-4 = 1
        assert length_points(YARBOROUGH) == 1

    def test_monster_flat(self) -> None:
        # 4-3-3-3, no suit beyond 4
        assert length_points(MONSTER) == 0

    def test_void_hand(self) -> None:
        # Two 5-card suits: (5-4) + (5-4) = 2
        assert length_points(VOID_HAND) == 2

    def test_very_long_suit(self) -> None:
        # S:AKQJT98765 H:- D:- C:432 — 10-card spade suit
        hand = Hand.from_pbn("AKQJT98765...432")
        assert length_points(hand) == 6  # 10 - 4 = 6


class TestTotalPoints:
    def test_balanced(self) -> None:
        assert total_points(BALANCED) == 18  # 17 + 1

    def test_yarborough(self) -> None:
        assert total_points(YARBOROUGH) == 1  # 0 + 1

    def test_monster_flat(self) -> None:
        assert total_points(MONSTER) == 32  # 32 + 0


class TestDistributionPoints:
    def test_balanced(self) -> None:
        # doubleton D = 1
        assert distribution_points(BALANCED) == 1

    def test_monster_flat(self) -> None:
        # 4-3-3-3, no shortness
        assert distribution_points(MONSTER) == 0

    def test_void_hand(self) -> None:
        # void D = 5
        assert distribution_points(VOID_HAND) == 5

    def test_singleton_and_doubleton(self) -> None:
        # S:AKQ32 H:AKQJ2 D:K C:A7 — shape 5-5-1-2
        hand = Hand.from_pbn("AKQ32.AKQJ2.K.A7")
        # singleton D=3, doubleton C=1 → 4
        assert distribution_points(hand) == 4

    def test_yarborough(self) -> None:
        # 5-3-3-2, doubleton C = 1
        assert distribution_points(YARBOROUGH) == 1

    def test_multiple_voids(self) -> None:
        # S:AKQJT98765 H:- D:- C:432 — two voids
        hand = Hand.from_pbn("AKQJT98765...432")
        # void H=5, void D=5 → 10
        assert distribution_points(hand) == 10

    def test_trump_suit_excluded(self) -> None:
        # S:AKQ32 H:AKQJ2 D:K C:A7 — shape 5-5-1-2
        hand = Hand.from_pbn("AKQ32.AKQJ2.K.A7")
        # Without trump: singleton D=3, doubleton C=1 → 4
        assert distribution_points(hand) == 4
        # Raising hearts: skip H, count S(0)+D(3)+C(1) = 4 (same here)
        assert distribution_points(hand, trump_suit=Suit.HEARTS) == 4
        # Raising diamonds: skip D (the singleton!), count S(0)+H(0)+C(1) = 1
        assert distribution_points(hand, trump_suit=Suit.DIAMONDS) == 1


class TestControls:
    def test_balanced(self) -> None:
        # Aces: SA, CA = 2*2=4. Kings: SK, HK = 2*1=2. Total=6
        assert controls(BALANCED) == 6

    def test_yarborough(self) -> None:
        assert controls(YARBOROUGH) == 0

    def test_monster(self) -> None:
        # 4 aces (4*2=8) + 3 kings (3*1=3) = 11
        assert controls(MONSTER) == 11

    def test_max_controls(self) -> None:
        # 4 aces + 4 kings + 5 others
        hand = Hand.from_pbn("AK32.AK32.AK3.AK")
        # 4*2 + 4*1 = 12
        assert controls(hand) == 12


class TestQuickTricks:
    def test_balanced(self) -> None:
        # S: AK=2.0, H: KQ=1.0, D: none=0, C: A=1.0 → 4.0
        assert quick_tricks(BALANCED) == 4.0

    def test_yarborough(self) -> None:
        assert quick_tricks(YARBOROUGH) == 0.0

    def test_monster(self) -> None:
        # S: AK=2.0, H: AK=2.0, D: AK=2.0, C: A=1.0 → 7.0
        assert quick_tricks(MONSTER) == 7.0

    def test_aq_suit(self) -> None:
        # S:AQ543 H:K32 D:Q87 C:K6 — shape 5-3-3-2
        hand = Hand.from_pbn("AQ543.K32.Q87.K6")
        # S: AQ=1.5, H: Kx=0.5, D: Q alone=0, C: Kx=0.5 → 2.5
        assert quick_tricks(hand) == 2.5

    def test_singleton_king_no_quick_trick(self) -> None:
        # S:K H:AQJ54 D:KQ32 C:A73 — singleton K in spades
        hand = Hand.from_pbn("K.AQJ54.KQ32.A73")
        # S: singleton K, length=1 < 2, so 0
        # H: AQ=1.5, D: KQ=1.0, C: A=1.0 → 3.5
        assert quick_tricks(hand) == 3.5

    def test_protected_king(self) -> None:
        # S:K5 H:AQJ43 D:KQ32 C:A7 — Kx in spades
        hand = Hand.from_pbn("K5.AQJ43.KQ32.A7")
        # S: Kx (length=2, no Q)=0.5
        # H: AQ=1.5, D: KQ=1.0, C: A=1.0 → 4.0
        assert quick_tricks(hand) == 4.0


class TestLosingTrickCount:
    def test_balanced(self) -> None:
        # S: AKJ52 (3+, has A+K, no Q) = 1 loser
        # H: KQ3 (3+, has K+Q, no A) = 1 loser
        # D: 84 (doubleton, no honors) = 2 losers
        # C: A73 (3+, has A only) = 2 losers → 6
        assert losing_trick_count(BALANCED) == 6

    def test_yarborough(self) -> None:
        # S: 87654 (3+, no honors) = 3
        # H: 432 (3+, no honors) = 3
        # D: T98 (3+, no honors) = 3
        # C: 65 (doubleton, no honors) = 2 → 11
        assert losing_trick_count(YARBOROUGH) == 11

    def test_monster(self) -> None:
        # S: AKQJ (3+, A+K+Q) = 0
        # H: AKQ (3+, A+K+Q) = 0
        # D: AKQ (3+, A+K+Q) = 0
        # C: A32 (3+, A only) = 2 → 2
        assert losing_trick_count(MONSTER) == 2

    def test_void(self) -> None:
        # S: AKQJ5 (3+, A+K+Q) = 0
        # H: KQJT9 (3+, K+Q, no A) = 1
        # D: void = 0
        # C: A32 (3+, A only) = 2 → 3
        assert losing_trick_count(VOID_HAND) == 3

    def test_singleton_ace(self) -> None:
        # S:A H:KQJ54 D:AKQ32 C:73
        hand = Hand.from_pbn("A.KQJ54.AKQ32.73")
        # S: singleton A = 0
        # H: KQJ54, K+Q no A = 1
        # D: AKQ32, A+K+Q = 0
        # C: 73, doubleton, no honors = 2 → 3
        assert losing_trick_count(hand) == 3

    def test_singleton_non_ace(self) -> None:
        # S:K H:AQJ54 D:KQ32 C:A73
        hand = Hand.from_pbn("K.AQJ54.KQ32.A73")
        # S: singleton K = 1
        # H: AQJ54, A+Q no K = 1
        # D: KQ32, K+Q no A = 1
        # C: A73, A only = 2 → 5
        assert losing_trick_count(hand) == 5

    def test_doubleton_ak(self) -> None:
        # S:AK H:QJT54 D:KQ32 C:A7
        hand = Hand.from_pbn("AK.QJT54.KQ32.A7")
        # S: doubleton AK = 0
        # H: QJT54 (3+, Q only) = 2
        # D: KQ32, K+Q no A = 1
        # C: A7, doubleton, has A = 1 → 4
        assert losing_trick_count(hand) == 4

    def test_flat_weak(self) -> None:
        # S: T987 (3+, no honors) = 3
        # H: J654 (3+, no A/K/Q) = 3
        # D: Q32 (3+, Q only) = 2
        # C: K8 (doubleton, has K) = 1 → 9
        assert losing_trick_count(FLAT_WEAK) == 9
