"""Tests for the RubberTracker state machine.

Covers game completion, part-score carryover, vulnerability tracking,
rubber completion, entry editing/insertion/removal, and auto-populate.
"""

from __future__ import annotations

import pytest

from bridge.model.auction import Contract, Seat, Vulnerability
from bridge.model.card import Suit
from bridge.scoring.rubber import RubberTracker


def _add_made(
    tracker: RubberTracker,
    level: int,
    suit: Suit,
    declarer: Seat,
    tricks: int,
    *,
    doubled: bool = False,
    redoubled: bool = False,
    position: int | None = None,
) -> int:
    """Convenience: add an entry with tricks_taken already set."""
    return tracker.add_entry(
        contract_level=level,
        contract_suit=suit,
        declarer=declarer,
        tricks_taken=tricks,
        doubled=doubled,
        redoubled=redoubled,
        position=position,
    )


# ---------------------------------------------------------------------------
# Basic scoring
# ---------------------------------------------------------------------------


class TestBasicScoring:
    def test_empty_rubber(self) -> None:
        t = RubberTracker()
        state = t.get_state()
        assert state.ns_games_won == 0
        assert state.ew_games_won == 0
        assert state.ns_above == 0
        assert state.ew_above == 0
        assert state.ns_below_current == 0
        assert state.ew_below_current == 0
        assert not state.is_complete
        assert state.entries == []
        assert state.games == []
        assert state.pending_entry_id is None

    def test_single_partscore(self) -> None:
        t = RubberTracker()
        _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8)
        state = t.get_state()
        # 2H made = 60 below the line
        assert state.ns_below_current == 60
        assert state.ew_below_current == 0
        assert state.ns_games_won == 0
        assert len(state.games) == 0

    def test_overtricks_go_above(self) -> None:
        t = RubberTracker()
        _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 10)
        state = t.get_state()
        # 2H + 2 = 60 below, 60 above (2 * 30)
        assert state.ns_below_current == 60
        assert state.ns_above == 60

    def test_undertricks_go_to_defenders(self) -> None:
        t = RubberTracker()
        _add_made(t, 4, Suit.SPADES, Seat.NORTH, 9)
        state = t.get_state()
        # Down 1, NV = 50 to EW above
        assert state.ns_below_current == 0
        assert state.ew_above == 50


# ---------------------------------------------------------------------------
# Game completion
# ---------------------------------------------------------------------------


class TestGameCompletion:
    def test_3nt_is_game(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.SOUTH, 9)
        state = t.get_state()
        assert state.ns_games_won == 1
        assert len(state.games) == 1
        assert state.games[0].ns_below == 100
        # Below-the-line resets for next game
        assert state.ns_below_current == 0

    def test_partscore_carryover(self) -> None:
        """Two partscores that together reach 100."""
        t = RubberTracker()
        _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8)  # 60
        _add_made(t, 2, Suit.CLUBS, Seat.SOUTH, 8)  # 40
        state = t.get_state()
        # 60 + 40 = 100, game!
        assert state.ns_games_won == 1
        assert state.ns_below_current == 0

    def test_both_sides_partscores(self) -> None:
        """Part-scores from both sides, NS reaches game first."""
        t = RubberTracker()
        _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8)  # NS: 60
        _add_made(t, 2, Suit.DIAMONDS, Seat.EAST, 8)  # EW: 40
        _add_made(t, 2, Suit.CLUBS, Seat.SOUTH, 8)  # NS: 60+40=100 -> game
        state = t.get_state()
        assert state.ns_games_won == 1
        assert state.ew_games_won == 0
        # EW's 40 below is wiped for the new game
        assert state.ew_below_current == 0

    def test_ew_game(self) -> None:
        t = RubberTracker()
        _add_made(t, 4, Suit.SPADES, Seat.WEST, 10)
        state = t.get_state()
        assert state.ew_games_won == 1
        assert state.ns_games_won == 0


# ---------------------------------------------------------------------------
# Vulnerability tracking
# ---------------------------------------------------------------------------


