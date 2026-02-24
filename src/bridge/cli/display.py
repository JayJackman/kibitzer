"""Rich display formatters for the bridge CLI.

Pure formatting functions that take domain objects and return Rich
renderables. No I/O -- callers print the returned objects.
"""

from __future__ import annotations

import re

from rich.panel import Panel
from rich.table import Table

from bridge.engine.rule import RuleResult
from bridge.engine.selector import ThoughtProcess, ThoughtStep
from bridge.model.auction import Contract, Seat
from bridge.model.bid import Bid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Suit
from bridge.model.hand import Hand
from bridge.service.models import BiddingAdvice, HandEvaluation

_MARKUP_RE = re.compile(r"\[[/a-z]+\]")

_SUIT_COLORS: dict[Suit, str] = {
    Suit.SPADES: "blue",
    Suit.HEARTS: "red",
    Suit.DIAMONDS: "yellow",
    Suit.CLUBS: "green",
}

_SEAT_NAMES: dict[Seat, str] = {
    Seat.NORTH: "North",
    Seat.SOUTH: "South",
    Seat.EAST: "East",
    Seat.WEST: "West",
}

# Column order for the auction grid (standard bridge diagram).
_AUCTION_SEATS = (Seat.WEST, Seat.NORTH, Seat.EAST, Seat.SOUTH)


def _colored_suit(suit: Suit) -> str:
    """Return a suit symbol wrapped in Rich color markup."""
    color = _SUIT_COLORS.get(suit)
    symbol = str(suit)
    if color:
        return f"[{color}]{symbol}[/{color}]"
    return symbol


def format_bid(bid: Bid) -> str:
    """Format a bid with colored suit symbols for Rich output.

    Example: ``1[blue]S[/blue]``, ``2NT``, ``Pass``
    """
    if is_suit_bid(bid):
        suit = bid.suit
        level = bid.level
        if suit == Suit.NOTRUMP:
            return f"{level}NT"
        return f"{level}{_colored_suit(suit)}"
    return str(bid)


def _format_hand_lines(hand: Hand) -> list[str]:
    """Format a hand as a list of suit lines (no panel)."""
    lines = []
    for suit in SUITS_SHDC:
        cards = hand.suit_cards(suit)
        ranks = " ".join(str(c.rank) for c in cards)
        lines.append(f"{_colored_suit(suit)}  {ranks}")
    return lines


def format_hand(hand: Hand) -> Panel:
    """Display a hand with colored suit symbols.

    Example::

        +-- Your Hand ---+
        |  S  A K J 5 2  |
        |  H  K Q 3      |
        |  D  8 4        |
        |  C  A 7 3      |
        +----------------+
    """
    return Panel(
        "\n".join(f"  {line}" for line in _format_hand_lines(hand)),
        title="Your Hand",
    )


def _visible_len(s: str) -> int:
    """Length of a string after stripping Rich markup tags."""
    return len(_MARKUP_RE.sub("", s))


def _ljust(s: str, width: int) -> str:
    """Left-justify accounting for invisible Rich markup."""
    return s + " " * max(0, width - _visible_len(s))


def _center_block(block: list[str], width: int) -> list[str]:
    """Center a block of lines as a unit, preserving internal alignment."""
    max_vis = max(_visible_len(line) for line in block)
    pad = max(0, width - max_vis) // 2
    prefix = " " * pad
    return [prefix + line for line in block]


def format_all_hands(hands: dict[Seat, Hand]) -> Panel:
    """Display all four hands in bridge diagram layout.

    Example::

        +---------- All Hands -----------+
        |          North                 |
        |        S  A K 3 2              |
        |        H  K Q 3                |
        |        ...                     |
        |                                |
        | West                East       |
        | S  8 4              S  Q J 5   |
        | ...                 ...        |
        |                                |
        |          South                 |
        |        S  T 9 7 6              |
        |        ...                     |
        +--------------------------------+
    """
    north = _format_hand_lines(hands[Seat.NORTH])
    south = _format_hand_lines(hands[Seat.SOUTH])
    west = _format_hand_lines(hands[Seat.WEST])
    east = _format_hand_lines(hands[Seat.EAST])

    col = 24  # visible width reserved for each hand (West / East)
    gap = 4  # space between the West and East columns
    total = col * 2 + gap  # full content width

    lines: list[str] = []

    # North/South are shifted slightly left of center to sit above West
    ns_width = total - 14

    # North (centered as a block so suit symbols stay aligned)
    lines.append(f"{'North':^{ns_width}}")
    lines.extend(_center_block(north, ns_width))
    lines.append("")

    # West and East side by side
    lines.append(f"{'West':<{col}}{'':>{gap}}East")
    for w, e in zip(west, east, strict=True):
        lines.append(f"{_ljust(w, col)}{'':>{gap}}{e}")
    lines.append("")

    # South (centered as a block)
    lines.append(f"{'South':^{ns_width}}")
    lines.extend(_center_block(south, ns_width))

    return Panel("\n".join(lines), title="All Hands")


def format_hand_eval(ev: HandEvaluation) -> Panel:
    """Display hand evaluation metrics.

    Example::

        +---- Hand Evaluation -----------+
        |  HCP: 17   Total Pts: 17.      |
        |  Shape: 5-3-3-2 (balanced).    |
        |  Quick Tricks: 3.5   Losers: 6 |
        |  Controls: 6                   |
        +--------------------------------+
    """
    shape = "-".join(str(n) for n in ev.shape)
    if ev.is_balanced:
        shape += " (balanced)"
    elif ev.is_semi_balanced:
        shape += " (semi-balanced)"

    lines = [
        f"  HCP: {ev.hcp}   Total Pts: {ev.total_points}",
        f"  Shape: {shape}",
        f"  Quick Tricks: {ev.quick_tricks}   Losers: {ev.losers}",
        f"  Controls: {ev.controls}",
    ]
    return Panel("\n".join(lines), title="Hand Evaluation")


