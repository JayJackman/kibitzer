"""PracticeSession -- core state machine for bidding practice.

Supports three modes:
- Solo practice: 1 human + 3 computers, random deals, engine feedback.
- Multiplayer practice: 1-4 humans + computers, random deals, engine feedback.
- Helper mode: companion for physical bridge. Players enter real hands,
  enter bids as they happen at the table, and get engine advice on demand.
  No random dealing, no computer auto-bidding. Any seated player can
  proxy-bid for unoccupied seats.
"""

from __future__ import annotations

import enum
import logging
import random
import uuid
from dataclasses import dataclass

from bridge import evaluate
from bridge.model.auction import (
    BOTH_VULNERABLE,
    EW_VULNERABLE,
    NO_VULNERABILITY,
    NS_VULNERABLE,
    AuctionState,
    Contract,
    Seat,
    Vulnerability,
)
from bridge.model.bid import Bid, SuitBid, parse_bid
from bridge.model.card import Card, Suit
from bridge.model.hand import Hand
from bridge.scoring.rubber import RubberState, RubberTracker
from bridge.service.advisor import BiddingAdvisor
from bridge.service.deal import deal
from bridge.service.models import BiddingAdvice, HandEvaluation

logger = logging.getLogger(__name__)


class SessionMode(enum.Enum):
    """The type of practice session."""

    PRACTICE = "practice"
    HELPER = "helper"


@dataclass(frozen=True)
class ComputerBidRecord:
    """A bid placed by a computer-controlled seat."""

    seat: Seat
    bid: Bid
    explanation: str


@dataclass(frozen=True)
class BidResult:
    """Feedback returned after the human places a bid."""

    matched_engine: bool
    engine_bid: str
    engine_explanation: str
    computer_bids: list[ComputerBidRecord]
    auction_complete: bool
    contract: Contract | None


@dataclass(frozen=True)
class PracticeState:
    """Filtered view of a session for a specific user."""

    id: str
    mode: SessionMode
    join_code: str
    your_seat: Seat
    hand: Hand | None
    hand_evaluation: HandEvaluation | None
    auction: AuctionState
    computer_bids: list[ComputerBidRecord]
    bid_explanations: dict[int, str]
    bid_matched: dict[int, bool]
    is_my_turn: bool
    legal_bids: list[str]
    last_feedback: BidResult | None
    all_hands: dict[Seat, Hand] | None
    hand_number: int
    players: dict[Seat, str | None]
    waiting_for: Seat | None
    can_proxy_bid: bool
    proxy_seat: Seat | None
    can_undo: bool
    scoring: RubberState | None


_ALL_VULNERABILITIES = [
    NO_VULNERABILITY,
    NS_VULNERABLE,
    EW_VULNERABLE,
    BOTH_VULNERABLE,
]


class PlayerNotFoundError(Exception):
    """Raised when a user_id is not seated at the session."""


class NotYourTurnError(Exception):
    """Raised when a player tries to bid out of turn."""


class AuctionCompleteError(Exception):
    """Raised when trying to bid after the auction is over."""


class SeatOccupiedError(Exception):
    """Raised when trying to join a seat that already has a human player."""


class AlreadySeatedError(Exception):
    """Raised when a user who is already seated tries to join another seat."""


class HelperModeOnlyError(Exception):
    """Raised when an operation is only allowed in helper mode."""


class HandNotSetError(Exception):
    """Raised when an operation requires a hand that hasn't been entered yet."""


class DuplicateCardError(Exception):
    """Raised when a hand contains cards that already appear in another seat's hand."""


class NoBidsToUndoError(Exception):
    """Raised when undo is requested but there are no human bids to undo."""


def compute_legal_bids(auction: AuctionState) -> list[str]:
    """Return all legal bid strings for the current position."""
    legal = ["Pass"]
    last = auction.last_contract_bid
    for level in range(1, 8):
        for suit in Suit:
            bid = SuitBid(level, suit)
            if last is None or bid > last:
                legal.append(f"{level}{suit.letter}")
    if auction.can_double:
        legal.append("X")
    if auction.can_redouble:
        legal.append("XX")
    return legal