class TestVulnerability:
    def test_initially_no_one_vulnerable(self) -> None:
        t = RubberTracker()
        state = t.get_state()
        assert not state.ns_vulnerable
        assert not state.ew_vulnerable

    def test_game_winner_becomes_vulnerable(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS game
        state = t.get_state()
        assert state.ns_vulnerable
        assert not state.ew_vulnerable

    def test_vulnerability_affects_scoring(self) -> None:
        """After NS wins a game, NS undertricks cost 100 (vulnerable)."""
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS wins game 1
        _add_made(t, 4, Suit.SPADES, Seat.SOUTH, 9)  # NS down 1, vulnerable
        state = t.get_state()
        # Down 1 vulnerable = 100 to EW above
        assert state.ew_above == 100

    def test_both_vulnerable(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS wins game 1
        _add_made(t, 4, Suit.HEARTS, Seat.EAST, 10)  # EW wins game 2
        state = t.get_state()
        assert state.ns_vulnerable
        assert state.ew_vulnerable

    def test_current_vulnerability_method(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS game
        vuln = t.current_vulnerability()
        assert vuln == Vulnerability(ns_vulnerable=True, ew_vulnerable=False)


# ---------------------------------------------------------------------------
# Rubber completion
# ---------------------------------------------------------------------------


class TestRubberCompletion:
    def test_rubber_2_0(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS game 1
        _add_made(t, 4, Suit.HEARTS, Seat.SOUTH, 10)  # NS game 2
        state = t.get_state()
        assert state.is_complete
        assert state.ns_games_won == 2
        assert state.ew_games_won == 0
        assert state.rubber_bonus == 700
        # Rubber bonus added to NS above
        assert state.ns_total > state.ew_total

    def test_rubber_2_1(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS game 1
        _add_made(t, 4, Suit.SPADES, Seat.EAST, 10)  # EW game 1
        _add_made(t, 4, Suit.HEARTS, Seat.SOUTH, 10)  # NS game 2
        state = t.get_state()
        assert state.is_complete
        assert state.ns_games_won == 2
        assert state.ew_games_won == 1
        assert state.rubber_bonus == 500

    def test_ew_wins_rubber(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.EAST, 9)  # EW game 1
        _add_made(t, 4, Suit.HEARTS, Seat.WEST, 10)  # EW game 2
        state = t.get_state()
        assert state.is_complete
        assert state.ew_games_won == 2
        assert state.rubber_bonus == 700

    def test_vulnerability_off_after_rubber_complete(self) -> None:
        """Once the rubber is over, vulnerability flags are cleared."""
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)
        _add_made(t, 4, Suit.HEARTS, Seat.SOUTH, 10)
        state = t.get_state()
        assert not state.ns_vulnerable
        assert not state.ew_vulnerable

    def test_total_includes_all_games(self) -> None:
        """Grand total includes all above + below from all games."""
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS: 100 below
        _add_made(t, 4, Suit.HEARTS, Seat.SOUTH, 10)  # NS: 120 below
        state = t.get_state()
        # NS total = 100 (game1 below) + 120 (game2 below) + 700 (rubber bonus)
        assert state.ns_total == 100 + 120 + 700


# ---------------------------------------------------------------------------
# New rubber
# ---------------------------------------------------------------------------


class TestNewRubber:
    def test_new_rubber_resets(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)
        t.new_rubber()
        state = t.get_state()
        assert state.entries == []
        assert state.ns_games_won == 0
        assert state.ew_games_won == 0
        assert state.ns_total == 0


# ---------------------------------------------------------------------------
# Pending entries
# ---------------------------------------------------------------------------


class TestPendingEntries:
    def test_pending_entry_tracked(self) -> None:
        t = RubberTracker()
        eid = t.add_entry(
            contract_level=4,
            contract_suit=Suit.SPADES,
            declarer=Seat.NORTH,
        )
        state = t.get_state()
        assert state.pending_entry_id == eid
        assert state.entries[0].score is None

    def test_filling_in_tricks_clears_pending(self) -> None:
        t = RubberTracker()
        eid = t.add_entry(
            contract_level=4,
            contract_suit=Suit.SPADES,
            declarer=Seat.NORTH,
        )
        t.update_entry(
            eid,
            contract_level=4,
            contract_suit=Suit.SPADES,
            declarer=Seat.NORTH,
            doubled=False,
            redoubled=False,
            tricks_taken=10,
        )
        state = t.get_state()
        assert state.pending_entry_id is None
        assert state.entries[0].score is not None

    def test_multiple_pending_tracks_first(self) -> None:
        t = RubberTracker()
        eid1 = t.add_entry(
            contract_level=3, contract_suit=Suit.NOTRUMP, declarer=Seat.NORTH
        )
        t.add_entry(contract_level=4, contract_suit=Suit.HEARTS, declarer=Seat.EAST)
        state = t.get_state()
        assert state.pending_entry_id == eid1


# ---------------------------------------------------------------------------
# Auto-populate from Contract
# ---------------------------------------------------------------------------


class TestAutoPopulate:
    def test_auto_populate_creates_pending(self) -> None:
        t = RubberTracker()
        contract = Contract(
            level=4, suit=Suit.SPADES, declarer=Seat.NORTH, doubled=True
        )
        eid = t.auto_populate_contract(contract)
        state = t.get_state()
        assert state.pending_entry_id == eid
        entry = state.entries[0].entry
        assert entry.contract_level == 4
        assert entry.contract_suit == Suit.SPADES
        assert entry.declarer == Seat.NORTH
        assert entry.doubled is True
        assert entry.tricks_taken is None


# ---------------------------------------------------------------------------
# Entry editing
# ---------------------------------------------------------------------------


class TestEntryEditing:
    def test_update_tricks(self) -> None:
        t = RubberTracker()
        eid = _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)
        t.update_entry(
            eid,
            contract_level=3,
            contract_suit=Suit.NOTRUMP,
            declarer=Seat.NORTH,
            doubled=False,
            redoubled=False,
            tricks_taken=10,
        )
        state = t.get_state()
        # Now 3NT + 1 overtrick
        assert state.ns_above == 30  # 1 NT overtrick

    def test_update_contract(self) -> None:
        t = RubberTracker()
        eid = _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8)
        t.update_entry(
            eid,
            contract_level=3,
            contract_suit=Suit.NOTRUMP,
            declarer=Seat.NORTH,
            doubled=False,
            redoubled=False,
            tricks_taken=8,
        )
        state = t.get_state()
        # 3NT made with 8 tricks = down 1 (needs 9)
        assert not state.entries[0].score.made  # type: ignore[union-attr]

    def test_editing_recalculates_game_boundaries(self) -> None:
        """Change a part-score to a game and verify boundaries shift."""
        t = RubberTracker()
        eid = _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8)  # 60 below, no game
        assert t.get_state().ns_games_won == 0

        # Change to 4H made 10 tricks -> 120 below -> game
        t.update_entry(
            eid,
            contract_level=4,
            contract_suit=Suit.HEARTS,
            declarer=Seat.NORTH,
            doubled=False,
            redoubled=False,
            tricks_taken=10,
        )
        state = t.get_state()
        assert state.ns_games_won == 1

    def test_edit_not_found_raises(self) -> None:
        t = RubberTracker()
        with pytest.raises(KeyError):
            t.update_entry(
                999,
                contract_level=1,
                contract_suit=Suit.CLUBS,
                declarer=Seat.NORTH,
                doubled=False,
                redoubled=False,
                tricks_taken=10,
            )


# ---------------------------------------------------------------------------
# Entry insertion at arbitrary position
# ---------------------------------------------------------------------------


class TestEntryInsertion:
    def test_insert_at_beginning(self) -> None:
        t = RubberTracker()
        id1 = _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8)
        id2 = _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9, position=0)
        state = t.get_state()
        # The 3NT was inserted first, so NS should have won game 1
        assert state.entries[0].entry.id == id2
        assert state.entries[1].entry.id == id1
        # 3NT = 100 -> game, then 2H in new game = 60
        assert state.ns_games_won == 1
        assert state.ns_below_current == 60

    def test_insert_in_middle(self) -> None:
        t = RubberTracker()
        id1 = _add_made(t, 1, Suit.CLUBS, Seat.NORTH, 7)  # 20
        id3 = _add_made(t, 2, Suit.CLUBS, Seat.NORTH, 8)  # 40
        # Insert a deal between them
        id2 = _add_made(t, 2, Suit.DIAMONDS, Seat.SOUTH, 8, position=1)  # 40
        state = t.get_state()
        assert [e.entry.id for e in state.entries] == [id1, id2, id3]
        # 20 + 40 = 60, then +40 = 100 -> game
        assert state.ns_games_won == 1

    def test_insert_changes_vulnerability(self) -> None:
        """Inserting a game-winning deal changes vulnerability for later deals."""
        t = RubberTracker()
        # EW win game then NS goes down 1
        _add_made(t, 4, Suit.SPADES, Seat.NORTH, 9)  # NS down 1, NV -> 50 to EW
        state = t.get_state()
        assert state.ew_above == 50  # NV penalty

        # Now insert a NS game win before that deal
        _add_made(t, 3, Suit.NOTRUMP, Seat.SOUTH, 9, position=0)
        state = t.get_state()
        # NS won game, so when 4S down 1 is re-scored, NS is now vulnerable
        assert state.ew_above == 100  # V penalty


