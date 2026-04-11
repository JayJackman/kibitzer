"""Tests for the deal scoring calculator.

Every test references the scoring table in research/08-rubber-scoring.md.
"""

from __future__ import annotations

from bridge.model.card import Suit
from bridge.scoring.calculator import DealScore, score_deal

# ---------------------------------------------------------------------------
# Contract points (below the line)
# ---------------------------------------------------------------------------


class TestContractPoints:
    """Only tricks bid and made count below the line."""

    def test_minor_suit(self) -> None:
        # 3C made exactly = 20 * 3 = 60
        s = score_deal(3, Suit.CLUBS, tricks_taken=9)
        assert s.contract_points == 60

    def test_major_suit(self) -> None:
        # 4S made exactly = 30 * 4 = 120
        s = score_deal(4, Suit.SPADES, tricks_taken=10)
        assert s.contract_points == 120

    def test_notrump_first_trick_is_40(self) -> None:
        # 1NT = 40
        s = score_deal(1, Suit.NOTRUMP, tricks_taken=7)
        assert s.contract_points == 40

    def test_notrump_3nt_is_game(self) -> None:
        # 3NT = 40 + 30 + 30 = 100
        s = score_deal(3, Suit.NOTRUMP, tricks_taken=9)
        assert s.contract_points == 100

    def test_doubled_minor(self) -> None:
        # 2D doubled = 20 * 2 * 2 = 80
        s = score_deal(2, Suit.DIAMONDS, doubled=True, tricks_taken=8)
        assert s.contract_points == 80

    def test_doubled_major_is_game(self) -> None:
        # 2H doubled = 30 * 2 * 2 = 120
        s = score_deal(2, Suit.HEARTS, doubled=True, tricks_taken=8)
        assert s.contract_points == 120

    def test_redoubled_minor(self) -> None:
        # 1C redoubled = 20 * 1 * 4 = 80
        s = score_deal(1, Suit.CLUBS, redoubled=True, tricks_taken=7)
        assert s.contract_points == 80

    def test_redoubled_nt_is_game(self) -> None:
        # 1NT redoubled = 40 * 4 = 160
        s = score_deal(1, Suit.NOTRUMP, redoubled=True, tricks_taken=7)
        assert s.contract_points == 160

    def test_5c_is_game(self) -> None:
        # 5C = 20 * 5 = 100
        s = score_deal(5, Suit.CLUBS, tricks_taken=11)
        assert s.contract_points == 100

    def test_5d_is_game(self) -> None:
        # 5D = 20 * 5 = 100
        s = score_deal(5, Suit.DIAMONDS, tricks_taken=11)
        assert s.contract_points == 100


# ---------------------------------------------------------------------------
# Overtricks (above the line for declarer side)
# ---------------------------------------------------------------------------


class TestOvertricks:
    """Undoubled overtricks = denomination value. Doubled/redoubled are flat."""

    def test_undoubled_minor_overtrick(self) -> None:
        # 2C + 1 overtrick = 20 above
        s = score_deal(2, Suit.CLUBS, tricks_taken=9)
        assert s.overtrick_points == 20

    def test_undoubled_major_overtrick(self) -> None:
        # 3H + 2 overtricks = 30 * 2 = 60
        s = score_deal(3, Suit.HEARTS, tricks_taken=11)
        assert s.overtrick_points == 60

    def test_undoubled_nt_overtrick(self) -> None:
        # 1NT + 3 overtricks = 30 * 3 = 90
        s = score_deal(1, Suit.NOTRUMP, tricks_taken=10)
        assert s.overtrick_points == 90

    def test_doubled_nv_overtrick(self) -> None:
        # Doubled, not vulnerable: 100 per overtrick
        s = score_deal(2, Suit.SPADES, doubled=True, tricks_taken=10)
        assert s.overtrick_points == 200  # 2 overtricks * 100

    def test_doubled_v_overtrick(self) -> None:
        # Doubled, vulnerable: 200 per overtrick
        s = score_deal(
            2, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=10
        )
        assert s.overtrick_points == 400  # 2 * 200

    def test_redoubled_nv_overtrick(self) -> None:
        # Redoubled, not vulnerable: 200 per overtrick
        s = score_deal(1, Suit.HEARTS, redoubled=True, tricks_taken=9)
        assert s.overtrick_points == 400  # 2 * 200

    def test_redoubled_v_overtrick(self) -> None:
        # Redoubled, vulnerable: 400 per overtrick
        s = score_deal(
            1, Suit.HEARTS, redoubled=True, declarer_vulnerable=True, tricks_taken=8
        )
        assert s.overtrick_points == 400  # 1 * 400

    def test_no_overtricks(self) -> None:
        s = score_deal(4, Suit.SPADES, tricks_taken=10)
        assert s.overtrick_points == 0


# ---------------------------------------------------------------------------
# Undertrick penalties (above the line for defending side)
# ---------------------------------------------------------------------------


