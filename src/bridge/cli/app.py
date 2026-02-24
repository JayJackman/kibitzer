"""Bridge bidding assistant CLI."""

import typer
from rich.console import Console

from bridge.cli.display import (
    format_advice,
    format_all_hands,
    format_alternatives,
    format_auction,
    format_bid,
    format_bid_prompt,
    format_contract,
    format_hand,
    format_hand_eval,
    format_thought_process,
)
from bridge.model.auction import (
    AuctionState,
    IllegalBidError,
    Seat,
    Vulnerability,
    parse_auction,
)
from bridge.model.bid import is_pass, parse_bid
from bridge.model.hand import Hand
from bridge.service.advisor import BiddingAdvisor
from bridge.service.deal import deal

app = typer.Typer(add_completion=False)
console = Console()

_SEAT_NAMES: dict[Seat, str] = {
    Seat.NORTH: "North",
    Seat.SOUTH: "South",
    Seat.EAST: "East",
    Seat.WEST: "West",
}


@app.command()
def advise(
    hand: str = typer.Option(..., help="Hand in PBN format (e.g. AKJ52.KQ3.84.A73)"),
    auction: str = typer.Option("", help="Space-separated bids (e.g. '1H P')"),
    dealer: str = typer.Option("N", help="Dealer seat (N/E/S/W)"),
    vulnerability: str = typer.Option("None", help="Vulnerability (None/NS/EW/Both)"),
) -> None:
    """Get a bid recommendation for a hand and auction state."""
    try:
        dealer_seat = Seat.from_str(dealer)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid dealer: {dealer!r}. Use N, E, S, or W."
        )
        raise typer.Exit(code=1) from None

    try:
        vuln = Vulnerability.from_str(vulnerability)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid vulnerability: {vulnerability!r}. "
            "Use None, NS, EW, or Both."
        )
        raise typer.Exit(code=1) from None

    try:
        parsed_hand = Hand.from_pbn(hand)
    except ValueError as e:
        console.print(f"[red]Error:[/red] Invalid hand: {e}")
        raise typer.Exit(code=1) from None

    try:
        auction_state = parse_auction(auction, dealer_seat, vuln)
    except (ValueError, IllegalBidError) as e:
        console.print(f"[red]Error:[/red] Invalid auction: {e}")
        raise typer.Exit(code=1) from None

    advisor = BiddingAdvisor()
    advice = advisor.advise(parsed_hand, auction_state)

    console.print(format_hand(parsed_hand))
    console.print(format_hand_eval(advice.hand_evaluation))
    console.print(
        format_auction(
            auction_state.bids,
            auction_state.dealer,
            auction_state.current_seat,
        )
    )
    console.print(format_advice(advice))
    console.print(format_thought_process(advice.thought_process))
    alts_panel = format_alternatives(advice.alternatives)
    if alts_panel is not None:
        console.print(alts_panel)


@app.command()
def practice(
    seat: str = typer.Option("S", help="Your seat (N/E/S/W)"),
    dealer: str = typer.Option("S", help="Dealer seat (N/E/S/W)"),
    vulnerability: str = typer.Option("None", help="Vulnerability (None/NS/EW/Both)"),
) -> None:
    """Interactive solo bidding practice."""
    try:
        player_seat = Seat.from_str(seat)
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid seat: {seat!r}. Use N, E, S, or W.")
        raise typer.Exit(code=1) from None

    try:
        dealer_seat = Seat.from_str(dealer)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid dealer: {dealer!r}. Use N, E, S, or W."
        )
        raise typer.Exit(code=1) from None

    try:
        vuln = Vulnerability.from_str(vulnerability)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid vulnerability: {vulnerability!r}. "
            "Use None, NS, EW, or Both."
        )
        raise typer.Exit(code=1) from None

    advisor = BiddingAdvisor()

    try:
        _practice_loop(advisor, player_seat, dealer_seat, vuln)
    except (KeyboardInterrupt, EOFError):
        console.print("\nGoodbye!")


