"""Shared helpers for responder rebid rules after a 1-of-a-suit opening."""

from __future__ import annotations

from bridge import evaluate
from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import condition
from bridge.engine.context import BiddingContext
from bridge.model.bid import SuitBid, is_suit_bid
from bridge.model.card import Suit

# ── Core accessors ─────────────────────────────────────────────────


def opening_bid(ctx: BiddingContext) -> SuitBid:
    """Return partner's opening bid (always a suit bid in this module)."""
    assert ctx.opening_bid is not None
    _, bid = ctx.opening_bid
    assert is_suit_bid(bid)
    return bid


def opening_suit(ctx: BiddingContext) -> Suit:
    """Return partner's opening suit (never NOTRUMP for 1-suit openings)."""
    bid = opening_bid(ctx)
    assert not bid.is_notrump
    return bid.suit


def my_response(ctx: BiddingContext) -> SuitBid:
    """Return my first bid (response in round 2)."""
    bid = ctx.my_bids[0]
    assert is_suit_bid(bid)
    return bid


def my_response_suit(ctx: BiddingContext) -> Suit:
    """Return the suit I bid in round 2."""
    return my_response(ctx).suit


def partner_rebid(ctx: BiddingContext) -> SuitBid:
    """Return partner's rebid (round 3)."""
    rebid = ctx.partner_last_bid
    assert rebid is not None and is_suit_bid(rebid)
    return rebid


def partner_rebid_suit(ctx: BiddingContext) -> Suit:
    """Return the suit partner bid in round 3."""
    return partner_rebid(ctx).suit


# ── Guard conditions ──────────────────────────────────────────────


@condition("partner opened 1 of a suit")
def partner_opened_1_suit(ctx: BiddingContext) -> bool:
    """Guard: partner's opening was 1C/1D/1H/1S."""
    bid = opening_bid(ctx)
    return bid.level == 1 and not bid.is_notrump


@condition("opening suit is major")
def opening_is_major(ctx: BiddingContext) -> bool:
    return opening_suit(ctx).is_major


# ── My response classifiers (what I bid in round 2) ───────────────


