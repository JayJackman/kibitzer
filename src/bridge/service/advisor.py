"""BiddingAdvisor - wraps the engine pipeline into a single call."""

from __future__ import annotations

from bridge.engine.context import BiddingContext
from bridge.engine.sayc import create_sayc_registry
from bridge.engine.selector import BidSelector
from bridge.model.auction import AuctionState
from bridge.model.board import Board
from bridge.model.hand import Hand

from .models import BiddingAdvice, HandEvaluation


class BiddingAdvisor:
    """Provides bid recommendations using the SAYC rule engine."""

    def __init__(self) -> None:
        registry = create_sayc_registry()
        self._selector = BidSelector(registry)

    def advise(self, hand: Hand, auction: AuctionState) -> BiddingAdvice:
        """Get a bid recommendation for the given hand and auction state.

        The seat is inferred from auction.current_seat.
        """
        board = Board(hand=hand, seat=auction.current_seat, auction=auction)
        ctx = BiddingContext(board)

        recommended = self._selector.select(ctx)
        all_candidates = self._selector.candidates(ctx)
        alternatives = [
            c for c in all_candidates if c.rule_name != recommended.rule_name
        ]
        phase = self._selector.detect_phase(ctx)

        hand_evaluation = HandEvaluation(
            hcp=ctx.hcp,
            length_points=ctx.length_pts,
            total_points=ctx.total_pts,
            distribution_points=ctx.distribution_pts,
            controls=ctx.controls,
            quick_tricks=ctx.quick_tricks,
            losers=ctx.losers,
            shape=ctx.shape,
            sorted_shape=ctx.sorted_shape,
            is_balanced=ctx.is_balanced,
            is_semi_balanced=ctx.is_semi_balanced,
            longest_suit=ctx.longest_suit,
        )

        return BiddingAdvice(
            recommended=recommended,
            alternatives=alternatives,
            hand_evaluation=hand_evaluation,
            phase=phase,
        )
