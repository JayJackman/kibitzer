"""Tests for CLI display formatters."""

from io import StringIO

from rich.console import Console

from bridge.cli.display import (
    format_advice,
    format_alternatives,
    format_auction,
    format_bid,
    format_bid_prompt,
    format_contract,
    format_hand,
    format_hand_eval,
    format_thought_process,
)
from bridge.engine.condition import ConditionResult
from bridge.engine.rule import RuleResult
from bridge.engine.selector import ThoughtProcess, ThoughtStep
from bridge.model.auction import Contract, Seat
from bridge.model.bid import DOUBLE, PASS, REDOUBLE, SuitBid
from bridge.model.card import Suit
from bridge.model.hand import Hand
from bridge.service.models import BiddingAdvice, HandEvaluation


def _render(renderable: object) -> str:
    """Render a Rich object to plain text."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    console.print(renderable)
    return buf.getvalue()


# ── format_bid ──────────────────────────────────────────────────────


class TestFormatBid:
    def test_suit_bid_hearts(self) -> None:
        result = format_bid(SuitBid(1, Suit.HEARTS))
        assert "1" in result
        assert "♥" in result

    def test_suit_bid_spades(self) -> None:
        result = format_bid(SuitBid(2, Suit.SPADES))
        assert "2" in result
        assert "♠" in result

    def test_notrump(self) -> None:
        assert format_bid(SuitBid(3, Suit.NOTRUMP)) == "3NT"

    def test_pass(self) -> None:
        assert format_bid(PASS) == "Pass"

    def test_double(self) -> None:
        assert format_bid(DOUBLE) == "X"

    def test_redouble(self) -> None:
        assert format_bid(REDOUBLE) == "XX"


# ── format_hand ─────────────────────────────────────────────────────


class TestFormatHand:
    def test_contains_all_suits(self) -> None:
        hand = Hand.from_pbn("AKJ52.KQ3.84.A73")
        output = _render(format_hand(hand))
        assert "♠" in output
        assert "♥" in output
        assert "♦" in output
        assert "♣" in output

    def test_contains_ranks(self) -> None:
        hand = Hand.from_pbn("AKJ52.KQ3.84.A73")
        output = _render(format_hand(hand))
        assert "A" in output
        assert "K" in output
        assert "J" in output

    def test_has_title(self) -> None:
        hand = Hand.from_pbn("AKJ52.KQ3.84.A73")
        output = _render(format_hand(hand))
        assert "Your Hand" in output


# ── format_hand_eval ────────────────────────────────────────────────


class TestFormatHandEval:
    def _make_eval(self) -> HandEvaluation:
        return HandEvaluation(
            hcp=15,
            length_points=1,
            total_points=16,
            distribution_points=1,
            controls=6,
            quick_tricks=3.5,
            losers=6,
            shape=(5, 3, 2, 3),
            sorted_shape=(5, 3, 3, 2),
            is_balanced=False,
            is_semi_balanced=True,
            longest_suit=Suit.SPADES,
        )

    def test_shows_hcp(self) -> None:
        output = _render(format_hand_eval(self._make_eval()))
        assert "HCP: 15" in output

    def test_shows_total_pts(self) -> None:
        output = _render(format_hand_eval(self._make_eval()))
        assert "Total Pts: 16" in output

    def test_shows_shape(self) -> None:
        output = _render(format_hand_eval(self._make_eval()))
        assert "5-3-2-3" in output

    def test_shows_semi_balanced(self) -> None:
        output = _render(format_hand_eval(self._make_eval()))
        assert "semi-balanced" in output

    def test_shows_balanced(self) -> None:
        ev = HandEvaluation(
            hcp=15,
            length_points=0,
            total_points=15,
            distribution_points=0,
            controls=6,
            quick_tricks=3.5,
            losers=6,
            shape=(4, 3, 3, 3),
            sorted_shape=(4, 3, 3, 3),
            is_balanced=True,
            is_semi_balanced=True,
            longest_suit=Suit.SPADES,
        )
        output = _render(format_hand_eval(ev))
        assert "balanced" in output
        assert "semi-balanced" not in output


# ── format_auction ──────────────────────────────────────────────────


class TestFormatAuction:
    def test_dealer_north(self) -> None:
        bids: list[tuple[Seat, SuitBid | type]] = [
            (Seat.NORTH, SuitBid(1, Suit.HEARTS)),
            (Seat.EAST, PASS),
        ]
        output = _render(format_auction(bids, Seat.NORTH, Seat.SOUTH))  # type: ignore[arg-type]
        assert "♥" in output
        assert "Pass" in output

    def test_shows_question_mark_for_current(self) -> None:
        output = _render(format_auction([], Seat.NORTH, Seat.NORTH))
        assert "?" in output

    def test_no_question_mark_when_complete(self) -> None:
        bids = [
            (Seat.NORTH, SuitBid(1, Suit.HEARTS)),
            (Seat.EAST, PASS),
            (Seat.SOUTH, PASS),
            (Seat.WEST, PASS),
        ]
        output = _render(format_auction(bids, Seat.NORTH, None))  # type: ignore[arg-type]
        assert "?" not in output

    def test_has_seat_headers(self) -> None:
        output = _render(format_auction([], Seat.NORTH, Seat.NORTH))
        assert "W" in output
        assert "N" in output
        assert "E" in output
        assert "S" in output


# ── format_advice ───────────────────────────────────────────────────


class TestFormatAdvice:
    def _make_advice(self, forcing: bool = False) -> BiddingAdvice:
        return BiddingAdvice(
            recommended=RuleResult(
                bid=SuitBid(1, Suit.SPADES),
                rule_name="response.new_suit_1_level",
                explanation="5+ spades, new suit at 1-level",
                forcing=forcing,
            ),
            alternatives=[],
            hand_evaluation=HandEvaluation(
                hcp=15,
                length_points=1,
                total_points=16,
                distribution_points=1,
                controls=6,
                quick_tricks=3.5,
                losers=6,
                shape=(5, 3, 2, 3),
                sorted_shape=(5, 3, 3, 2),
                is_balanced=False,
                is_semi_balanced=True,
                longest_suit=Suit.SPADES,
            ),
            phase="response",  # type: ignore[arg-type]
            thought_process=ThoughtProcess(
                steps=(),
                selected=RuleResult(
                    bid=SuitBid(1, Suit.SPADES),
                    rule_name="response.new_suit_1_level",
                    explanation="5+ spades, new suit at 1-level",
                ),
            ),
        )

    def test_shows_bid(self) -> None:
        output = _render(format_advice(self._make_advice()))
        assert "♠" in output

    def test_shows_explanation(self) -> None:
        output = _render(format_advice(self._make_advice()))
        assert "5+ spades" in output

    def test_shows_forcing(self) -> None:
        output = _render(format_advice(self._make_advice(forcing=True)))
        assert "forcing" in output


# ── format_alternatives ─────────────────────────────────────────────


class TestFormatAlternatives:
    def test_empty_returns_none(self) -> None:
        assert format_alternatives([]) is None

    def test_shows_alternatives(self) -> None:
        alts = [
            RuleResult(
                bid=SuitBid(2, Suit.HEARTS),
                rule_name="response.single_raise",
                explanation="Single raise, 3+ support",
            ),
        ]
        panel = format_alternatives(alts)
        assert panel is not None
        output = _render(panel)
        assert "♥" in output
        assert "Single raise" in output


# ── format_thought_process ──────────────────────────────────────────


class TestFormatThoughtProcess:
    def _make_tp(self) -> ThoughtProcess:
        return ThoughtProcess(
            steps=(
                ThoughtStep(
                    rule_name="opening.2c",
                    passed=False,
                    bid=None,
                    condition_results=(
                        ConditionResult(
                            passed=False,
                            label="22+ total pts",
                            detail="16 total points (need 22+)",
                        ),
                    ),
                ),
                ThoughtStep(
                    rule_name="opening.1nt",
                    passed=True,
                    bid=SuitBid(1, Suit.NOTRUMP),
                    condition_results=(
                        ConditionResult(
                            passed=True,
                            label="15-17 HCP",
                            detail="16 HCP (15-17)",
                        ),
                        ConditionResult(
                            passed=True,
                            label="balanced",
                            detail="Shape 4-3-3-3 (balanced)",
                        ),
                    ),
                ),
                ThoughtStep(
                    rule_name="opening.1suit",
                    passed=True,
                    bid=SuitBid(1, Suit.SPADES),
                    condition_results=(
                        ConditionResult(
                            passed=True,
                            label="meets opening",
                            detail="Meets opening strength",
                        ),
                    ),
                ),
            ),
            selected=RuleResult(
                bid=SuitBid(1, Suit.NOTRUMP),
                rule_name="opening.1nt",
                explanation="15-17 HCP, balanced",
            ),
        )

    def test_shows_recommended(self) -> None:
        output = _render(format_thought_process(self._make_tp()))
        assert "opening.1nt" in output
        assert "1NT" in output

    def test_shows_passing_conditions(self) -> None:
        output = _render(format_thought_process(self._make_tp()))
        assert "16 HCP (15-17)" in output
        assert "balanced" in output

    def test_shows_failing_condition(self) -> None:
        output = _render(format_thought_process(self._make_tp()))
        # opening.2c fails immediately so it's not "interesting"
        # (no conditions passed before the failure)
        assert "opening.2c" not in output

    def test_shows_passing_alternative(self) -> None:
        output = _render(format_thought_process(self._make_tp()))
        assert "opening.1suit" in output

    def test_interesting_failing_shown(self) -> None:
        """A rule that passes some conditions before failing is shown."""
        tp = ThoughtProcess(
            steps=(
                ThoughtStep(
                    rule_name="response.jump_shift",
                    passed=False,
                    bid=None,
                    condition_results=(
                        ConditionResult(
                            passed=True,
                            label="opened 1 suit",
                            detail="Partner opened 1 of a suit",
                        ),
                        ConditionResult(
                            passed=False,
                            label="17+ HCP",
                            detail="12 HCP (need 17+)",
                        ),
                    ),
                ),
                ThoughtStep(
                    rule_name="response.new_suit",
                    passed=True,
                    bid=SuitBid(1, Suit.SPADES),
                    condition_results=(
                        ConditionResult(
                            passed=True,
                            label="opened 1 suit",
                            detail="Partner opened 1 of a suit",
                        ),
                    ),
                ),
            ),
            selected=RuleResult(
                bid=SuitBid(1, Suit.SPADES),
                rule_name="response.new_suit",
                explanation="New suit at 1-level",
            ),
        )
        output = _render(format_thought_process(tp))
        assert "response.jump_shift" in output
        assert "12 HCP (need 17+)" in output


# ── format_contract ─────────────────────────────────────────────────


class TestFormatContract:
    def test_simple(self) -> None:
        c = Contract(level=3, suit=Suit.NOTRUMP, declarer=Seat.SOUTH)
        result = format_contract(c)
        assert "3NT" in result
        assert "South" in result

    def test_suited(self) -> None:
        c = Contract(level=4, suit=Suit.HEARTS, declarer=Seat.NORTH)
        result = format_contract(c)
        assert "♥" in result
        assert "North" in result

    def test_doubled(self) -> None:
        c = Contract(level=1, suit=Suit.SPADES, declarer=Seat.EAST, doubled=True)
        result = format_contract(c)
        assert "doubled" in result

    def test_passed_out(self) -> None:
        c = Contract(level=0, suit=Suit.CLUBS, declarer=Seat.NORTH, passed_out=True)
        assert format_contract(c) == "Passed out"


# ── format_bid_prompt ───────────────────────────────────────────────


class TestFormatBidPrompt:
    def test_north(self) -> None:
        assert format_bid_prompt(Seat.NORTH) == "North's bid: "

    def test_south(self) -> None:
        assert format_bid_prompt(Seat.SOUTH) == "South's bid: "