# ---------------------------------------------------------------------------
# Entry removal
# ---------------------------------------------------------------------------


class TestEntryRemoval:
    def test_remove_entry(self) -> None:
        t = RubberTracker()
        eid = _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)
        t.remove_entry(eid)
        state = t.get_state()
        assert state.entries == []
        assert state.ns_games_won == 0

    def test_remove_recalculates(self) -> None:
        t = RubberTracker()
        eid1 = _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # game
        _add_made(t, 4, Suit.SPADES, Seat.SOUTH, 9)  # down 1, vulnerable
        state = t.get_state()
        assert state.ew_above == 100  # V penalty

        t.remove_entry(eid1)
        state = t.get_state()
        # Without the game, NS is NV again, down 1 = 50
        assert state.ew_above == 50
        assert state.ns_games_won == 0

    def test_remove_not_found_raises(self) -> None:
        t = RubberTracker()
        with pytest.raises(KeyError):
            t.remove_entry(999)


# ---------------------------------------------------------------------------
# Slam bonus in rubber context
# ---------------------------------------------------------------------------


class TestSlamInRubber:
    def test_small_slam_nv(self) -> None:
        t = RubberTracker()
        _add_made(t, 6, Suit.HEARTS, Seat.NORTH, 12)
        state = t.get_state()
        # 6H = 180 below (game), 500 slam bonus above
        assert state.ns_games_won == 1
        assert state.ns_above == 500

    def test_grand_slam_v(self) -> None:
        t = RubberTracker()
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 9)  # NS game (now vulnerable)
        _add_made(t, 7, Suit.SPADES, Seat.SOUTH, 13)
        state = t.get_state()
        # 7S = 210 below (game 2), 1500 slam bonus (vulnerable)
        assert state.ns_games_won == 2
        assert state.is_complete
        assert state.ns_above >= 1500  # includes rubber bonus too


