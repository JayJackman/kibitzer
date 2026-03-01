"""PracticeSession -- core state machine for solo bidding practice."""

from __future__ import annotations

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
)
from bridge.model.bid import Bid, SuitBid, parse_bid
from bridge.model.card import Suit
from bridge.model.hand import Hand
from bridge.service.advisor import BiddingAdvisor
from bridge.service.deal import deal
from bridge.service.models import BiddingAdvice, HandEvaluation


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
    your_seat: Seat
    hand: Hand
    hand_evaluation: HandEvaluation
    auction: AuctionState
    computer_bids: list[ComputerBidRecord]
    bid_explanations: dict[int, str]
    bid_matched: dict[int, bool]
    is_my_turn: bool
    legal_bids: list[str]
    last_feedback: BidResult | None
    all_hands: dict[Seat, Hand] | None
    hand_number: int


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

    def __init__(
        self,
        user_id: int,
        seat: Seat,
        advisor: BiddingAdvisor,
        *,
        rng: random.Random | None = None,
    ) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.host_user_id: int = user_id
        self.advisor: BiddingAdvisor = advisor
        self._rng: random.Random | None = rng

        # All seats default to computer (None); assign the human's seat.
        self.players: dict[Seat, int | None] = {s: None for s in Seat}
        self.players[seat] = user_id

        self.hand_number: int = 1
        self.hands: dict[Seat, Hand] = deal(rng=self._rng)
        self.auction: AuctionState = AuctionState(
            dealer=seat, vulnerability=random.choice(_ALL_VULNERABILITIES)
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
        self._last_computer_bids: list[ComputerBidRecord] = self._run_computer_bids()
        self._last_feedback: BidResult | None = None

    # ── Public API ───────────────────────────────────────────────

    def seat_for(self, user_id: int) -> Seat:
        """Look up the seat occupied by a user_id."""
        for seat, uid in self.players.items():
            if uid == user_id:
                return seat
        raise PlayerNotFoundError(f"User {user_id} is not seated at this session")

    def get_state(self, user_id: int) -> PracticeState:
        """Filtered view: only the human's hand, full auction, legal bids."""
        seat = self.seat_for(user_id)

        is_my_turn = not self.auction.is_complete and self.auction.current_seat == seat
        legal_bids = compute_legal_bids(self.auction) if is_my_turn else []

        # Reveal all hands only when the auction is complete.
        all_hands = dict(self.hands) if self.auction.is_complete else None

        return PracticeState(
            id=self.id,
            your_seat=seat,
            hand=self.hands[seat],
            hand_evaluation=self._hand_evals[seat],
            auction=self.auction,
            computer_bids=list(self._last_computer_bids),
            bid_explanations=dict(self._bid_explanations),
            bid_matched=dict(self._bid_matched),
            is_my_turn=is_my_turn,
            legal_bids=legal_bids,
            last_feedback=self._last_feedback,
            all_hands=all_hands,
            hand_number=self.hand_number,
        )

    def place_bid(self, user_id: int, bid_str: str) -> BidResult:
        """Validate and add the human's bid, then run computer bids."""
        seat = self.seat_for(user_id)

        if self.auction.is_complete:
            raise AuctionCompleteError("The auction is already complete")
        if self.auction.current_seat != seat:
            raise NotYourTurnError("It is not your turn to bid")

        bid = parse_bid(bid_str)

        # Get the engine's advice *before* adding the human's bid.
        advice = self.advisor.advise(self.hands[seat], self.auction)
        engine_bid = advice.recommended.bid

        # Record the engine's explanation and match status for this bid
        # position before adding it (so len(bids) gives us the correct index).
        bid_index = len(self.auction.bids)
        self._bid_explanations[bid_index] = advice.recommended.explanation
        self._bid_matched[bid_index] = bid == engine_bid

        # This raises IllegalBidError if the bid is not legal.
        self.auction.add_bid(bid)

        # Run computer bids after the human's bid.
        computer_bids = self._run_computer_bids()
        self._last_computer_bids = computer_bids

        result = BidResult(
            matched_engine=(bid == engine_bid),
            engine_bid=str(engine_bid),
            engine_explanation=advice.recommended.explanation,
            computer_bids=computer_bids,
            auction_complete=self.auction.is_complete,
            contract=self.auction.contract,
        )
        self._last_feedback = result
        return result

    def get_advice(self, user_id: int) -> BiddingAdvice:
        """Engine recommendation for the human's current position."""
        seat = self.seat_for(user_id)
        return self.advisor.advise(self.hands[seat], self.auction)

    def redeal(self) -> None:
        """Deal new hands, rotate dealer, pick random vulnerability."""
        self.hand_number += 1
        self.hands = deal(rng=self._rng)
        self._hand_evals = self._compute_evals()
        next_dealer = Seat((self.auction.dealer.value + 1) % 4)
        self.auction = AuctionState(
            dealer=next_dealer,
            vulnerability=random.choice(_ALL_VULNERABILITIES),
        )
        self._bid_explanations = {}
        self._bid_matched = {}
        self._last_computer_bids = self._run_computer_bids()
        self._last_feedback = None

    # ── Internals ────────────────────────────────────────────────

    def _compute_evals(self) -> dict[Seat, HandEvaluation]:
        """Build HandEvaluation for each seat from the current hands."""
        evals: dict[Seat, HandEvaluation] = {}
        for seat in Seat:
            hand = self.hands[seat]
            evals[seat] = HandEvaluation(
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
        return evals

    def _run_computer_bids(self) -> list[ComputerBidRecord]:
        """Advance all computer seats until it's a human's turn or auction ends."""
        computer_bids: list[ComputerBidRecord] = []
        while not self.auction.is_complete:
            current = self.auction.current_seat
            if self.players[current] is not None:
                break  # Human's turn
            advice = self.advisor.advise(self.hands[current], self.auction)
            self._bid_explanations[len(self.auction.bids)] = (
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
