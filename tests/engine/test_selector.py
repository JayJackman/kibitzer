"""Tests for BidSelector and phase detection."""

from bridge.engine.condition import Condition, condition
from bridge.engine.context import BiddingContext
from bridge.engine.registry import RuleRegistry
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.engine.selector import BidSelector, ThoughtProcess, ThoughtStep
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, Bid, SuitBid, is_pass
from bridge.model.board import Board
from bridge.model.card import Suit
from bridge.model.hand import Hand

HAND = Hand.from_pbn("AKJ52.KQ3.84.A73")


@condition("always")
def _always(ctx: BiddingContext) -> bool:
    return True


@condition("never")
def _never(ctx: BiddingContext) -> bool:
    return False


class MockRule(Rule):
    """Configurable mock rule for testing the selector."""

    def __init__(
        self,
        name: str,
        category: Category,
        priority: int,
        bid: Bid | None = None,
        should_apply: bool = True,
    ) -> None:
        self._name = name
        self._category = category
        self._priority = priority
        self._bid = bid or PASS
        self._should_apply = should_apply

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> Category:
        return self._category

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def conditions(self) -> Condition:
        return _always if self._should_apply else _never

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=self._bid,
            rule_name=self._name,
            explanation=f"Mock rule {self._name}",
        )


def _make_ctx(seat: Seat, auction: AuctionState) -> BiddingContext:
    return BiddingContext(Board(hand=HAND, seat=seat, auction=auction))


