"""Tests for CLI app commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from bridge.cli.app import app
from bridge.model.auction import Seat
from bridge.model.hand import Hand

runner = CliRunner()


# ── advise command ─────────────────────────────────────────────────


class TestAdvise:
    def test_opening_hand(self) -> None:
        """17 HCP balanced -> recommends 1NT."""
        result = runner.invoke(app, ["advise", "--hand", "AK32.KQ3.J84.A73"])
        assert result.exit_code == 0
        assert "1NT" in result.output

    def test_with_auction(self) -> None:
        """Response to 1H with 5 spades -> recommends 1S."""
        result = runner.invoke(
            app, ["advise", "--hand", "AKJ52.Q73.84.A73", "--auction", "1H P"]
        )
        assert result.exit_code == 0
        assert "♠" in result.output

    def test_with_dealer(self) -> None:
        result = runner.invoke(
            app, ["advise", "--hand", "AK32.KQ3.J84.A73", "--dealer", "E"]
        )
        assert result.exit_code == 0

    def test_with_vulnerability(self) -> None:
        result = runner.invoke(
            app,
            ["advise", "--hand", "AK32.KQ3.J84.A73", "--vulnerability", "NS"],
        )
        assert result.exit_code == 0

    def test_shows_hand(self) -> None:
        result = runner.invoke(app, ["advise", "--hand", "AK32.KQ3.J84.A73"])
        assert "Your Hand" in result.output

    def test_shows_thought_process(self) -> None:
        result = runner.invoke(app, ["advise", "--hand", "AK32.KQ3.J84.A73"])
        assert "Thought Process" in result.output

    def test_bad_hand(self) -> None:
        result = runner.invoke(app, ["advise", "--hand", "invalid"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_bad_auction(self) -> None:
        result = runner.invoke(
            app, ["advise", "--hand", "AK32.KQ3.J84.A73", "--auction", "ZZ"]
        )
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_illegal_bid_sequence(self) -> None:
        result = runner.invoke(
            app,
            ["advise", "--hand", "AK32.KQ3.J84.A73", "--auction", "1H 1C"],
        )
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_bad_dealer(self) -> None:
        result = runner.invoke(
            app, ["advise", "--hand", "AK32.KQ3.J84.A73", "--dealer", "Z"]
        )
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_bad_vulnerability(self) -> None:
        result = runner.invoke(
            app,
            [
                "advise",
                "--hand",
                "AK32.KQ3.J84.A73",
                "--vulnerability",
                "X",
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.output


# ── practice command ───────────────────────────────────────────────

# Fixed deal for deterministic tests
_FIXED_HANDS = {
    Seat.NORTH: Hand.from_pbn("AK32.KQ3.J84.A73"),
    Seat.EAST: Hand.from_pbn("QJ5.J876.Q73.K85"),
    Seat.SOUTH: Hand.from_pbn("T976.A54.K65.QJ4"),
    Seat.WEST: Hand.from_pbn("84.T92.AT92.T962"),
}


def _patch_deal():
    return patch("bridge.cli.app.deal", return_value=_FIXED_HANDS)


class TestPractice:
    def test_quit_immediately(self) -> None:
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="q\n")
        assert result.exit_code == 0

    def test_shows_hand(self) -> None:
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="q\n")
        assert "Your Hand" in result.output

    def test_help_command(self) -> None:
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="?\nq\n")
        assert "Valid bids" in result.output

    def test_hand_command(self) -> None:
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="h\nq\n")
        assert "Valid bids" in result.output

    def test_invalid_bid_reprompts(self) -> None:
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="ZZ\nq\n")
        assert "Invalid bid" in result.output

    def test_bad_seat(self) -> None:
        result = runner.invoke(app, ["practice", "--seat", "Z"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_one_bid_then_quit(self) -> None:
        """Player bids 1NT (matching engine), then quits."""
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="1NT\nq\n")
        assert "engine" in result.output.lower()

    def test_advise_command(self) -> None:
        with _patch_deal():
            result = runner.invoke(app, ["practice"], input="a\nq\n")
        assert "Recommended Bid" in result.output

    def test_play_again_no(self) -> None:
        """Complete a 1-bid auction and decline to play again."""
        # North opens 1S, computers all pass -> contract is 1S by North
        one_bid_hands = {
            Seat.NORTH: Hand.from_pbn("AKJ52.KQ3.84.A73"),
            Seat.EAST: Hand.from_pbn("84.T92.AT92.T962"),
            Seat.SOUTH: Hand.from_pbn("T976.J54.K65.854"),
            Seat.WEST: Hand.from_pbn("Q3.A876.Q73.KQJ6"),
        }
        with patch("bridge.cli.app.deal", return_value=one_bid_hands):
            result = runner.invoke(
                app,
                ["practice", "--seat", "N", "--dealer", "N"],
                input="1S\nn\n",
            )
        assert result.exit_code == 0
        assert "Final contract" in result.output