class PracticeSession:
    """Core state machine for a practice bidding session.

    Manages hands, auction, computer bidding, and advice. The ``players``
    dict maps each seat to a user_id (human) or None (computer). For solo
    practice, exactly one seat has a user_id; the rest are None.

    Multi-player ready: methods take ``user_id`` and look up the seat from
    ``players``, so adding more human seats later requires no structural
    changes.
    """

    # Characters for join codes (no ambiguous I/O/0/1).
    _JOIN_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    def __init__(
        self,
        user_id: int,
        seat: Seat,
        advisor: BiddingAdvisor,
        *,
        mode: SessionMode = SessionMode.PRACTICE,
        username: str = "",
        rng: random.Random | None = None,
        dealer: Seat | None = None,
        vulnerability: Vulnerability | None = None,
    ) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.host_user_id: int = user_id
        self.mode: SessionMode = mode
        self.join_code: str = "".join(random.choices(self._JOIN_CODE_CHARS, k=6))
        self.advisor: BiddingAdvisor = advisor
        self._rng: random.Random | None = rng

        # All seats default to computer (None); assign the human's seat.
        self.players: dict[Seat, int | None] = {s: None for s in Seat}
        self.players[seat] = user_id

        # Maps user_id -> username for display in the UI.
        self._usernames: dict[int, str] = {}
        if username:
            self._usernames[user_id] = username

        self.hand_number: int = 1

        if mode == SessionMode.HELPER:
            # Helper mode: no random deal -- hands entered manually via set_hand().
            self.hands: dict[Seat, Hand | None] = {s: None for s in Seat}
            self.auction: AuctionState = AuctionState(
                dealer=dealer if dealer is not None else seat,
                vulnerability=(
                    vulnerability if vulnerability is not None else NO_VULNERABILITY
                ),
            )
        else:
            # Practice mode: random deal, auto-assign dealer/vulnerability.
            # Explicit annotation widens dict[Seat, Hand] to dict[Seat, Hand | None]
            # (dict is invariant, so assignment alone would fail the type check).
            self.hands = dict[Seat, Hand | None](deal(rng=self._rng))
            self.auction = AuctionState(
                dealer=seat,
                vulnerability=random.choice(_ALL_VULNERABILITIES),
            )

        # Cache hand evaluations per seat (computed once per deal, since
        # eval depends only on the hand, not the auction state).
        self._hand_evals: dict[Seat, HandEvaluation] = self._compute_evals()

        # Maps bid index (position in auction.bids) to the engine's
        # explanation for that bid. Populated for both computer and player
        # bids so the frontend can show explanations in the auction history.
        self._bid_explanations: dict[int, str] = {}

        # Tracks whether each player bid matched the engine's recommendation.
        # Only populated for human bids (not computer bids).
        self._bid_matched: dict[int, bool] = {}

        # Run any computer bids before the human's first turn.
        # Helper mode skips this entirely (no computer auto-bidding).
        self._last_computer_bids: list[ComputerBidRecord] = self._run_computer_bids()
        self._last_feedback: BidResult | None = None

        # Rubber bridge scoring (helper mode only, lazy-initialized).
        self.rubber: RubberTracker | None = None

        # Track how many bids were placed before the first human turn.
        # Undo/reset never go past this point -- these initial computer
        # bids are the "starting position" of the hand.
        self._initial_bid_count: int = self.auction.bid_count

        logger.info(
            "Session %s created (mode=%s, join_code=%s)",
            self.id,
            mode.value,
            self.join_code,
        )

    # ── Public API ───────────────────────────────────────────────

    def seat_for(self, user_id: int) -> Seat:
        """Look up the seat occupied by a user_id."""
        for seat, uid in self.players.items():
            if uid == user_id:
                return seat
        raise PlayerNotFoundError(f"User {user_id} is not seated at this session")

    def available_seats(self) -> list[Seat]:
        """Return seats not occupied by a human player."""
        return [seat for seat, uid in self.players.items() if uid is None]

    def join(self, user_id: int, seat: Seat, *, username: str = "") -> None:
        """Claim an unoccupied seat for a human player."""
        # Check if user is already seated somewhere.
        for s, uid in self.players.items():
            if uid == user_id:
                raise AlreadySeatedError(f"User {user_id} is already seated at {s}")
        if self.players[seat] is not None:
            raise SeatOccupiedError(f"Seat {seat} is already occupied")
        self.players[seat] = user_id
        if username:
            self._usernames[user_id] = username
        logger.info("User %d joined session %s at seat %s", user_id, self.id, seat.name)

    def leave(self, user_id: int) -> None:
        """Revert a human's seat to computer control.

        After removing the player, run computer bids so the auction
        doesn't stall if it was this player's turn.
        """
        seat = self.seat_for(user_id)  # Raises PlayerNotFoundError if absent.
        self.players[seat] = None
        self._usernames.pop(user_id, None)
        logger.info("User %d left session %s (seat %s)", user_id, self.id, seat.name)
        self._last_computer_bids = self._run_computer_bids()

    def set_hand(self, user_id: int, seat: Seat, hand: Hand) -> None:
        """Set the hand for a seat (helper mode only).

        Any seated player can set any seat's hand (e.g., one player enters
        all four hands from the physical deal). Validates that no card in
        the new hand duplicates a card already in another seat's hand.
        """
        if self.mode != SessionMode.HELPER:
            raise HelperModeOnlyError("set_hand is only allowed in helper mode")
        self.seat_for(user_id)  # Raises PlayerNotFoundError if not seated.

        # Cross-hand duplicate check: collect all cards from other seats.
        existing_cards: set[Card] = set()
        for s in Seat:
            other = self.hands[s]
            if s != seat and other is not None:
                existing_cards |= other.cards
        overlap = hand.cards & existing_cards
        if overlap:
            names = ", ".join(str(c) for c in sorted(overlap))
            raise DuplicateCardError(f"Cards already in another hand: {names}")

        self.hands[seat] = hand
        self._hand_evals[seat] = self._compute_eval(hand)
        logger.info("Hand set for seat %s in session %s", seat.name, self.id)

    def _player_names(self) -> dict[Seat, str | None]:
        """Map each seat to its player's username (None = computer)."""
        return {
            seat: self._usernames.get(uid, "") if uid is not None else None
            for seat, uid in self.players.items()
        }

    def _waiting_for(self) -> Seat | None:
        """Which human seat the session is waiting on, if any."""
        if self.auction.is_complete:
            return None
        current = self.auction.current_seat
        if self.players[current] is not None:
            return current
        return None

    def get_state(self, user_id: int) -> PracticeState:
        """Filtered view: only the human's hand, full auction, legal bids."""
        seat = self.seat_for(user_id)

        is_my_turn = not self.auction.is_complete and self.auction.current_seat == seat
        legal_bids = compute_legal_bids(self.auction) if is_my_turn else []

        # Reveal all hands only when the auction is complete.
        # In helper mode, only include seats that have a hand set.
        all_hands: dict[Seat, Hand] | None = None
        if self.auction.is_complete:
            all_hands = {s: h for s, h in self.hands.items() if h is not None}

        # Helper mode: proxy bidding lets any seated player bid for
        # unoccupied seats. Compute whether the current seat is unoccupied
        # and the caller is seated (already verified above via seat_for).
        can_proxy = False
        proxy_seat: Seat | None = None
        if (
            self.mode == SessionMode.HELPER
            and not self.auction.is_complete
            and not is_my_turn
        ):
            current = self.auction.current_seat
            if self.players[current] is None:
                can_proxy = True
                proxy_seat = current
                # In proxy mode, also provide legal bids for the proxy seat.
                legal_bids = compute_legal_bids(self.auction)

        return PracticeState(
            id=self.id,
            mode=self.mode,
            join_code=self.join_code,
            your_seat=seat,
            hand=self.hands[seat],
            hand_evaluation=self._hand_evals.get(seat),
            auction=self.auction,
            computer_bids=list(self._last_computer_bids),
            bid_explanations=dict(self._bid_explanations),
            bid_matched=dict(self._bid_matched),
            is_my_turn=is_my_turn,
            legal_bids=legal_bids,
            last_feedback=self._last_feedback,
            all_hands=all_hands,
            hand_number=self.hand_number,
            players=self._player_names(),
            waiting_for=self._waiting_for(),
            can_proxy_bid=can_proxy,
            proxy_seat=proxy_seat,
            can_undo=self.can_undo,
            scoring=self.rubber.get_state() if self.rubber else None,
        )

    def place_bid(
        self, user_id: int, bid_str: str, *, for_seat: Seat | None = None
    ) -> BidResult:
        """Validate and add a bid, then run computer bids.

        In practice mode, the caller bids for their own seat.
        In helper mode, ``for_seat`` allows any seated player to bid on
        behalf of an unoccupied seat (proxy bidding).
        """
        caller_seat = self.seat_for(user_id)

        if self.auction.is_complete:
            raise AuctionCompleteError("The auction is already complete")

        # Determine which seat is actually bidding.
        if for_seat is not None:
            if self.mode != SessionMode.HELPER:
                raise HelperModeOnlyError(
                    "Proxy bidding (for_seat) is only allowed in helper mode"
                )
            if self.players[for_seat] is not None:
                raise NotYourTurnError(
                    f"Seat {for_seat} is occupied -- they must bid themselves"
                )
            bidding_seat = for_seat
        else:
            bidding_seat = caller_seat

        if self.auction.current_seat != bidding_seat:
            raise NotYourTurnError("It is not your turn to bid")

        bid = parse_bid(bid_str)

        # Get the engine's advice *before* adding the bid (if the hand
        # is available for comparison).
        hand = self.hands[bidding_seat]
        if hand is not None:
            advice = self.advisor.advise(hand, self.auction)
            engine_bid = advice.recommended.bid
            engine_explanation = advice.recommended.explanation
            matched = bid == engine_bid
        else:
            # Hand not set (helper mode) -- can't compare to engine.
            engine_bid = None
            engine_explanation = ""
            matched = False

        # Record the engine's explanation and match status for this bid
        # position before adding it (so len(bids) gives us the correct index).
        bid_index = self.auction.bid_count
        if engine_explanation:
            self._bid_explanations[bid_index] = engine_explanation
        if hand is not None:
            self._bid_matched[bid_index] = matched

        # This raises IllegalBidError if the bid is not legal.
        self.auction.add_bid(bid)
        logger.info("User %d bid %s in session %s", user_id, bid_str, self.id)

        # Run computer bids after the bid (no-op in helper mode).
        computer_bids = self._run_computer_bids()
        self._last_computer_bids = computer_bids

        # Auto-populate scoring entry when auction completes in helper mode.
        if (
            self.rubber is not None
            and self.auction.is_complete
            and self.auction.contract is not None
            and not self.auction.contract.passed_out
        ):
            self.rubber.auto_populate_contract(self.auction.contract)

        result = BidResult(
            matched_engine=matched,
            engine_bid=str(engine_bid) if engine_bid is not None else "",
            engine_explanation=engine_explanation,
            computer_bids=computer_bids,
            auction_complete=self.auction.is_complete,
            contract=self.auction.contract,
        )
        self._last_feedback = result
        return result

    def get_advice(self, user_id: int) -> BiddingAdvice:
        """Engine recommendation for the human's current position."""
        seat = self.seat_for(user_id)
        hand = self.hands[seat]
        if hand is None:
            raise HandNotSetError(f"Hand for seat {seat} has not been entered yet")
        return self.advisor.advise(hand, self.auction)

    def redeal(
        self,
        *,
        dealer: Seat | None = None,
        vulnerability: Vulnerability | None = None,
    ) -> None:
        """Start a new hand.

        Practice mode: deal new random hands, rotate dealer, random vulnerability.
        Helper mode: clear all hands (to be re-entered via set_hand()),
        reset auction. Accepts optional dealer/vulnerability overrides;
        defaults to rotating dealer and keeping the same vulnerability.
        """
        self.hand_number += 1
        next_dealer = Seat((self.auction.dealer.value + 1) % 4)

        if self.mode == SessionMode.HELPER:
            self.hands = {s: None for s in Seat}
            # Determine vulnerability: explicit override > rubber state > previous.
            if vulnerability is not None:
                vuln = vulnerability
            elif self.rubber is not None:
                vuln = self.rubber.current_vulnerability()
            else:
                vuln = self.auction.vulnerability
            self.auction = AuctionState(
                dealer=dealer if dealer is not None else next_dealer,
                vulnerability=vuln,
            )
        else:
            self.hands = dict[Seat, Hand | None](deal(rng=self._rng))
            self.auction = AuctionState(
                dealer=next_dealer,
                vulnerability=random.choice(_ALL_VULNERABILITIES),
            )

        self._hand_evals = self._compute_evals()
        self._bid_explanations = {}
        self._bid_matched = {}
        self._last_computer_bids = self._run_computer_bids()
        self._last_feedback = None
        self._initial_bid_count = self.auction.bid_count
        logger.info("Session %s redeal (hand #%d)", self.id, self.hand_number)

    @property
    def can_undo(self) -> bool:
        """Whether there are bids that can be undone."""
        return self.auction.bid_count > self._initial_bid_count

    def undo_bid(self, user_id: int) -> int:
        """Undo the last round of bids.

        Practice mode: removes the last human bid and all computer bids
        that followed it, restoring the auction to the state before the
        last ``place_bid()`` call.
        Helper mode: removes exactly one bid.

        Returns the number of bids removed.
        """
        self.seat_for(user_id)  # verify caller is seated

        if not self.can_undo:
            raise NoBidsToUndoError("No bids to undo")

        removed = 0
        while self.auction.bid_count > self._initial_bid_count:
            seat, _ = self.auction.remove_last_bid()
            # After removal, bid_count equals the index of the removed bid.
            self._bid_explanations.pop(self.auction.bid_count, None)
            self._bid_matched.pop(self.auction.bid_count, None)
            removed += 1

            if self.mode == SessionMode.HELPER:
                break  # One bid at a time in helper mode

            # Practice mode: keep popping computer bids until we've
            # removed the human bid that triggered them.
            if self.players[seat] is not None:
                break

        self._last_feedback = None
        self._last_computer_bids = []
        logger.info("Session %s undo (%d bids removed)", self.id, removed)
        return removed

    def reset_auction(self, user_id: int) -> int:
        """Remove all bids back to the initial state.

        Keeps hands, dealer, vulnerability, and initial computer bids
        intact. Returns the number of bids removed.
        """
        self.seat_for(user_id)  # verify caller is seated

        removed = self.auction.bid_count - self._initial_bid_count
        self.auction.truncate(self._initial_bid_count)
        # Drop metadata for all removed bid indices.
        for idx in range(self._initial_bid_count, self._initial_bid_count + removed):
            self._bid_explanations.pop(idx, None)
            self._bid_matched.pop(idx, None)

        self._last_feedback = None
        self._last_computer_bids = []
        logger.info("Session %s reset (%d bids removed)", self.id, removed)
        return removed

    # ── Internals ────────────────────────────────────────────────

    @staticmethod
    def _compute_eval(hand: Hand) -> HandEvaluation:
        """Build a HandEvaluation for a single hand."""
        return HandEvaluation(
            hcp=evaluate.hcp(hand),
            length_points=evaluate.length_points(hand),
            total_points=evaluate.total_points(hand),
            distribution_points=evaluate.distribution_points(hand),
            controls=evaluate.controls(hand),
            quick_tricks=evaluate.quick_tricks(hand),
            losers=evaluate.losing_trick_count(hand),
            shape=hand.shape,
            sorted_shape=hand.sorted_shape,
            is_balanced=hand.is_balanced,
            is_semi_balanced=hand.is_semi_balanced,
            longest_suit=hand.longest_suit,
        )

    def _compute_evals(self) -> dict[Seat, HandEvaluation]:
        """Build HandEvaluation for each seat that has a hand."""
        evals: dict[Seat, HandEvaluation] = {}
        for seat in Seat:
            hand = self.hands[seat]
            if hand is not None:
                evals[seat] = self._compute_eval(hand)
        return evals

    def _run_computer_bids(self) -> list[ComputerBidRecord]:
        """Advance all computer seats until it's a human's turn or auction ends.

        In helper mode, no computer auto-bidding occurs -- all bids are
        entered manually (either by the seated player or via proxy bidding).
        """
        if self.mode == SessionMode.HELPER:
            return []
        computer_bids: list[ComputerBidRecord] = []
        while not self.auction.is_complete:
            current = self.auction.current_seat
            if self.players[current] is not None:
                break  # Human's turn
            hand = self.hands[current]
            assert hand is not None  # Practice mode always has dealt hands.
            advice = self.advisor.advise(hand, self.auction)
            self._bid_explanations[self.auction.bid_count] = (
                advice.recommended.explanation
            )
            self.auction.add_bid(advice.recommended.bid)
            computer_bids.append(
                ComputerBidRecord(
                    seat=current,
                    bid=advice.recommended.bid,
                    explanation=advice.recommended.explanation,
                )
            )
        return computer_bids
