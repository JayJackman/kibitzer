"""Table - manages a stateful game session for a live auction."""

from __future__ import annotations

import secrets

from bridge.model.auction import NO_VULNERABILITY, AuctionState, Seat, Vulnerability
from bridge.model.bid import Bid
from bridge.model.hand import Hand

from .advisor import BiddingAdvisor
from .models import (
    AuctionCompleteError,
    BiddingAdvice,
    DuplicateCardError,
    HandNotSetError,
    NotYourTurnError,
    Player,
    PlayerNotSeatedError,
    SeatEmptyError,
    SeatOccupiedError,
    TableStatus,
    TableView,
    UnauthorizedBidError,
)


class Table:
    """Manages the stateful game session for a live auction."""

    def __init__(
        self,
        table_id: str | None = None,
        dealer: Seat = Seat.NORTH,
        vulnerability: Vulnerability = NO_VULNERABILITY,
    ) -> None:
        self.id: str = table_id or secrets.token_urlsafe(6)
        self.seats: dict[Seat, Player | None] = {seat: None for seat in Seat}
        self.hands: dict[Seat, Hand | None] = {seat: None for seat in Seat}
        self.auction: AuctionState = AuctionState(
            dealer=dealer, vulnerability=vulnerability
        )
        self.status: TableStatus = TableStatus.WAITING
        self._advisor: BiddingAdvisor = BiddingAdvisor()

    def join(self, seat: Seat, player: Player) -> None:
        """Claim a seat. Raises SeatOccupiedError if seat is occupied."""
        if self.seats[seat] is not None:
            raise SeatOccupiedError(f"Seat {seat.name} is already occupied")
        self.seats[seat] = player

    def leave(self, seat: Seat) -> None:
        """Vacate a seat. Raises SeatEmptyError if seat is empty."""
        if self.seats[seat] is None:
            raise SeatEmptyError(f"Seat {seat.name} is empty")
        self.seats[seat] = None

    def set_hand(self, seat: Seat, hand: Hand) -> None:
        """Set the hand for a seat.

        Raises SeatEmptyError if seat is unoccupied.
        Raises DuplicateCardError if any card conflicts with another seat's hand.
        """
        if self.seats[seat] is None:
            raise SeatEmptyError(f"Seat {seat.name} is not occupied")

        # Check for duplicate cards across other seated hands
        for other_seat, other_hand in self.hands.items():
            if other_seat == seat or other_hand is None:
                continue
            if hand.cards & other_hand.cards:
                raise DuplicateCardError(
                    f"Card conflict between {seat.name} and {other_seat.name} "
                    f"- both players should re-check and re-enter their hands"
                )

        self.hands[seat] = hand

    def make_bid(self, seat: Seat, bid: Bid, player: Player) -> None:
        """Place a bid for a seat.

        Authorization:
        - If seat has a player assigned and player == that player -> allowed
        - If seat has no player assigned -> allowed (proxy bid for empty seat)
        - If seat has a player assigned and player != that player -> rejected

        Raises NotYourTurnError if it's not this seat's turn.
        Raises AuctionCompleteError if the auction is already finished.
        Raises PlayerNotSeatedError if the player is not seated anywhere.
        Raises UnauthorizedBidError if bidding for another player's seat.
        """
        if self.status == TableStatus.COMPLETED:
            raise AuctionCompleteError("Auction is already complete")

        # Player must be seated somewhere
        if not any(p == player for p in self.seats.values() if p is not None):
            raise PlayerNotSeatedError(
                f"Player {player.name!r} is not seated at this table"
            )

        # Check authorization
        seat_player = self.seats[seat]
        if seat_player is not None and seat_player != player:
            raise UnauthorizedBidError(
                f"Cannot bid for {seat.name} - that seat belongs to {seat_player.name}"
            )

        # Must be this seat's turn
        if self.auction.current_seat != seat:
            raise NotYourTurnError(
                f"It is {self.auction.current_seat.name}'s turn, not {seat.name}'s"
            )

        # Delegate bid legality to AuctionState
        self.auction.add_bid(bid)

        # Status transitions
        if self.status == TableStatus.WAITING:
            self.status = TableStatus.IN_PROGRESS
        if self.auction.is_complete:
            self.status = TableStatus.COMPLETED

    def get_state(self, seat: Seat) -> TableView:
        """Return a filtered view for a specific seat (only your hand visible)."""
        return TableView(
            seat=seat,
            hand=self.hands[seat],
            seats=dict(self.seats),
            bids=self.auction.bids,
            current_seat=self.auction.current_seat,
            is_complete=self.auction.is_complete,
            contract=self.auction.contract,
            status=self.status,
        )

    def get_advice(self, seat: Seat) -> BiddingAdvice:
        """Get bid advice for a seat.

        Raises HandNotSetError if no hand is set for this seat.
        Raises NotYourTurnError if it's not this seat's turn.
        Raises AuctionCompleteError if auction is already finished.
        """
        if self.status == TableStatus.COMPLETED:
            raise AuctionCompleteError("Auction is already complete")

        if (hand := self.hands[seat]) is None:
            raise HandNotSetError(f"No hand set for {seat.name}")

        if self.auction.current_seat != seat:
            raise NotYourTurnError(
                f"It is {self.auction.current_seat.name}'s turn, not {seat.name}'s"
            )

        return self._advisor.advise(hand, self.auction)

    def reset(self) -> None:
        """Clear hands and auction for a new deal. Keep seat assignments."""
        self.hands = {seat: None for seat in Seat}
        self.auction = AuctionState(
            dealer=self.auction.dealer,
            vulnerability=self.auction.vulnerability,
        )
        self.status = TableStatus.WAITING