@condition("I raised opener's suit")
def i_raised(ctx: BiddingContext) -> bool:
    """I single-raised opener's suit (e.g. 1H->2H)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    return resp.suit == opening.suit and resp.level == opening.level + 1


# ── Partner's rebid classifiers (what opener bid in round 3) ──────


@condition("partner rebid own suit")
def partner_rebid_own_suit(ctx: BiddingContext) -> bool:
    """Partner rebid same suit at cheapest level."""
    opening = opening_bid(ctx)
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    cheapest = cheapest_bid_in_suit(opening.suit, my_resp)
    return rebid.suit == opening.suit and rebid.level == cheapest.level


@condition("partner jump-rebid own suit")
def partner_jump_rebid_own_suit(ctx: BiddingContext) -> bool:
    """Partner jump-rebid same suit (one level higher than cheapest)."""
    opening = opening_bid(ctx)
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    cheapest = cheapest_bid_in_suit(opening.suit, my_resp)
    return rebid.suit == opening.suit and rebid.level == cheapest.level + 1


@condition("partner bid a new suit (non-reverse)")
def partner_rebid_new_suit(ctx: BiddingContext) -> bool:
    """Partner bid a new suit that is NOT a reverse.

    Covers both lower-ranking suits at 2-level (1H->1S->2C)
    and higher-ranking suits at 1-level (1C->1H->1S).
    """
    rebid = partner_rebid(ctx)
    if rebid.suit in (opening_suit(ctx), my_response_suit(ctx)) or rebid.is_notrump:
        return False
    # Non-reverse: either lower-ranking suit, or 1-level (can't be a reverse)
    return rebid.suit < opening_suit(ctx) or rebid.level == 1


@condition("partner reversed")
def partner_reversed(ctx: BiddingContext) -> bool:
    """Partner made a reverse bid (new higher-ranking suit at cheapest level, 17+)."""
    rebid = partner_rebid(ctx)
    if rebid.suit in (opening_suit(ctx), my_response_suit(ctx)) or rebid.is_notrump:
        return False
    # Reverse: higher-ranking suit at 2-level+, at cheapest level (not a jump).
    # A 1-level bid (e.g. 1C->1D->1H) is NOT a reverse.
    cheapest = cheapest_bid_in_suit(rebid.suit, my_response(ctx))
    return (
        rebid.suit > opening_suit(ctx)
        and rebid.level >= 2
        and rebid.level == cheapest.level
    )


@condition("partner jumped to game in own suit")
def partner_game_in_own_suit(ctx: BiddingContext) -> bool:
    """Partner bid game or higher in their opening suit (e.g. 1H->...->4H)."""
    rebid = partner_rebid(ctx)
    return rebid.suit == opening_suit(ctx) and rebid.level >= 4


@condition("partner jump-shifted")
def partner_jump_shifted(ctx: BiddingContext) -> bool:
    """Partner made a jump shift (new suit, one level higher than cheapest)."""
    rebid = partner_rebid(ctx)
    if rebid.suit in (opening_suit(ctx), my_response_suit(ctx)) or rebid.is_notrump:
        return False
    cheapest = cheapest_bid_in_suit(rebid.suit, my_response(ctx))
    return rebid.level > cheapest.level


@condition("partner raised my suit")
def partner_raised_my_suit(ctx: BiddingContext) -> bool:
    """Partner raised my response suit at cheapest level."""
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    if my_resp.is_notrump:
        return False
    cheapest = cheapest_bid_in_suit(my_resp.suit, my_resp)
    return rebid.suit == my_resp.suit and rebid.level == cheapest.level


@condition("partner rebid 2NT")
def partner_rebid_2nt(ctx: BiddingContext) -> bool:
    rebid = partner_rebid(ctx)
    return rebid.is_notrump and rebid.level == 2


@condition("partner rebid 3NT")
def partner_rebid_3nt(ctx: BiddingContext) -> bool:
    rebid = partner_rebid(ctx)
    return rebid.is_notrump and rebid.level == 3


# ── Response suit helpers ─────────────────────────────────────────


@condition("I responded in a major")
def i_responded_in_a_major(ctx: BiddingContext) -> bool:
    return my_response_suit(ctx).is_major


@condition("I responded in a minor")
def i_responded_in_a_minor(ctx: BiddingContext) -> bool:
    return my_response_suit(ctx).is_minor


@condition("6+ cards in my response suit")
def my_response_suit_6plus(ctx: BiddingContext) -> bool:
    return ctx.hand.suit_length(my_response_suit(ctx)) >= 6


@condition("exactly 5 cards in my response suit")
def my_response_suit_5(ctx: BiddingContext) -> bool:
    return ctx.hand.suit_length(my_response_suit(ctx)) == 5


@condition("5+ cards in my response suit")
def my_response_suit_5plus(ctx: BiddingContext) -> bool:
    return ctx.hand.suit_length(my_response_suit(ctx)) >= 5


# ── Utility functions ──────────────────────────────────────────────


@condition("stoppers in unbid suits")
def stoppers_in_unbid(ctx: BiddingContext) -> bool:
    """Check for stoppers (A, Kx+, Qxx+) in all suits not bid by our side."""
    suits = {
        opening_suit(ctx),
        my_response_suit(ctx),
        partner_rebid_suit(ctx),
    }
    unbid = {Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES} - suits
    return all(evaluate.has_stopper(ctx.hand, suit) for suit in unbid)


def fourth_suit(ctx: BiddingContext) -> Suit | None:
    """The only unbid suit, or None if fewer than 3 suits have been bid."""
    suits: set[Suit] = {
        opening_suit(ctx),
        my_response_suit(ctx),
        partner_rebid_suit(ctx),
    }
    unbid = {Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES} - suits
    return next(iter(unbid)) if len(unbid) == 1 else None


def find_new_suit_forcing(ctx: BiddingContext, *, min_len: int = 4) -> Suit | None:
    """Find a new suit for a forcing bid."""
    exclude = {opening_suit(ctx), my_response_suit(ctx), partner_rebid_suit(ctx)}
    return max(
        (
            suit
            for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES)
            if suit not in exclude and ctx.hand.suit_length(suit) >= min_len
        ),
        # Pick the longest and cheapest new suit.
        key=lambda s: (ctx.hand.suit_length(s), -s),
        default=None,
    )


def find_fourth_suit_bid(ctx: BiddingContext) -> SuitBid | None:
    """Find the fourth suit forcing bid (must be at 2-level or higher)."""
    suit = fourth_suit(ctx)
    if suit is None:
        return None
    rebid = partner_rebid(ctx)
    bid = cheapest_bid_in_suit(suit, rebid)
    # FSF is only at 2+ level; at the 1-level a new suit is natural, not artificial.
    if bid.level == 1:
        return None
    return bid
