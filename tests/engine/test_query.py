"""Tests for Q2 query function: 'What would bid X mean here?'"""

from bridge.engine.query import BidAnalysis, analyze_bid
from bridge.engine.sayc import create_sayc_registry
from bridge.model.auction import AuctionState, Seat, parse_auction
from bridge.model.bid import PASS, SuitBid, parse_bid
from bridge.model.card import Suit


def _registry():
    return create_sayc_registry()


class TestAnalyzeBidOpening:
    """Opening position -- empty auction."""

    def test_1s_matches_open_1_major(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        result = analyze_bid(auction, parse_bid("1S"), _registry())

        assert len(result.matches) >= 1
        names = [m.rule_name for m in result.matches]
        assert "opening.1_major" in names

    def test_1s_promises_hcp_and_spade_length(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        result = analyze_bid(auction, parse_bid("1S"), _registry())

        assert result.combined.hcp[0] is not None
        assert result.combined.hcp[0] >= 12
        assert Suit.SPADES in result.combined.lengths
        spade_min = result.combined.lengths[Suit.SPADES][0]
        assert spade_min is not None and spade_min >= 5

    def test_1nt_promises_balanced_and_hcp_range(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        result = analyze_bid(auction, parse_bid("1N"), _registry())

        assert result.combined.hcp == (15, 17)
        assert result.combined.balanced is True

    def test_pass_matches(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        result = analyze_bid(auction, PASS, _registry())

        assert len(result.matches) >= 1
        names = [m.rule_name for m in result.matches]
        assert "opening.pass" in names


class TestAnalyzeBidResponse:
    """Response position -- after partner opens."""

    def test_2c_after_1s(self) -> None:
        """2C response to 1S opening (2-over-1)."""
        auction = parse_auction("1S P")
        result = analyze_bid(auction, parse_bid("2C"), _registry())

        assert len(result.matches) >= 1
        names = [m.rule_name for m in result.matches]
        assert "response.2_over_1" in names

        # Should promise HCP range and club length
        assert result.combined.hcp[0] is not None
        assert result.combined.hcp[0] >= 10
        assert Suit.CLUBS in result.combined.lengths
        club_min = result.combined.lengths[Suit.CLUBS][0]
        assert club_min is not None and club_min >= 4


class TestAnalyzeBidRebid:
    """Rebid position -- after opener's partner responded."""

    def test_2s_rebid_after_2_over_1(self) -> None:
        """Opener rebids 2S after 1S-2C: multiple rules may match."""
        auction = parse_auction("1S P 2C P")
        result = analyze_bid(auction, parse_bid("2S"), _registry())

        # At least one rule should match for rebidding own suit
        assert len(result.matches) >= 1

    def test_multiple_matches_union(self) -> None:
        """When multiple rules match, combined is wider than any single match."""
        auction = parse_auction("1S P 2C P")
        result = analyze_bid(auction, parse_bid("2S"), _registry())

        if len(result.matches) > 1:
            # Combined should be the union (wider bounds)
            for match in result.matches:
                # Each match's HCP min should be >= combined's min
                # (union widens, so combined min <= each match min)
                match_min = match.promise.hcp[0]
                combined_min = result.combined.hcp[0]
                if match_min is not None and combined_min is not None:
                    assert combined_min <= match_min


class TestAnalyzeBidNoMatch:
    """Edge cases -- bids with no matching rules."""

    def test_impossible_bid_returns_empty(self) -> None:
        """A 7NT opening has no rule, should return empty matches."""
        auction = AuctionState(dealer=Seat.NORTH)
        result = analyze_bid(auction, parse_bid("7N"), _registry())

        assert len(result.matches) == 0
        # Combined should be fully unconstrained
        assert result.combined.hcp == (None, None)

    def test_result_type(self) -> None:
        """Verify the return type structure."""
        auction = AuctionState(dealer=Seat.NORTH)
        result = analyze_bid(auction, parse_bid("1H"), _registry())

        assert isinstance(result, BidAnalysis)
        assert result.bid == SuitBid(1, Suit.HEARTS)
        for match in result.matches:
            assert match.rule_name
            assert match.explanation


class TestAnalyzeBidEndToEnd:
    """End-to-end example from the planning doc: 1S -> 2C -> 2S -> ?"""

    def test_full_auction_position(self) -> None:
        """At South's second bid after 1S-P-2C-P-2S-P, analyze 4S."""
        auction = parse_auction("1S P 2C P 2S P")
        result = analyze_bid(auction, parse_bid("4S"), _registry())

        # Should find at least one rule for jumping to game in opener's suit
        assert len(result.matches) >= 1

    def test_3nt_at_reresponse(self) -> None:
        """At South's second bid after 1S-P-2C-P-2S-P, analyze 3NT."""
        auction = parse_auction("1S P 2C P 2S P")
        result = analyze_bid(auction, parse_bid("3N"), _registry())

        # Should find at least one rule for 3NT
        assert len(result.matches) >= 1