# ---------------------------------------------------------------------------
# Insult bonus in rubber context
# ---------------------------------------------------------------------------


class TestInsultInRubber:
    def test_doubled_made(self) -> None:
        t = RubberTracker()
        _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 8, doubled=True)
        state = t.get_state()
        # 2H doubled = 120 below (game!), 50 insult above
        assert state.ns_games_won == 1
        assert state.ns_above == 50

    def test_redoubled_made(self) -> None:
        t = RubberTracker()
        _add_made(t, 1, Suit.NOTRUMP, Seat.NORTH, 7, redoubled=True)
        state = t.get_state()
        # 1NT rdbl = 160 below (game!), 100 insult above
        assert state.ns_games_won == 1
        assert state.ns_above == 100


# ---------------------------------------------------------------------------
# Full rubber scenario
# ---------------------------------------------------------------------------


class TestFullRubberScenario:
    def test_realistic_rubber(self) -> None:
        """Play through a realistic rubber and verify final totals."""
        t = RubberTracker()

        # Deal 1: NS bid 2H, made 9 (1 overtrick). NV.
        _add_made(t, 2, Suit.HEARTS, Seat.NORTH, 9)
        # NS: 60 below, 30 above

        # Deal 2: EW bid 3NT, made 9. NV.
        _add_made(t, 3, Suit.NOTRUMP, Seat.EAST, 9)
        # EW: 100 below -> game! EW vulnerable now.
        # NS 60 below is wiped for next game.

        state = t.get_state()
        assert state.ew_games_won == 1
        assert state.ew_vulnerable
        assert not state.ns_vulnerable
        assert state.ns_below_current == 0

        # Deal 3: NS bid 4S, made 10. NV (NS didn't win a game).
        _add_made(t, 4, Suit.SPADES, Seat.SOUTH, 10)
        # NS: 120 below -> game! NS vulnerable now.

        state = t.get_state()
        assert state.ns_games_won == 1
        assert state.ns_vulnerable

        # Deal 4: EW bid 3H, down 2. EW is vulnerable.
        _add_made(t, 3, Suit.HEARTS, Seat.WEST, 7)
        # EW down 2, vulnerable = 200 to NS above

        state = t.get_state()
        assert state.ns_above == 30 + 200  # overtrick from deal 1 + penalty

        # Deal 5: NS bid 3NT, made 10 (1 overtrick). NS is vulnerable.
        _add_made(t, 3, Suit.NOTRUMP, Seat.NORTH, 10)
        # NS: 100 below -> game 2! Rubber over (2-1).

        state = t.get_state()
        assert state.is_complete
        assert state.ns_games_won == 2
        assert state.ew_games_won == 1
        assert state.rubber_bonus == 500

        # Verify totals:
        # NS below: 60 (game1 wiped but counts in total) + 120 (game2) + 100 (game3)
        # Actually: game1 had ns_below=0 when EW won it. Let me recalc.
        # Game 1: NS=60 below, EW=100 below. EW wins. Both wiped.
        # Game 2: NS=120 below. NS wins.
        # Game 3: NS=100 below. NS wins.
        # NS total below = 60 + 120 + 100 = 280
        # NS above = 30 (deal1 OT) + 200 (deal4 penalty) + 30 (deal5 OT) + 500 (rubber)
        # NS total = 280 + 760 = 1040
        assert state.ns_total == 1040

        # EW total below = 100 (game1)
        # EW total above = 0
        # EW total = 100
        assert state.ew_total == 100