def _practice_loop(
    advisor: BiddingAdvisor,
    player_seat: Seat,
    dealer_seat: Seat,
    vuln: Vulnerability,
) -> None:
    """Run the practice loop. Separated for testability."""
    while True:
        hands = deal()
        auction = AuctionState(dealer=dealer_seat, vulnerability=vuln)

        player_hand = hands[player_seat]
        advice_result = advisor.advise(player_hand, auction)
        hand_panel = format_hand(player_hand)
        eval_panel = format_hand_eval(advice_result.hand_evaluation)

        feedback: str | None = None
        computer_bids: list[str] = []
        while not auction.is_complete:
            current = auction.current_seat

            if current != player_seat:
                # Computer bids
                computer_advice = advisor.advise(hands[current], auction)
                bid = computer_advice.recommended.bid
                auction.add_bid(bid)
                if not is_pass(bid):
                    name = _SEAT_NAMES[current]
                    bid_str = format_bid(bid)
                    explanation = computer_advice.recommended.explanation
                    computer_bids.append(f"  {name} bid {bid_str}: {explanation}")
            else:
                # Redraw hand + eval + auction before each player prompt
                console.clear()
                console.print()
                console.print(hand_panel)
                console.print(eval_panel)
                console.print(format_auction(auction.bids, auction.dealer, current))
                if feedback is not None:
                    console.print(feedback)
                    feedback = None
                for line in computer_bids:
                    console.print(line)
                computer_bids.clear()
                result = _player_turn(advisor, player_hand, auction, player_seat)
                if result is None:
                    return
                if result == _REDEAL:
                    break
                feedback = result

        else:
            # Auction complete (not redealt)
            console.clear()
            console.print()
            console.print(hand_panel)
            console.print(eval_panel)
            console.print(format_auction(auction.bids, auction.dealer, None))
            if feedback is not None:
                console.print(feedback)
            for line in computer_bids:
                console.print(line)
            contract = auction.contract
            if contract is not None:
                console.print(f"  Final contract: {format_contract(contract)}")
            console.print(format_all_hands(hands))

            again = console.input("\nPlay again? [Y/n] ").strip().lower()
            if again in ("n", "no"):
                return


_REDEAL = "<<redeal>>"


def _player_turn(
    advisor: BiddingAdvisor,
    hand: Hand,
    auction: AuctionState,
    seat: Seat,
) -> str | None:
    """Handle one player turn. Returns feedback string, _REDEAL, or None to quit."""
    while True:
        raw = console.input(format_bid_prompt(seat)).strip()
        cmd = raw.lower()

        if cmd in ("q", "quit"):
            return None
        if cmd in ("r", "redeal"):
            return _REDEAL
        if cmd in ("h", "?", "help"):
            console.print("  Valid bids: 1C..7NT, P (Pass), X (Double), XX (Redouble)")
            continue
        if cmd in ("a", "advise"):
            advice = advisor.advise(hand, auction)
            console.print(format_advice(advice))
            console.print(format_thought_process(advice.thought_process))
            alts = format_alternatives(advice.alternatives)
            if alts is not None:
                console.print(alts)
            continue

        # Try to parse as a bid
        try:
            bid = parse_bid(raw)
        except ValueError:
            console.print(f"  [red]Invalid bid:[/red] {raw!r}. Try: 1H, 2NT, P, X, XX")
            continue

        # Get engine advice before adding the bid
        advice = advisor.advise(hand, auction)

        try:
            auction.add_bid(bid)
        except IllegalBidError as e:
            console.print(f"  [red]Illegal bid:[/red] {e}")
            continue

        # Build feedback for display after next redraw
        bid_str = format_bid(bid)
        if bid == advice.recommended.bid:
            return f"  {bid_str} matched the engine's recommendation."
        rec_bid = format_bid(advice.recommended.bid)
        return (
            f"  You bid {bid_str}. The engine recommends {rec_bid}: "
            f"{advice.recommended.explanation}"
        )