def format_auction(
    bids: list[tuple[Seat, Bid]],
    dealer: Seat,
    current_seat: Seat | None,
) -> Panel:
    """Display the auction as a 4-column grid.

    Pass ``current_seat=None`` when the auction is complete.

    Example::

        +------- Auction --------+
        |  W     N     E     S   |
        |        1D   Pass   1H  |
        |  Pass   ?              |
        +------------------------+
    """
    table = Table(show_header=True, show_edge=False, pad_edge=False, box=None)
    for seat in _AUCTION_SEATS:
        table.add_column(str(seat), justify="center", min_width=6)

    dealer_col = _AUCTION_SEATS.index(dealer)

    # Build rows of 4 cells each
    row: list[str] = [""] * 4
    col = dealer_col
    for _seat, bid in bids:
        row[col] = format_bid(bid)
        col += 1
        if col == 4:
            table.add_row(*row)
            row = [""] * 4
            col = 0

    # Add pending marker for current seat
    if current_seat is not None:
        current_col = _AUCTION_SEATS.index(current_seat)
        row[current_col] = "[bold]?[/bold]"

    # Add the last partial row if it has content
    if any(cell != "" for cell in row):
        table.add_row(*row)

    return Panel(table, title="Auction")


def format_advice(advice: BiddingAdvice) -> Panel:
    """Display the recommended bid with explanation.

    Example::

        +---- Recommended Bid --------------------------+
        |  1NT: 15-17 HCP, balanced -- SAYC 1NT opening |
        +-----------------------------------------------+
    """
    bid_str = format_bid(advice.recommended.bid)
    explanation = advice.recommended.explanation
    if advice.recommended.forcing:
        explanation += " (forcing)"
    return Panel(f"  {bid_str}: {explanation}", title="Recommended Bid")


def format_alternatives(alternatives: list[RuleResult]) -> Panel | None:
    """Display alternative bids. Returns None if empty.

    Example::

        +---- Alternatives -------------------------+
        |  2H  (rebid.reverse) - 17+ pts, H reverse |
        |  3D  (rebid.jump_rebid) - 6+ D, 17-18 pts |
        +-------------------------------------------+
    """
    if not alternatives:
        return None
    lines = []
    for alt in alternatives:
        bid_str = format_bid(alt.bid)
        lines.append(f"  {bid_str}  ({alt.rule_name}) - {alt.explanation}")
    return Panel("\n".join(lines), title="Alternatives")


def format_thought_process(tp: ThoughtProcess) -> Panel:
    """Display the engine's reasoning trace.

    Example::

        +---- Thought Process ------------+
        |  Recommended: 1NT (opening.1nt) |
        |    V 15-17 HCP                  |
        |    V Balanced shape             |
        |                                 |
        |  Also considered:               |
        |    1S (opening.suit)            |
        |    opening.2nt                  |
        |      X 20-21 HCP                |
        +---------------------------------+
    """
    lines: list[str] = []

    # Find the winning step (None when selected is fallback.pass)
    winning_step = next(
        (s for s in tp.steps if s.rule_name == tp.selected.rule_name and s.passed),
        None,
    )

    # Show the winning rule
    bid_str = format_bid(tp.selected.bid)
    lines.append(f"  Recommended: {bid_str} ({tp.selected.rule_name})")
    if winning_step:
        for cr in winning_step.condition_results:
            mark = "[green]✓[/green]" if cr.passed else "[red]✗[/red]"
            lines.append(f"    {mark} {cr.detail}")

    # Collect alternatives: other passing steps + interesting failing steps
    other_passing = [
        s for s in tp.steps if s.passed and s.rule_name != tp.selected.rule_name
    ]
    interesting_failing = [s for s in tp.steps if not s.passed and _is_interesting(s)]

    considered = other_passing + interesting_failing[:5]
    if considered:
        lines.append("")
        lines.append("  Also considered:")
        for step in considered:
            if step.passed:
                assert step.bid is not None
                lines.append(f"    {format_bid(step.bid)} ({step.rule_name})")
            else:
                # Show rule name + first failing condition
                lines.append(f"    {step.rule_name}")
                for cr in step.condition_results:
                    if not cr.passed:
                        lines.append(f"      [red]✗[/red] {cr.detail}")
                        break

    return Panel("\n".join(lines), title="Thought Process")


def _is_interesting(step: ThoughtStep) -> bool:
    """A failing step is interesting if it passed at least one condition."""
    return any(cr.passed for cr in step.condition_results)


def format_contract(contract: Contract) -> str:
    """Format a contract with colored suit symbols.

    Example: ``3NT by North``, ``4S by South doubled``, ``Passed out``
    """
    if contract.passed_out:
        return "Passed out"
    suit = contract.suit
    if suit == Suit.NOTRUMP:
        bid_part = f"{contract.level}NT"
    else:
        bid_part = f"{contract.level}{_colored_suit(suit)}"
    declarer = _SEAT_NAMES[contract.declarer]
    result = f"{bid_part} by {declarer}"
    if contract.redoubled:
        result += " redoubled"
    elif contract.doubled:
        result += " doubled"
    return result


def format_bid_prompt(current_seat: Seat) -> str:
    """Return a prompt with available commands.

    Example: ``North's bid (a=advise, h=help, q=quit):``
    """
    name = _SEAT_NAMES[current_seat]
    return f"{name}'s bid (a=advise, r=redeal, h=help, q=quit): "
