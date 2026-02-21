"""Auction state tracking for bridge bidding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique

from .bid import Bid, BidType


@unique
class Seat(IntEnum):
    """Seat positions at the bridge table."""

    WEST = 0
    NORTH = 1
    EAST = 2
    SOUTH = 3

    @property
    def partner(self) -> Seat:
        return Seat((self.value + 2) % 4)

    @property
    def lho(self) -> Seat:
        """Left-hand opponent."""
        return Seat((self.value + 1) % 4)

    @property
    def rho(self) -> Seat:
        """Right-hand opponent."""
        return Seat((self.value + 3) % 4)

    def __str__(self) -> str:
        return self.name[0]

    @classmethod
    def from_str(cls, text: str) -> Seat:
        """Parse a seat name: 'N', 'North', 'north', etc."""
        text = text.strip().upper()
        for seat in cls:
            if text == seat.name or text == seat.name[0]:
                return seat
        raise ValueError(f"Invalid seat: {text!r}")


@dataclass(frozen=True)
class Vulnerability:
    """Vulnerability state for both partnerships."""

    ns_vulnerable: bool = False
    ew_vulnerable: bool = False

    def is_vulnerable(self, seat: Seat) -> bool:
        if seat in (Seat.NORTH, Seat.SOUTH):
            return self.ns_vulnerable
        return self.ew_vulnerable

    def __str__(self) -> str:
        if self.ns_vulnerable and self.ew_vulnerable:
            return "Both"
        if self.ns_vulnerable:
            return "NS"
        if self.ew_vulnerable:
            return "EW"
        return "None"

    @classmethod
    def from_str(cls, text: str) -> Vulnerability:
        """Parse vulnerability: 'None', 'NS', 'EW', 'Both', 'All'."""
        text = text.strip().upper()
        if text in ("NONE", "-"):
            return cls()
        if text == "NS":
            return cls(ns_vulnerable=True)
        if text == "EW":
            return cls(ew_vulnerable=True)
        if text in ("BOTH", "ALL"):
            return cls(ns_vulnerable=True, ew_vulnerable=True)
        raise ValueError(f"Invalid vulnerability: {text!r}")


class IllegalBidError(Exception):
    """Raised when an illegal bid is attempted."""


@dataclass
class AuctionState:
    """Tracks the full auction history and derived state.

    Bids are stored in order. The seat for each bid is derived from
    the dealer and the bid's position in the list.
    """

    dealer: Seat
    vulnerability: Vulnerability = field(default_factory=Vulnerability)
    _bids: list[Bid] = field(default_factory=list)

    @property
    def bids(self) -> list[tuple[Seat, Bid]]:
        """Full bid history as (seat, bid) pairs."""
        return [
            (Seat((self.dealer.value + i) % 4), bid) for i, bid in enumerate(self._bids)
        ]

    @property
    def current_seat(self) -> Seat:
        """Whose turn it is to bid."""
        return Seat((self.dealer.value + len(self._bids)) % 4)

    @property
    def is_complete(self) -> bool:
        """Auction is over: 3 passes after a non-pass bid, or 4 initial passes."""
        n = len(self._bids)
        if n < 4:
            return False
        # Four initial passes = passed out
        if all(b.is_pass for b in self._bids):
            return True
        # Three consecutive passes after at least one non-pass bid
        return all(b.is_pass for b in self._bids[-3:])

    @property
    def last_contract_bid(self) -> Bid | None:
        """Most recent suit bid (not pass/double/redouble)."""
        for bid in reversed(self._bids):
            if bid.bid_type == BidType.SUIT:
                return bid
        return None

    @property
    def opening_bid(self) -> tuple[Seat, Bid] | None:
        """First non-pass bid and who made it."""
        for seat, bid in self.bids:
            if bid.bid_type == BidType.SUIT:
                return (seat, bid)
        return None

    @property
    def has_opened(self) -> bool:
        """True if someone has made a non-pass bid."""
        return any(not b.is_pass for b in self._bids)

    def partner_last_bid(self, seat: Seat) -> Bid | None:
        """Most recent non-pass bid by seat's partner."""
        partner = seat.partner
        for s, b in reversed(self.bids):
            if s == partner and not b.is_pass:
                return b
        return None

    def rho_last_bid(self, seat: Seat) -> Bid | None:
        """Most recent non-pass bid by right-hand opponent."""
        rho = seat.rho
        for s, b in reversed(self.bids):
            if s == rho and not b.is_pass:
                return b
        return None

    def bids_by(self, seat: Seat) -> list[Bid]:
        """All bids made by a specific seat."""
        return [b for s, b in self.bids if s == seat]

    def is_competitive(self) -> bool:
        """Whether opponents of the opening side have entered the auction."""
        opening = self.opening_bid
        if opening is None:
            return False
        opening_seat = opening[0]
        opponents = {opening_seat.lho, opening_seat.rho}
        return any(s in opponents and b.bid_type == BidType.SUIT for s, b in self.bids)

    def add_bid(self, bid: Bid) -> None:
        """Add a bid, validating legality.

        Raises IllegalBidError if the bid is not legal in the current state.
        """
        if self.is_complete:
            raise IllegalBidError("Auction is already complete")

        last_contract = self.last_contract_bid

        if bid.bid_type == BidType.SUIT:
            # Suit bid must be higher than the current contract
            if last_contract is not None and bid <= last_contract:
                raise IllegalBidError(
                    f"Bid {bid} is not higher than current contract {last_contract}"
                )

        elif bid.bid_type == BidType.DOUBLE:
            # Can only double an opponent's last suit bid
            if last_contract is None:
                raise IllegalBidError("Cannot double: no bid to double")
            # Find who made the last contract bid
            last_bidder: Seat | None = None
            for s, b in reversed(self.bids):
                if b.bid_type == BidType.SUIT:
                    last_bidder = s
                    break
            if last_bidder is None:
                raise IllegalBidError("Cannot double: no bid to double")
            current = self.current_seat
            if last_bidder == current or last_bidder == current.partner:
                raise IllegalBidError("Cannot double your own side's bid")
            if self._is_doubled() or self._is_redoubled():
                raise IllegalBidError("Bid is already doubled")

        elif bid.bid_type == BidType.REDOUBLE:
            # Can only redouble a doubled bid by the opponents
            if not self._is_doubled():
                raise IllegalBidError("Cannot redouble: bid is not doubled")
            if self._is_redoubled():
                raise IllegalBidError("Bid is already redoubled")

        self._bids.append(bid)

    def _is_doubled(self) -> bool:
        """Check if the current contract is doubled (not redoubled)."""
        for bid in reversed(self._bids):
            if bid.bid_type in (BidType.SUIT, BidType.REDOUBLE):
                return False
            if bid.bid_type == BidType.DOUBLE:
                return True
        return False

    def _is_redoubled(self) -> bool:
        """Check if the current contract is redoubled."""
        for bid in reversed(self._bids):
            if bid.bid_type in (BidType.SUIT, BidType.DOUBLE):
                return False
            if bid.bid_type == BidType.REDOUBLE:
                return True
        return False