class TestUndertricks:
    """Undoubled = flat per trick. Doubled escalates. Redoubled = 2x doubled."""

    # -- Undoubled --

    def test_undoubled_nv_down_1(self) -> None:
        s = score_deal(4, Suit.SPADES, tricks_taken=9)
        assert s.undertrick_points == 50
        assert not s.made

    def test_undoubled_v_down_1(self) -> None:
        s = score_deal(4, Suit.SPADES, declarer_vulnerable=True, tricks_taken=9)
        assert s.undertrick_points == 100

    def test_undoubled_nv_down_3(self) -> None:
        s = score_deal(4, Suit.SPADES, tricks_taken=7)
        assert s.undertrick_points == 150  # 3 * 50

    def test_undoubled_v_down_5(self) -> None:
        s = score_deal(4, Suit.SPADES, declarer_vulnerable=True, tricks_taken=5)
        assert s.undertrick_points == 500  # 5 * 100

    # -- Doubled, not vulnerable --
    # Cumulative: 1=100, 2=300, 3=500, 4=800, 5=1100, 6=1400, 7=1700

    def test_doubled_nv_down_1(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=9)
        assert s.undertrick_points == 100

    def test_doubled_nv_down_2(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=8)
        assert s.undertrick_points == 300

    def test_doubled_nv_down_3(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=7)
        assert s.undertrick_points == 500

    def test_doubled_nv_down_4(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=6)
        assert s.undertrick_points == 800

    def test_doubled_nv_down_5(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=5)
        assert s.undertrick_points == 1100

    def test_doubled_nv_down_7(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=3)
        assert s.undertrick_points == 1700

    # -- Doubled, vulnerable --
    # Cumulative: 1=200, 2=500, 3=800, 4=1100, 5=1400, 6=1700, 7=2000

    def test_doubled_v_down_1(self) -> None:
        s = score_deal(
            4, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=9
        )
        assert s.undertrick_points == 200

    def test_doubled_v_down_2(self) -> None:
        s = score_deal(
            4, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=8
        )
        assert s.undertrick_points == 500

    def test_doubled_v_down_3(self) -> None:
        s = score_deal(
            4, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=7
        )
        assert s.undertrick_points == 800

    def test_doubled_v_down_4(self) -> None:
        s = score_deal(
            4, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=6
        )
        assert s.undertrick_points == 1100

    def test_doubled_v_down_7(self) -> None:
        s = score_deal(
            4, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=3
        )
        assert s.undertrick_points == 2000

    # -- Redoubled = 2x doubled --

    def test_redoubled_nv_down_1(self) -> None:
        s = score_deal(4, Suit.SPADES, redoubled=True, tricks_taken=9)
        assert s.undertrick_points == 200

    def test_redoubled_nv_down_3(self) -> None:
        s = score_deal(4, Suit.SPADES, redoubled=True, tricks_taken=7)
        assert s.undertrick_points == 1000

    def test_redoubled_v_down_1(self) -> None:
        s = score_deal(
            4, Suit.SPADES, redoubled=True, declarer_vulnerable=True, tricks_taken=9
        )
        assert s.undertrick_points == 400

    def test_redoubled_v_down_3(self) -> None:
        s = score_deal(
            4, Suit.SPADES, redoubled=True, declarer_vulnerable=True, tricks_taken=7
        )
        assert s.undertrick_points == 1600

    def test_redoubled_v_down_7(self) -> None:
        s = score_deal(
            4, Suit.SPADES, redoubled=True, declarer_vulnerable=True, tricks_taken=3
        )
        assert s.undertrick_points == 4000


# ---------------------------------------------------------------------------
# Slam bonuses
# ---------------------------------------------------------------------------


class TestSlamBonus:
    """Must bid at 6 or 7 level to earn the bonus."""

    def test_small_slam_nv(self) -> None:
        s = score_deal(6, Suit.HEARTS, tricks_taken=12)
        assert s.slam_bonus == 500

    def test_small_slam_v(self) -> None:
        s = score_deal(6, Suit.HEARTS, declarer_vulnerable=True, tricks_taken=12)
        assert s.slam_bonus == 750

    def test_grand_slam_nv(self) -> None:
        s = score_deal(7, Suit.NOTRUMP, tricks_taken=13)
        assert s.slam_bonus == 1000

    def test_grand_slam_v(self) -> None:
        s = score_deal(7, Suit.CLUBS, declarer_vulnerable=True, tricks_taken=13)
        assert s.slam_bonus == 1500

    def test_no_bonus_below_6(self) -> None:
        # Making 12 tricks on a 4-level contract: no slam bonus.
        s = score_deal(4, Suit.SPADES, tricks_taken=12)
        assert s.slam_bonus == 0
        assert s.overtrick_points == 30 * 2  # 2 overtricks at major value

    def test_slam_defeated_no_bonus(self) -> None:
        # Bid 6H but made only 11 tricks: down 1, no slam bonus.
        s = score_deal(6, Suit.HEARTS, tricks_taken=11)
        assert s.slam_bonus == 0
        assert not s.made


