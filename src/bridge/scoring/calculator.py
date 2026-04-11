"""Pure scoring functions for a single bridge deal.

Format-agnostic: the returned DealScore breakdown is identical for rubber,
duplicate, MP, and IMP scoring.  The *aggregation* differs by format --
RubberTracker handles rubber-specific logic (below/above the line, game
accumulation, rubber bonus).  A future duplicate scorer would apply flat
game bonuses to the same DealScore.

All formulas follow research/08-rubber-scoring.md (ACBL Laws of Rubber Bridge).
"""

from __future__ import annotations

from dataclasses import dataclass

from bridge.model.card import Suit


@dataclass(frozen=True)
class DealScore:
    """Complete point breakdown for one deal."""

    contract_points: int
    """Below-the-line points (tricks bid and made only)."""

    overtrick_points: int
    """Above-the-line points for the declaring side (overtricks)."""

    undertrick_points: int
    """Above-the-line points for the defending side (penalties)."""

    slam_bonus: int
    """Above-the-line slam bonus for the declaring side (0 if not a slam)."""

    insult_bonus: int
    """Above-the-line bonus for making a doubled/redoubled contract."""

    made: bool
    """True if the contract was fulfilled (tricks_taken >= 6 + level)."""


def score_deal(
    level: int,
    suit: Suit,
    *,
    doubled: bool = False,
    redoubled: bool = False,
    declarer_vulnerable: bool = False,
    tricks_taken: int,
) -> DealScore:
    """Compute the full point breakdown for a single deal.

    Parameters
    ----------
    level:
        Contract level (1-7).
    suit:
        Contract denomination (CLUBS, DIAMONDS, HEARTS, SPADES, NOTRUMP).
    doubled:
        True if the contract was doubled (mutually exclusive with redoubled).
    redoubled:
        True if the contract was redoubled (mutually exclusive with doubled).
    declarer_vulnerable:
        True if the declaring side is vulnerable.
    tricks_taken:
        Total tricks won by the declaring side (0-13).
    """
    tricks_needed = 6 + level
    result = tricks_taken - tricks_needed  # positive = overtricks, negative = down

    if result >= 0:
        return _score_made(level, suit, doubled, redoubled, declarer_vulnerable, result)
    return _score_defeated(doubled, redoubled, declarer_vulnerable, -result)


# ---------------------------------------------------------------------------
# Contract made
# ---------------------------------------------------------------------------


def _contract_points(level: int, suit: Suit, doubled: bool, redoubled: bool) -> int:
    """Below-the-line points for tricks bid and made."""
    if suit == Suit.NOTRUMP:
        # First trick is 40, subsequent tricks are 30.
        base = 40 + 30 * (level - 1)
    elif suit.is_major:
        base = 30 * level
    else:
        base = 20 * level

    if redoubled:
        return base * 4
    if doubled:
        return base * 2
    return base


def _overtrick_points(
    suit: Suit,
    doubled: bool,
    redoubled: bool,
    declarer_vulnerable: bool,
    overtricks: int,
) -> int:
    """Above-the-line points for overtricks."""
    if overtricks == 0:
        return 0

    if redoubled:
        per_trick = 400 if declarer_vulnerable else 200
        return per_trick * overtricks
    if doubled:
        per_trick = 200 if declarer_vulnerable else 100
        return per_trick * overtricks

    # Undoubled: score at denomination's trick value.
    if suit == Suit.NOTRUMP:
        per_trick = 30  # Subsequent NT tricks (not 40).
    elif suit.is_major:
        per_trick = 30
    else:
        per_trick = 20
    return per_trick * overtricks


def _slam_bonus(level: int, declarer_vulnerable: bool) -> int:
    """Above-the-line slam bonus (must be BID at the slam level)."""
    if level == 7:
        return 1500 if declarer_vulnerable else 1000
    if level == 6:
        return 750 if declarer_vulnerable else 500
    return 0


def _insult_bonus(doubled: bool, redoubled: bool) -> int:
    """Bonus for making a doubled or redoubled contract."""
    if redoubled:
        return 100
    if doubled:
        return 50
    return 0


def _score_made(
    level: int,
    suit: Suit,
    doubled: bool,
    redoubled: bool,
    declarer_vulnerable: bool,
    overtricks: int,
) -> DealScore:
    return DealScore(
        contract_points=_contract_points(level, suit, doubled, redoubled),
        overtrick_points=_overtrick_points(
            suit, doubled, redoubled, declarer_vulnerable, overtricks
        ),
        undertrick_points=0,
        slam_bonus=_slam_bonus(level, declarer_vulnerable),
        insult_bonus=_insult_bonus(doubled, redoubled),
        made=True,
    )


# ---------------------------------------------------------------------------
# Contract defeated
# ---------------------------------------------------------------------------


def _undertrick_penalty(
    doubled: bool,
    redoubled: bool,
    declarer_vulnerable: bool,
    down: int,
) -> int:
    """Total penalty points for the defending side."""
    if not doubled and not redoubled:
        per_trick = 100 if declarer_vulnerable else 50
        return per_trick * down

    # Doubled undertrick schedule (per-trick, not cumulative):
    #   1st:  NV=100, V=200
    #   2nd:  NV=200, V=300
    #   3rd:  NV=200, V=300
    #   4th+: NV=300, V=300
    total = 0
    for i in range(1, down + 1):
        if i == 1:
            trick_penalty = 200 if declarer_vulnerable else 100
        elif i <= 3:
            trick_penalty = 300 if declarer_vulnerable else 200
        else:
            trick_penalty = 300
        total += trick_penalty

    if redoubled:
        return total * 2
    return total


def _score_defeated(
    doubled: bool,
    redoubled: bool,
    declarer_vulnerable: bool,
    down: int,
) -> DealScore:
    return DealScore(
        contract_points=0,
        overtrick_points=0,
        undertrick_points=_undertrick_penalty(
            doubled, redoubled, declarer_vulnerable, down
        ),
        slam_bonus=0,
        insult_bonus=0,
        made=False,
    )
