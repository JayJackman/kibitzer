"""Rich display formatters for the bridge CLI.

Pure formatting functions that take domain objects and return Rich
renderables. No I/O -- callers print the returned objects.
"""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bridge.engine.rule import RuleResult
from bridge.engine.selector import ThoughtProcess, ThoughtStep
from bridge.model.auction import Contract, Seat
from bridge.model.bid import Bid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Suit
from bridge.model.hand import Hand
from bridge.service.models import BiddingAdvice, HandEvaluation

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
    """Format a bid with colored suit symbols for Rich output."""
    if is_suit_bid(bid):
        suit = bid.suit
        level = bid.level
        if suit == Suit.NOTRUMP:
            return f"{level}NT"
        return f"{level}{_colored_suit(suit)}"
    return str(bid)


def format_hand(hand: Hand) -> Panel:
    """Display a hand with colored suit symbols."""
    text = Text()
    for i, suit in enumerate(SUITS_SHDC):
        if i > 0:
            text.append("\n")
        text.append(f"  {_colored_suit(suit)}  ", style=None)
        cards = hand.suit_cards(suit)
        text.append(" ".join(str(c.rank) for c in cards))
    return Panel(text, title="Your Hand")


def format_hand_eval(ev: HandEvaluation) -> Panel:
    """Display hand evaluation metrics."""
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
    """Display the recommended bid with explanation."""
    bid_str = format_bid(advice.recommended.bid)
    explanation = advice.recommended.explanation
    if advice.recommended.forcing:
        explanation += " (forcing)"
    return Panel(f"  {explanation}", title=f"Recommended Bid: {bid_str}")


def format_alternatives(alternatives: list[RuleResult]) -> Panel | None:
    """Display alternative bids. Returns None if empty."""
    if not alternatives:
        return None
    lines = []
    for alt in alternatives:
        bid_str = format_bid(alt.bid)
        lines.append(f"  {bid_str}  - {alt.explanation}")
    return Panel("\n".join(lines), title="Alternatives")


def format_thought_process(tp: ThoughtProcess) -> Panel:
    """Display the engine's reasoning trace."""
    text = Text()

    # Find the winning step (None when selected is fallback.pass)
    winning_step = next(
        (s for s in tp.steps if s.rule_name == tp.selected.rule_name and s.passed),
        None,
    )

    # Show the winning rule
    bid_str = format_bid(tp.selected.bid)
    text.append(f"  Recommended: {bid_str} ({tp.selected.rule_name})\n")
    if winning_step:
        for cr in winning_step.condition_results:
            mark = "[green]✓[/green]" if cr.passed else "[red]✗[/red]"
            text.append(f"    {mark} {cr.detail}\n")

    # Collect alternatives: other passing steps + interesting failing steps
    other_passing = [
        s for s in tp.steps if s.passed and s.rule_name != tp.selected.rule_name
    ]
    interesting_failing = [s for s in tp.steps if not s.passed and _is_interesting(s)]

    considered = other_passing + interesting_failing[:5]
    if considered:
        text.append("\n  Also considered:\n")
        for step in considered:
            if step.passed:
                assert step.bid is not None
                text.append(f"    {format_bid(step.bid)} ({step.rule_name})\n")
            else:
                # Show rule name + first failing condition
                text.append(f"    {step.rule_name}\n")
                for cr in step.condition_results:
                    if not cr.passed:
                        text.append(f"      [red]✗[/red] {cr.detail}\n")
                        break

    return Panel(text, title="Thought Process")


def _is_interesting(step: ThoughtStep) -> bool:
    """A failing step is interesting if it passed at least one condition."""
    return any(cr.passed for cr in step.condition_results)


def format_contract(contract: Contract) -> str:
    """Format a contract with colored suit symbols."""
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
    """Return a prompt string like \"North's bid: \"."""
    return f"{_SEAT_NAMES[current_seat]}'s bid: "
