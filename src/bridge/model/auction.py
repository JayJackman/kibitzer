"""Auction state tracking for bridge bidding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique

from .bid import (
    Bid,
    is_double,
    is_pass,
    is_redouble,
    is_suit_bid,
    parse_bid,
)
from .card import Suit


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
            return NO_VULNERABILITY
        if text == "NS":
            return NS_VULNERABLE
        if text == "EW":
            return EW_VULNERABLE
        if text in ("BOTH", "ALL"):
            return BOTH_VULNERABLE
        raise ValueError(f"Invalid vulnerability: {text!r}")


NO_VULNERABILITY = Vulnerability()
NS_VULNERABLE = Vulnerability(ns_vulnerable=True)
EW_VULNERABLE = Vulnerability(ew_vulnerable=True)
BOTH_VULNERABLE = Vulnerability(ns_vulnerable=True, ew_vulnerable=True)


@dataclass(frozen=True)
class Contract:
    """Result of a completed auction."""

    level: int
    suit: Suit
    declarer: Seat
    doubled: bool = False
    redoubled: bool = False
    passed_out: bool = False

    def __str__(self) -> str:
        if self.passed_out:
            return "Passed out"
        bid = f"{self.level}{self.suit.letter}"
        declarer = self.declarer.name.capitalize()
        if self.redoubled:
            return f"{bid} by {declarer} redoubled"
        if self.doubled:
            return f"{bid} by {declarer} doubled"
        return f"{bid} by {declarer}"


class IllegalBidError(Exception):
    """Raised when an illegal bid is attempted."""


@dataclass
class AuctionState:
    """Tracks the full auction history and derived state.

    Bids are stored in order. The seat for each bid is derived from
    the dealer and the bid's position in the list.
    """

    dealer: Seat
    vulnerability: Vulnerability = field(default=NO_VULNERABILITY)
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
        if all(is_pass(b) for b in self._bids):
            return True
        # Three consecutive passes after at least one non-pass bid
        return all(is_pass(b) for b in self._bids[-3:])

    @property
    def last_contract_bid(self) -> Bid | None:
        """Most recent suit bid (not pass/double/redouble)."""
        for bid in reversed(self._bids):
            if is_suit_bid(bid):
                return bid
        return None

    @property
    def opening_bid(self) -> tuple[Seat, Bid] | None:
        """First non-pass bid and who made it."""
        for seat, bid in self.bids:
            if is_suit_bid(bid):
                return (seat, bid)
        return None

    @property
    def has_opened(self) -> bool:
        """True if someone has made a non-pass bid."""
        return any(not is_pass(b) for b in self._bids)

    def partner_last_bid(self, seat: Seat) -> Bid | None:
        """Most recent non-pass bid by seat's partner."""
        partner = seat.partner
        for s, b in reversed(self.bids):
            if s == partner and not is_pass(b):
                return b
        return None

    def rho_last_bid(self, seat: Seat) -> Bid | None:
        """Most recent non-pass bid by right-hand opponent."""
        rho = seat.rho
        for s, b in reversed(self.bids):
            if s == rho and not is_pass(b):
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
        return any(s in opponents and is_suit_bid(b) for s, b in self.bids)

    def add_bid(self, bid: Bid) -> None:
        """Add a bid, validating legality.

        Raises IllegalBidError if the bid is not legal in the current state.
        """
        if self.is_complete:
            raise IllegalBidError("Auction is already complete")

        last_contract = self.last_contract_bid

        if is_suit_bid(bid):
            # Suit bid must be higher than the current contract
            if last_contract is not None and bid <= last_contract:
                raise IllegalBidError(
                    f"Bid {bid} is not higher than current contract {last_contract}"
                )

        elif is_double(bid) and not self.can_double:
            raise IllegalBidError("Cannot double in this position")

        elif is_redouble(bid) and not self.can_redouble:
            raise IllegalBidError("Cannot redouble in this position")

        self._bids.append(bid)

    @property
    def contract(self) -> Contract | None:
        """The contract if auction is complete, None otherwise."""
        if not self.is_complete:
            return None

        # All passes = passed out
        if all(is_pass(b) for b in self._bids):
            return Contract(
                level=0, suit=Suit.CLUBS, declarer=self.dealer, passed_out=True
            )

        last_bidder, last_bid = next(
            (seat, bid) for seat, bid in reversed(self.bids) if is_suit_bid(bid)
        )

        # Declarer: first player on the declaring side who bid this suit
        declaring_side = {last_bidder, last_bidder.partner}
        for seat, bid in self.bids:
            if (
                seat in declaring_side
                and is_suit_bid(bid)
                and bid.suit == last_bid.suit
            ):
                return Contract(
                    level=last_bid.level,
                    suit=last_bid.suit,
                    declarer=seat,
                    doubled=self.is_doubled,
                    redoubled=self.is_redoubled,
                )

        raise AssertionError("Could not determine declarer")  # pragma: no cover

    @property
    def is_doubled(self) -> bool:
        """Check if the current contract is doubled (not redoubled)."""
        for bid in reversed(self._bids):
            if is_suit_bid(bid) or is_redouble(bid):
                return False
            if is_double(bid):
                return True
        return False

    @property
    def is_redoubled(self) -> bool:
        """Check if the current contract is redoubled."""
        for bid in reversed(self._bids):
            if is_suit_bid(bid) or is_double(bid):
                return False
            if is_redouble(bid):
                return True
        return False

    @property
    def can_double(self) -> bool:
        """Whether a double is legal for the current seat."""
        if self.last_contract_bid is None:
            return False
        if self.is_doubled or self.is_redoubled:
            return False
        # Can only double an opponent's bid
        for seat, bid in reversed(self.bids):
            if is_suit_bid(bid):
                current = self.current_seat
                return seat != current and seat != current.partner
        return False

    @property
    def can_redouble(self) -> bool:
        """Whether a redouble is legal for the current seat."""
        return self.is_doubled and not self.is_redoubled


def parse_auction(
    text: str,
    dealer: Seat = Seat.NORTH,
    vulnerability: Vulnerability = NO_VULNERABILITY,
) -> AuctionState:
    """Parse an auction string into an AuctionState.

    Args:
        text: Space-separated bid strings, e.g. "1H P 2H P"
        dealer: Who dealt (default North)
        vulnerability: Vulnerability state

    Returns:
        AuctionState with all bids added.

    Raises:
        ValueError: If any bid string is invalid
        IllegalBidError: If any bid is illegal in sequence
    """
    auction = AuctionState(dealer=dealer, vulnerability=vulnerability)
    for token in text.split():
        auction.add_bid(parse_bid(token))
    return auction
