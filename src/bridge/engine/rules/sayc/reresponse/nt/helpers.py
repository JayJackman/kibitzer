"""Shared helpers for responder rebid rules after a 1NT or 2NT opening."""

from __future__ import annotations

from bridge.engine.condition import condition
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.model.bid import SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Rank, Suit

# ── Core accessors ─────────────────────────────────────────────────


def opening_bid(ctx: AuctionContext) -> SuitBid:
    """Return partner's opening bid (1NT or 2NT in this module).

    Only safe to call when guarded by partner_opened_1nt or partner_opened_2nt.
    """
    assert ctx.opening_bid is not None
    _, bid = ctx.opening_bid
    assert is_suit_bid(bid)
    return bid


def my_response(ctx: AuctionContext) -> SuitBid:
    """Return my first bid (response in round 2)."""
    bid = ctx.my_bids[0]
    assert is_suit_bid(bid)
    return bid


def partner_rebid(ctx: AuctionContext) -> SuitBid:
    """Return partner's rebid (round 3).

    Only safe to call when guarded by a partner-rebid condition.
    """
    rebid = ctx.partner_last_bid
    assert rebid is not None and is_suit_bid(rebid)
    return rebid


def partner_rebid_safe(ctx: AuctionContext) -> SuitBid | None:
    """Return partner's rebid, or None if partner didn't make a suit bid."""
    rebid = ctx.partner_last_bid
    if rebid is None or not is_suit_bid(rebid):
        return None
    return rebid


def shown_major(ctx: AuctionContext) -> Suit:
    """Return the major partner showed in response to Stayman.

    Only safe to call when partner_showed_a_major guard is active.
    """
    rebid = partner_rebid(ctx)
    assert rebid.suit.is_major
    return rebid.suit


# ── Guard conditions: opening ────────────────────────────────────


@condition("partner opened 1NT")
def partner_opened_1nt(ctx: BiddingContext) -> bool:
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 1 and bid.is_notrump


@condition("partner opened 2NT")
def partner_opened_2nt(ctx: BiddingContext) -> bool:
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 2 and bid.is_notrump


# ── Guard conditions: my response ────────────────────────────────


@condition("I bid Stayman (2C) over 1NT")
def i_bid_stayman_1nt(ctx: BiddingContext) -> bool:
    """I responded 2C (Stayman) to partner's 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 2 and bid.suit == Suit.CLUBS


@condition("I bid Stayman (3C) over 2NT")
def i_bid_stayman_2nt(ctx: BiddingContext) -> bool:
    """I responded 3C (Stayman) to partner's 2NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 3 and bid.suit == Suit.CLUBS


# ── Guard conditions: partner's Stayman rebid ────────────────────


@condition("partner denied a 4-card major")
def partner_denied_major(ctx: BiddingContext) -> bool:
    """Partner rebid 2D (over 1NT) or 3D (over 2NT) -- no 4-card major."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.suit == Suit.DIAMONDS and not rebid.is_notrump


@condition("partner showed hearts")
def partner_showed_hearts(ctx: BiddingContext) -> bool:
    """Partner rebid 2H (over 1NT) or 3H (over 2NT) -- 4+ hearts."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.suit == Suit.HEARTS


@condition("partner showed spades")
def partner_showed_spades(ctx: BiddingContext) -> bool:
    """Partner rebid 2S (over 1NT) or 3S (over 2NT) -- 4+ spades."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.suit == Suit.SPADES


@condition("partner showed a major")
def partner_showed_a_major(ctx: BiddingContext) -> bool:
    """Partner rebid a major in response to Stayman."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.suit.is_major


# ── Transfer accessors ──────────────────────────────────────────


def _transfer_target(bid_suit: Suit) -> Suit:
    """Map a transfer bid suit to its target major."""
    if bid_suit == Suit.DIAMONDS:
        return Suit.HEARTS
    assert bid_suit == Suit.HEARTS
    return Suit.SPADES


def transfer_suit(ctx: AuctionContext) -> Suit:
    """Return the major suit that was transferred to.

    Only safe to call when guarded by i_bid_transfer_1nt or i_bid_transfer_2nt.
    """
    return _transfer_target(my_response(ctx).suit)


# ── Guard conditions: my transfer response ──────────────────────


@condition("I bid a Jacoby transfer over 1NT")
def i_bid_transfer_1nt(ctx: BiddingContext) -> bool:
    """I responded 2D (->hearts) or 2H (->spades) to partner's 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return (
        is_suit_bid(bid) and bid.level == 2 and bid.suit in (Suit.DIAMONDS, Suit.HEARTS)
    )


@condition("I bid a transfer over 2NT")
def i_bid_transfer_2nt(ctx: BiddingContext) -> bool:
    """I responded 3D (->hearts) or 3H (->spades) to partner's 2NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return (
        is_suit_bid(bid) and bid.level == 3 and bid.suit in (Suit.DIAMONDS, Suit.HEARTS)
    )


# ── Guard conditions: partner's transfer rebid ──────────────────


@condition("partner completed the transfer")
def partner_completed_transfer(ctx: BiddingContext) -> bool:
    """Partner bid the transfer suit at the expected level."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    resp = my_response(ctx)
    target = _transfer_target(resp.suit)
    return rebid.suit == target and rebid.level == resp.level


@condition("partner super-accepted the transfer")
def partner_super_accepted(ctx: BiddingContext) -> bool:
    """Partner jumped in the transfer suit (17 HCP, 4+ support)."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    resp = my_response(ctx)
    target = _transfer_target(resp.suit)
    return rebid.suit == target and rebid.level == resp.level + 1


