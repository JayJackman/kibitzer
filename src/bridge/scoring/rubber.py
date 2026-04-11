"""Rubber bridge state machine.

Tracks a list of scoring entries (the single source of truth) and
recomputes game boundaries, vulnerability, and totals on every
``get_state()`` call.  Editing past entries automatically recalculates
everything downstream.

All scoring formulas delegate to ``calculator.score_deal()``.
"""

from __future__ import annotations

from dataclasses import dataclass

from bridge.model.auction import Contract, Seat, Side, Vulnerability
from bridge.model.card import Suit
from bridge.scoring.calculator import DealScore, score_deal

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class ScoringEntry:
    """One deal's result in the rubber."""

    id: int
    contract_level: int
    contract_suit: Suit
    declarer: Seat
    doubled: bool = False
    redoubled: bool = False
    tricks_taken: int | None = None


@dataclass(frozen=True)
class GameSummary:
    """Accumulated state for one completed game within the rubber."""

    ns_below: int
    ew_below: int
    entry_ids: list[int]


@dataclass(frozen=True)
class ScoredEntry:
    """An entry paired with its computed DealScore (for display)."""

    entry: ScoringEntry
    score: DealScore | None
    declarer_side: Side


@dataclass(frozen=True)
class RubberState:
    """Full rubber state snapshot, serializable for the API."""

    entries: list[ScoredEntry]
    ns_games_won: int
    ew_games_won: int
    ns_above: int
    ew_above: int
    ns_below_current: int
    ew_below_current: int
    ns_vulnerable: bool
    ew_vulnerable: bool
    is_complete: bool
    rubber_bonus: int
    ns_total: int
    ew_total: int
    games: list[GameSummary]
    pending_entry_id: int | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# RubberTracker
# ---------------------------------------------------------------------------