# ---------------------------------------------------------------------------
# Insult bonus (making doubled/redoubled)
# ---------------------------------------------------------------------------


class TestInsultBonus:
    def test_undoubled_no_insult(self) -> None:
        s = score_deal(3, Suit.NOTRUMP, tricks_taken=9)
        assert s.insult_bonus == 0

    def test_doubled_made(self) -> None:
        s = score_deal(2, Suit.HEARTS, doubled=True, tricks_taken=8)
        assert s.insult_bonus == 50

    def test_redoubled_made(self) -> None:
        s = score_deal(1, Suit.NOTRUMP, redoubled=True, tricks_taken=7)
        assert s.insult_bonus == 100

    def test_doubled_defeated_no_insult(self) -> None:
        s = score_deal(4, Suit.SPADES, doubled=True, tricks_taken=9)
        assert s.insult_bonus == 0


# ---------------------------------------------------------------------------
# Made vs defeated flag
# ---------------------------------------------------------------------------


class TestMadeFlag:
    def test_made_exactly(self) -> None:
        assert score_deal(4, Suit.SPADES, tricks_taken=10).made is True

    def test_made_with_overtricks(self) -> None:
        assert score_deal(2, Suit.CLUBS, tricks_taken=11).made is True

    def test_down_1(self) -> None:
        assert score_deal(4, Suit.SPADES, tricks_taken=9).made is False

    def test_down_many(self) -> None:
        assert score_deal(7, Suit.NOTRUMP, tricks_taken=0).made is False


# ---------------------------------------------------------------------------
# Full deal scenarios (verify all fields together)
# ---------------------------------------------------------------------------


class TestFullScenarios:
    def test_3nt_made_exactly_nv(self) -> None:
        """3NT made 9 tricks, not vulnerable."""
        s = score_deal(3, Suit.NOTRUMP, tricks_taken=9)
        assert s == DealScore(
            contract_points=100,
            overtrick_points=0,
            undertrick_points=0,
            slam_bonus=0,
            insult_bonus=0,
            made=True,
        )

    def test_4s_doubled_making_5_vulnerable(self) -> None:
        """4S doubled, vulnerable, making 11 tricks (1 overtrick)."""
        s = score_deal(
            4, Suit.SPADES, doubled=True, declarer_vulnerable=True, tricks_taken=11
        )
        assert s == DealScore(
            contract_points=240,  # 30 * 4 * 2
            overtrick_points=200,  # 1 * 200 (doubled, vulnerable)
            undertrick_points=0,
            slam_bonus=0,
            insult_bonus=50,
            made=True,
        )

    def test_6h_making_12_vulnerable(self) -> None:
        """6H vulnerable, making exactly 12 tricks."""
        s = score_deal(6, Suit.HEARTS, declarer_vulnerable=True, tricks_taken=12)
        assert s == DealScore(
            contract_points=180,  # 30 * 6
            overtrick_points=0,
            undertrick_points=0,
            slam_bonus=750,
            insult_bonus=0,
            made=True,
        )

    def test_7nt_redoubled_making_13_nv(self) -> None:
        """7NT redoubled, not vulnerable, all 13 tricks."""
        s = score_deal(7, Suit.NOTRUMP, redoubled=True, tricks_taken=13)
        assert s == DealScore(
            contract_points=880,  # (40 + 30*6) * 4
            overtrick_points=0,
            undertrick_points=0,
            slam_bonus=1000,
            insult_bonus=100,
            made=True,
        )

    def test_1nt_redoubled_making_13_v(self) -> None:
        """1NT redoubled, vulnerable, all 13 tricks (extreme)."""
        s = score_deal(
            1, Suit.NOTRUMP, redoubled=True, declarer_vulnerable=True, tricks_taken=13
        )
        assert s == DealScore(
            contract_points=160,  # 40 * 4
            overtrick_points=2400,  # 6 * 400 (redoubled, vulnerable)
            undertrick_points=0,
            slam_bonus=0,  # Only bid 1, not slam level
            insult_bonus=100,
            made=True,
        )

    def test_7s_doubled_down_7_nv(self) -> None:
        """7S doubled, not vulnerable, down 7 (only 6 tricks)."""
        s = score_deal(7, Suit.SPADES, doubled=True, tricks_taken=6)
        assert s == DealScore(
            contract_points=0,
            overtrick_points=0,
            undertrick_points=1700,
            slam_bonus=0,
            insult_bonus=0,
            made=False,
        )

    def test_passed_out_equivalent_1c_down_7(self) -> None:
        """1C, 0 tricks taken -- down 7 undoubled NV."""
        s = score_deal(1, Suit.CLUBS, tricks_taken=0)
        assert s.undertrick_points == 350  # 7 * 50
        assert not s.made