@condition("transfer suit is hearts")
def transfer_is_hearts(ctx: BiddingContext) -> bool:
    """I transferred to hearts (my response was diamonds)."""
    return my_response(ctx).suit == Suit.DIAMONDS


@condition("transfer suit is spades")
def transfer_is_spades(ctx: BiddingContext) -> bool:
    """I transferred to spades (my response was hearts)."""
    return my_response(ctx).suit == Suit.HEARTS


# ── Guard conditions: my puppet response ──────────────────────


@condition("I bid the 2S puppet over 1NT")
def i_bid_puppet_1nt(ctx: BiddingContext) -> bool:
    """I responded 2S (puppet to 3C) to partner's 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 2 and bid.suit == Suit.SPADES


@condition("I bid the 3S puppet over 2NT")
def i_bid_puppet_2nt(ctx: BiddingContext) -> bool:
    """I responded 3S (puppet to 4C) to partner's 2NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 3 and bid.suit == Suit.SPADES


# ── Guard conditions: partner's puppet rebid ──────────────────


@condition("partner completed the puppet")
def partner_completed_puppet(ctx: BiddingContext) -> bool:
    """Partner bid clubs at the expected level (3C after 2S, 4C after 3S)."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    resp = my_response(ctx)
    return rebid.suit == Suit.CLUBS and rebid.level == resp.level + 1


# ── Guard conditions: my Texas response ───────────────────────


@condition("I bid Texas over 1NT")
def i_bid_texas_1nt(ctx: BiddingContext) -> bool:
    """I responded 4D or 4H (Texas transfer) to partner's 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return (
        is_suit_bid(bid) and bid.level == 4 and bid.suit in (Suit.DIAMONDS, Suit.HEARTS)
    )


@condition("I bid Texas over 2NT")
def i_bid_texas_2nt(ctx: BiddingContext) -> bool:
    """I responded 4D or 4H (Texas transfer) to partner's 2NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return (
        is_suit_bid(bid) and bid.level == 4 and bid.suit in (Suit.DIAMONDS, Suit.HEARTS)
    )


# ── Guard conditions: partner's Texas rebid ──────────────────


@condition("partner completed Texas transfer")
def partner_completed_texas(ctx: BiddingContext) -> bool:
    """Partner bid the target major at level 4 (4H after 4D, 4S after 4H)."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    resp = my_response(ctx)
    if resp.suit == Suit.DIAMONDS:
        return rebid.suit == Suit.HEARTS and rebid.level == 4
    if resp.suit == Suit.HEARTS:
        return rebid.suit == Suit.SPADES and rebid.level == 4
    return False


# ── Guard conditions: my Gerber response ──────────────────────


@condition("I bid Gerber (4C) over 1NT")
def i_bid_gerber_1nt(ctx: BiddingContext) -> bool:
    """I responded 4C (Gerber) to partner's 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 4 and bid.suit == Suit.CLUBS


@condition("I bid Gerber (4C) over 2NT")
def i_bid_gerber_2nt(ctx: BiddingContext) -> bool:
    """I responded 4C (Gerber) to partner's 2NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 4 and bid.suit == Suit.CLUBS


# ── Guard conditions: partner's Gerber rebid ──────────────────


@condition("partner responded to Gerber")
def partner_responded_to_gerber(ctx: BiddingContext) -> bool:
    """Partner bid at the 4-level in response to Gerber (4D/4H/4S/4NT)."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.level == 4


@condition("partner responded below 4NT")
def partner_responded_below_4nt(ctx: BiddingContext) -> bool:
    """Partner bid 4D/4H/4S (0-1/1/2 aces) -- sign-off at 4NT possible."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.level == 4 and not rebid.is_notrump


@condition("partner responded 4NT")
def partner_responded_4nt(ctx: BiddingContext) -> bool:
    """Partner bid 4NT (3 aces) -- sign-off = pass."""
    rebid = partner_rebid_safe(ctx)
    if rebid is None:
        return False
    return rebid.level == 4 and rebid.is_notrump


# ── Gerber combined-ace helpers ──────────────────────────────


def _combined_aces(ctx: BiddingContext) -> int:
    """Compute combined aces from hand + partner's Gerber response.

    With 33+ combined HCP, opponents have at most 7 HCP = at most 1 ace.
    Partnership always has >= 3 aces.  The 0/4 ambiguity (4D response) is
    fully resolved: partner_aces = 4 - my_aces.
    """
    my_aces = sum(ctx.hand.has_card(s, Rank.ACE) for s in SUITS_SHDC)
    rebid = partner_rebid(ctx)
    if rebid.suit == Suit.HEARTS:
        return my_aces + 1
    if rebid.suit == Suit.SPADES:
        return my_aces + 2
    if rebid.is_notrump:
        return my_aces + 3
    # Diamonds = 0 or 4.  With 33+ combined HCP the partnership holds
    # at least 3 aces, so partner_aces = 4 - my_aces.
    return 4


@condition("enough aces for slam")
def enough_aces_for_slam(ctx: BiddingContext) -> bool:
    return _combined_aces(ctx) >= 3


@condition("not enough aces for slam")
def not_enough_aces_for_slam(ctx: BiddingContext) -> bool:
    return _combined_aces(ctx) <= 2
