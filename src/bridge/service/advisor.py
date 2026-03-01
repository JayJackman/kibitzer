"""BiddingAdvisor - wraps the engine pipeline into a single call."""

from __future__ import annotations

from bridge import evaluate
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, RuleResult
from bridge.engine.sayc import create_sayc_registry
from bridge.engine.selector import BidSelector, ThoughtProcess
from bridge.model.auction import AuctionState
from bridge.model.bid import PASS
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
        Returns a minimal result if the auction is already complete.
        """
        if auction.is_complete:
            complete = RuleResult(
                bid=PASS,
                rule_name="auction.complete",
                explanation="Auction is complete",
            )
            return BiddingAdvice(
                recommended=complete,
                alternatives=[],
                hand_evaluation=_build_hand_eval(hand),
                phase=Category.OPENING,
                thought_process=ThoughtProcess(steps=(), selected=complete),
            )

        board = Board(hand=hand, seat=auction.current_seat, auction=auction)
        ctx = BiddingContext(board)

        thought_process = self._selector.think(ctx)
        recommended = thought_process.selected
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
            thought_process=thought_process,
        )


def _build_hand_eval(hand: Hand) -> HandEvaluation:
    """Build HandEvaluation directly from a Hand without the engine pipeline."""
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