class RubberTracker:
    """Mutable state machine tracking a rubber bridge rubber."""

    def __init__(self) -> None:
        self._entries: list[ScoringEntry] = []
        self._next_id: int = 0

    # ── Entry management ──────────────────────────────────────────

    def add_entry(
        self,
        *,
        contract_level: int,
        contract_suit: Suit,
        declarer: Seat,
        doubled: bool = False,
        redoubled: bool = False,
        tricks_taken: int | None = None,
        position: int | None = None,
    ) -> int:
        """Add a scoring entry.  Returns the new entry's id.

        If *position* is given, insert at that index (0-based) instead
        of appending.  Useful for recording a missed deal retroactively.
        """
        entry = ScoringEntry(
            id=self._next_id,
            contract_level=contract_level,
            contract_suit=contract_suit,
            declarer=declarer,
            doubled=doubled,
            redoubled=redoubled,
            tricks_taken=tricks_taken,
        )
        self._next_id += 1
        if position is not None:
            self._entries.insert(position, entry)
        else:
            self._entries.append(entry)
        return entry.id

    def update_entry(
        self,
        entry_id: int,
        *,
        contract_level: int,
        contract_suit: Suit,
        declarer: Seat,
        doubled: bool,
        redoubled: bool,
        tricks_taken: int | None,
    ) -> None:
        """Replace all fields on an existing entry."""
        entry = self._find_entry(entry_id)
        entry.contract_level = contract_level
        entry.contract_suit = contract_suit
        entry.declarer = declarer
        entry.doubled = doubled
        entry.redoubled = redoubled
        entry.tricks_taken = tricks_taken

    def remove_entry(self, entry_id: int) -> None:
        """Remove an entry by id."""
        entry = self._find_entry(entry_id)
        self._entries.remove(entry)

    def auto_populate_contract(self, contract: Contract) -> int:
        """Create a pending entry from a completed auction contract.

        Returns the new entry's id.  ``tricks_taken`` is left as ``None``
        (pending) -- the user fills it in after playing the hand.
        """
        return self.add_entry(
            contract_level=contract.level,
            contract_suit=contract.suit,
            declarer=contract.declarer,
            doubled=contract.doubled,
            redoubled=contract.redoubled,
            tricks_taken=None,
        )

    # ── Queries ───────────────────────────────────────────────────

    def current_vulnerability(self) -> Vulnerability:
        """Vulnerability derived from rubber state (games won)."""
        state = self.get_state()
        return Vulnerability(
            ns_vulnerable=state.ns_vulnerable,
            ew_vulnerable=state.ew_vulnerable,
        )

    def get_state(self) -> RubberState:
        """Recompute the full rubber state from entries."""
        ns_games = 0
        ew_games = 0
        ns_below = 0
        ew_below = 0
        ns_above = 0
        ew_above = 0
        games: list[GameSummary] = []
        current_game_entry_ids: list[int] = []
        scored_entries: list[ScoredEntry] = []
        pending_entry_id: int | None = None
        rubber_complete = False

        for entry in self._entries:
            side = entry.declarer.side

            if entry.tricks_taken is None:
                # Pending entry -- no scoring yet.
                scored_entries.append(
                    ScoredEntry(entry=entry, score=None, declarer_side=side)
                )
                if pending_entry_id is None:
                    pending_entry_id = entry.id
                continue

            # Determine vulnerability at this point in the rubber.
            declarer_vul = (ns_games >= 1) if side == Side.NS else (ew_games >= 1)

            deal = score_deal(
                entry.contract_level,
                entry.contract_suit,
                doubled=entry.doubled,
                redoubled=entry.redoubled,
                declarer_vulnerable=declarer_vul,
                tricks_taken=entry.tricks_taken,
            )
            scored_entries.append(
                ScoredEntry(entry=entry, score=deal, declarer_side=side)
            )
            current_game_entry_ids.append(entry.id)

            if deal.made:
                # Contract points go below the line for the declaring side.
                if side == Side.NS:
                    ns_below += deal.contract_points
                else:
                    ew_below += deal.contract_points

                # Above-the-line bonuses for the declaring side.
                above = deal.overtrick_points + deal.slam_bonus + deal.insult_bonus
                if side == Side.NS:
                    ns_above += above
                else:
                    ew_above += above
            else:
                # Undertrick penalties go to the defending side (above the line).
                if side == Side.NS:
                    ew_above += deal.undertrick_points
                else:
                    ns_above += deal.undertrick_points

            # Check for game completion (100+ below the line).
            game_won_by: Side | None = None
            if ns_below >= 100:
                game_won_by = Side.NS
            elif ew_below >= 100:
                game_won_by = Side.EW

            if game_won_by is not None:
                games.append(
                    GameSummary(
                        ns_below=ns_below,
                        ew_below=ew_below,
                        entry_ids=list(current_game_entry_ids),
                    )
                )
                if game_won_by == Side.NS:
                    ns_games += 1
                else:
                    ew_games += 1

                # Reset below-the-line for the next game.
                ns_below = 0
                ew_below = 0
                current_game_entry_ids = []

                # Check for rubber completion.
                if ns_games >= 2 or ew_games >= 2:
                    rubber_complete = True

        # Rubber bonus (above the line for the winning side).
        rubber_bonus = 0
        if rubber_complete:
            if ns_games >= 2:
                rubber_bonus = 700 if ew_games == 0 else 500
                ns_above += rubber_bonus
            else:
                rubber_bonus = 700 if ns_games == 0 else 500
                ew_above += rubber_bonus

        # Grand totals (above + below, all games).
        ns_all_below = sum(g.ns_below for g in games) + ns_below
        ew_all_below = sum(g.ew_below for g in games) + ew_below

        return RubberState(
            entries=scored_entries,
            ns_games_won=ns_games,
            ew_games_won=ew_games,
            ns_above=ns_above,
            ew_above=ew_above,
            ns_below_current=ns_below,
            ew_below_current=ew_below,
            ns_vulnerable=ns_games >= 1 and not rubber_complete,
            ew_vulnerable=ew_games >= 1 and not rubber_complete,
            is_complete=rubber_complete,
            rubber_bonus=rubber_bonus,
            ns_total=ns_above + ns_all_below,
            ew_total=ew_above + ew_all_below,
            games=games,
            pending_entry_id=pending_entry_id,
        )

    def new_rubber(self) -> None:
        """Reset for a new rubber."""
        self._entries.clear()
        self._next_id = 1

    # ── Private ───────────────────────────────────────────────────

    def _find_entry(self, entry_id: int) -> ScoringEntry:
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        raise KeyError(f"No scoring entry with id {entry_id}")
