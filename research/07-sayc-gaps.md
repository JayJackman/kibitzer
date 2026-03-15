# SAYC System Gaps

Known gaps and awkward auctions in Standard American Yellow Card where the system
does not produce optimal results. These are not engine bugs -- they reflect genuine
limitations in the SAYC framework.

## Gap 1: 2-Over-1 Minor Raise With No Stopper

**Auction:** 1M - 2m - 3m - ?

**Problem:** After opener raises responder's minor, responder may have enough
combined strength for game but lack a stopper in an unbid suit. SAYC's one-round
force from the 2-over-1 has been satisfied by opener's 3m raise, so the auction
is no longer forcing. Responder must choose between:

- 3NT without a full stopper in every unbid suit (risky)
- Pass at the 3-level with 10+ HCP opposite an opener (underbid)

Neither option is good.

**Example:**

```
South (dealer): AK632.9.Q743.AKQ  (18 HCP, 5-1-4-3)
North:          Q9.A65.AT962.T98  (10 HCP, 2-3-5-3)

1S - 2D - 3D - ?
```

North has 10 HCP and hearts stopped (ace), but clubs are T98 -- not a stopper
by standard criteria (A, Kx, Qxx). The `ThreeNTAfterRaise2Over1` rule requires
stoppers in all unbid suits, so it fails. No other game-level rule applies
(not enough for 5m, not a major fit), so the engine passes.

In practice, 3NT makes easily: South has AKQ of clubs, and the combined 28 HCP
plus a 9-card diamond fit produce 11 tricks. But responder cannot know this.

**Root cause:** SAYC's 2-over-1 is forcing for one round only. Once opener raises
to 3m, the force is consumed. Responder with a minimum 2-over-1 (10-12 HCP) and
no stopper has no good bid.

### How 2/1 Game Forcing solves this

The 2/1 Game Forcing system addresses this exact problem by making any 2-over-1
response unconditionally game-forcing. In that system:

- After 1S - 2D - 3D, the auction is still forcing to game
- Responder can bid 3H (natural or stopper-showing) without fear of being passed
- The partnership can exchange stopper information below 3NT
- There is no pressure to leap to 3NT or risk being dropped in a partscore

This is one of the primary motivations for 2/1 GF over standard SAYC: it
eliminates the ambiguity of "is this forcing?" after a 2-level response,
particularly in minor-suit auctions where game requires either 3NT (needing
stoppers) or 5m (needing 11 tricks).

### Future work

A 2/1 Game Forcing rule registry could be added alongside the existing SAYC
registry. The main structural changes would be:

- 2-over-1 responses become game-forcing (not just one-round forcing)
- 1NT forcing response replaces many former 2-over-1 auctions with lighter hands
- Rebid and reresponse rules can assume game is reached, simplifying logic
- Stopper-showing bids and slam exploration become more natural below game