class TestPhaseDetection:
    def test_opening(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.OPENING

    def test_opening_after_passes(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(PASS)  # N
        auction.add_bid(PASS)  # E

        ctx = _make_ctx(Seat.SOUTH, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.OPENING

    def test_response(self) -> None:
        # Partner (N) opens 1H, opponent (E) passes, my turn (S)
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N opens
        auction.add_bid(PASS)  # E passes

        ctx = _make_ctx(Seat.SOUTH, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.RESPONSE

    def test_competitive_response(self) -> None:
        # Partner (N) opens 1H, opponent (E) overcalls 1S, my turn (S)
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N opens
        auction.add_bid(SuitBid(1, Suit.SPADES))  # E overcalls

        ctx = _make_ctx(Seat.SOUTH, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.COMPETITIVE_RESPONSE

    def test_rebid_opener(self) -> None:
        # I (N) opened 1H, E passes, partner (S) responds 2H, W passes
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N opens
        auction.add_bid(PASS)  # E
        auction.add_bid(SuitBid(2, Suit.HEARTS))  # S responds
        auction.add_bid(PASS)  # W

        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.REBID_OPENER

    def test_rebid_responder(self) -> None:
        # Partner (N) opened 1H, E passes, I (S) responded 1S,
        # W passes, partner (N) rebids 2H, E passes, my turn (S)
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N opens
        auction.add_bid(PASS)  # E
        auction.add_bid(SuitBid(1, Suit.SPADES))  # S responds
        auction.add_bid(PASS)  # W
        auction.add_bid(SuitBid(2, Suit.HEARTS))  # N rebids
        auction.add_bid(PASS)  # E

        ctx = _make_ctx(Seat.SOUTH, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.REBID_RESPONDER

    def test_competitive(self) -> None:
        # Opponent (N) opens 1H, my turn (E)
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N opens

        ctx = _make_ctx(Seat.EAST, auction)
        selector = BidSelector(RuleRegistry())

        assert selector.detect_phase(ctx) == Category.COMPETITIVE


class TestBidSelector:
    def test_highest_priority_wins(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )
        reg.register(
            MockRule(
                "opening.1nt",
                Category.OPENING,
                200,
                bid=SuitBid(1, Suit.NOTRUMP),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        result = selector.select(ctx)

        assert result.rule_name == "opening.1nt"
        assert str(result.bid) == "1NT"

    def test_skips_non_applicable(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.2c",
                Category.OPENING,
                400,
                bid=SuitBid(2, Suit.CLUBS),
                should_apply=False,
            )
        )
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        result = selector.select(ctx)

        assert result.rule_name == "opening.1suit"

    def test_fallback_to_pass(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.2c", Category.OPENING, 400, should_apply=False))

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        result = selector.select(ctx)

        assert result.rule_name == "fallback.pass"
        assert is_pass(result.bid)

    def test_empty_registry_returns_pass(self) -> None:
        reg = RuleRegistry()
        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        result = selector.select(ctx)

        assert is_pass(result.bid)
        assert result.rule_name == "fallback.pass"

    def test_overlay_rules_checked(self) -> None:
        reg = RuleRegistry()
        # Low-priority opening rule
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )
        # High-priority convention overlay
        reg.register(
            MockRule(
                "convention.stayman",
                Category.CONVENTION,
                350,
                bid=SuitBid(2, Suit.CLUBS),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        result = selector.select(ctx)

        # Convention overlay has higher priority, so it wins
        assert result.rule_name == "convention.stayman"

    def test_slam_overlay_checked(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )
        reg.register(
            MockRule(
                "slam.blackwood",
                Category.SLAM,
                500,
                bid=SuitBid(4, Suit.NOTRUMP),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        result = selector.select(ctx)

        assert result.rule_name == "slam.blackwood"


class TestCandidates:
    def test_returns_all_matching(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )
        reg.register(
            MockRule(
                "opening.1nt",
                Category.OPENING,
                200,
                bid=SuitBid(1, Suit.NOTRUMP),
            )
        )
        reg.register(
            MockRule(
                "opening.2c",
                Category.OPENING,
                400,
                should_apply=False,
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        results = selector.candidates(ctx)

        assert len(results) == 2
        names = [r.rule_name for r in results]
        assert "opening.1nt" in names
        assert "opening.1suit" in names
        assert "opening.2c" not in names

    def test_empty_when_none_apply(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.2c", Category.OPENING, 400, should_apply=False))

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)

        assert selector.candidates(ctx) == []


class TestThink:
    def test_returns_thought_process(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        assert isinstance(tp, ThoughtProcess)
        assert tp.selected.rule_name == "opening.1suit"
        assert str(tp.selected.bid) == "1S"

    def test_steps_include_all_rules(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.2c",
                Category.OPENING,
                400,
                bid=SuitBid(2, Suit.CLUBS),
                should_apply=False,
            )
        )
        reg.register(
            MockRule(
                "opening.1nt",
                Category.OPENING,
                200,
                bid=SuitBid(1, Suit.NOTRUMP),
            )
        )
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        assert len(tp.steps) == 3
        # Steps are in priority order (highest first)
        assert tp.steps[0].rule_name == "opening.2c"
        assert tp.steps[1].rule_name == "opening.1nt"
        assert tp.steps[2].rule_name == "opening.1suit"

    def test_passing_steps_have_bid(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1nt",
                Category.OPENING,
                200,
                bid=SuitBid(1, Suit.NOTRUMP),
            )
        )
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        for step in tp.steps:
            assert step.passed is True
            assert step.bid is not None

    def test_failing_steps_have_no_bid(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.2c",
                Category.OPENING,
                400,
                bid=SuitBid(2, Suit.CLUBS),
                should_apply=False,
            )
        )
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        failing = [s for s in tp.steps if not s.passed]
        assert len(failing) == 1
        assert failing[0].rule_name == "opening.2c"
        assert failing[0].bid is None

    def test_highest_priority_passing_rule_wins(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1nt",
                Category.OPENING,
                200,
                bid=SuitBid(1, Suit.NOTRUMP),
            )
        )
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        # 1NT has higher priority, so it's the selected rule
        assert tp.selected.rule_name == "opening.1nt"
        assert str(tp.selected.bid) == "1NT"

    def test_fallback_pass_when_none_apply(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.2c", Category.OPENING, 400, should_apply=False))

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        assert tp.selected.rule_name == "fallback.pass"
        assert is_pass(tp.selected.bid)
        assert len(tp.steps) == 1
        assert tp.steps[0].passed is False

    def test_empty_registry_fallback_pass(self) -> None:
        reg = RuleRegistry()
        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        assert tp.selected.rule_name == "fallback.pass"
        assert is_pass(tp.selected.bid)
        assert len(tp.steps) == 0

    def test_steps_have_condition_results(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        step = tp.steps[0]
        assert isinstance(step, ThoughtStep)
        assert len(step.condition_results) > 0
        # The _always condition should produce a passing result
        assert step.condition_results[0].passed is True

    def test_selected_has_explanation(self) -> None:
        reg = RuleRegistry()
        reg.register(
            MockRule(
                "opening.1suit",
                Category.OPENING,
                100,
                bid=SuitBid(1, Suit.SPADES),
            )
        )

        auction = AuctionState(dealer=Seat.NORTH)
        ctx = _make_ctx(Seat.NORTH, auction)
        selector = BidSelector(reg)
        tp = selector.think(ctx)

        assert tp.selected.explanation == "Mock rule opening.1suit"
