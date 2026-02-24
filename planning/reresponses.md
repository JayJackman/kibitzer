# Responder's Rebids (Round 4) -- Reresponse Rules

## Context

After opener's rebid (round 3), responder must make their second bid (round 4). This is where many common auctions are placed -- responder now has information from both their hand AND opener's rebid to decide: sign off, invite, or bid game/slam.

All rules use `Category.REBID_RESPONDER` (already defined in the Category enum).

---

## File Structure

```
src/bridge/engine/rules/sayc/reresponse/
    __init__.py
    suit.py       # After 1-of-a-suit openings
    nt.py         # After 1NT and 2NT openings
    strong.py     # After 2C opening
    preempt.py    # After preemptive openings (weak two, 3-level, 4-level)
```

---

## Major/Minor Split Recommendation

**Keep one `suit.py` file.** Rationale:

1. The primary differentiator in reresponses is the **responder's first action** and **opener's rebid type**, not whether opener opened a major or minor. After 1H->1S->1NT->?, the reresponse logic is identical to 1D->1S->1NT->?.

2. The paths that differ by major/minor (game target 4M vs 3NT, Jacoby 2NT major-only) are easily handled with guard conditions (`_opening_is_major`) within the same rules.

3. Precedent: `rebid/suit.py` handles both major and minor openings in one file with 51 rules and clear section headers.

4. If the file becomes unwieldy, splitting by **responder's first action** (after raise, after new suit, after NT response) would be more natural than by major/minor, since responder's action type drives the most branching.

---

## Common Helpers

Each file will need helper conditions. These follow the patterns established in `rebid/suit.py`.

### Guards

```python
@condition("partner opened 1 of a suit")
def _partner_opened_1_suit(ctx) -> bool:
    """Guard: partner's opening was 1C/1D/1H/1S."""

@condition("opening suit is major")
def _opening_is_major(ctx) -> bool:

@condition("opening suit is minor")
def _opening_is_minor(ctx) -> bool:
```

### My Response Classifiers (what I bid in round 2)

```python
_i_raised              # I single-raised opener's suit (e.g. 1H->2H)
_i_limit_raised        # I limit-raised (e.g. 1H->3H)
_i_bid_jacoby_2nt      # I bid Jacoby 2NT (1M->2NT, major only)
_i_bid_new_suit_1level # I bid a new suit at 1-level (e.g. 1D->1S)
_i_bid_1nt             # I responded 1NT
_i_bid_2_over_1        # I bid a new suit at 2-level (e.g. 1H->2C)
_i_jump_shifted        # I jump shifted (e.g. 1H->2S)
_i_bid_2nt_over_minor  # I bid 2NT over a minor (1m->2NT, GF)
_i_bid_3nt             # I bid 3NT
```

### Partner's Rebid Classifiers (what opener bid in round 3)

```python
_partner_rebid_own_suit        # Rebid same suit at cheapest level
_partner_jump_rebid_own_suit   # Jump rebid same suit
_partner_rebid_new_suit        # New suit (non-reverse)
_partner_reversed              # Reverse bid (higher new suit, 17+)
_partner_jump_shifted          # Jump shift new suit (19+)
_partner_raised_my_suit        # Simple raise of my suit
_partner_jump_raised_my_suit   # Jump raise of my suit
_partner_double_jump_raised    # Double jump raise (4-level)
_partner_rebid_1nt             # Rebid 1NT (12-14)
_partner_rebid_2nt             # Rebid 2NT (18-19)
_partner_rebid_3nt             # Rebid 3NT (19-21)
_partner_game_tried            # Help suit game try (new suit after raise)
_partner_rebid_game            # Partner bid game directly
```

### Suit Helpers

```python
_my_response_suit      # The suit I bid in round 2
_opening_suit          # Partner's opening suit
_partner_rebid_suit    # Partner's rebid suit
_fourth_suit           # The only unbid suit (for Fourth Suit Forcing)
```

---

## Priority Scheme

Priorities are per-category, so only compete within REBID_RESPONDER. Scheme:

| Range   | Meaning                                     |
|---------|---------------------------------------------|
| 400-500 | Slam exploration, very specific actions      |
| 300-399 | Game bids, game-forcing actions              |
| 200-299 | Invitational actions                         |
| 100-199 | Minimum/preference/sign-off actions          |
| 50-99   | Catch-all passes                             |

Higher priority within a range = more specific conditions.

---

## suit.py -- After 1-of-a-Suit Opening

### A. After I Raised Opener's Major (1M->2M->rebid->?)

I showed 6-10 support points, 3+ trumps.

#### A1. After Help Suit Game Try (1M->2M->3x new suit->?)

Opener showed 16-18 Bergen, asking for help in suit x.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `AcceptGameTryMax` | Max of range (9-10 pts) | 4M | Game | 310 | Accept with near-maximum regardless of help suit |
| `AcceptGameTryHelp` | Help in try suit (A/K/Q or shortness), 7-8 pts | 4M | Game | 305 | Accept: honor or shortness in the asked suit |
| `DeclineGameTry` | Minimum, no help | 3M | Sign-off | 150 | Decline: return to agreed major at 3-level |

"Help" in the game try suit = A, K, Q, singleton, or void in that suit. With a doubleton and no honor, decline.

#### A2. After Re-raise (1M->2M->3M->?)

Opener showed ~16-18 pts, invitational.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `AcceptReraise` | 8-10 support pts | 4M | Game | 300 | Accept invitation |
| `DeclineReraise` | 6-7 support pts | Pass | Sign-off | 130 | Decline invitation |

#### A3. After Direct Game (1M->2M->4M->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterGame` | Always | Pass | -- | 55 | Opener placed the contract |

#### A4. After Pass (1M->2M->Pass)

Auction is over. No reresponse needed (selector fallback handles this).

---

### B. After I Raised Opener's Minor (1m->2m->rebid->?)

I showed 6-10 HCP, adequate support, no 4-card major.

#### B1. After Opener's 3NT (1m->2m->3NT->?)

Opener showed 16+ HCP, balanced, game values.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterMinor3NT` | Always (after minor raise -> 3NT) | Pass | -- | 56 | Opener placed the contract |

#### B2. After Opener's 2NT (1m->2m->2NT->?)

Opener showed ~14-15 HCP, invitational.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Accept2NTAfterMinorRaise` | 9-10 HCP | 3NT | Game | 295 | Accept NT invitation |
| `Decline2NTAfterMinorRaise` | 6-8 HCP | 3m | Sign-off | 140 | Decline: return to minor |

#### B3. After Opener's New Suit (1m->2m->2x->?)

Opener showed a second suit, game-try territory.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Raise2ndSuitAfterMinorRaise` | 4+ support for new suit, 8-10 | 3x | Invit. | 260 | Support opener's second suit |
| `3NTAfterMinorNewSuit` | 9-10 HCP, stoppers | 3NT | Game | 290 | Game in NT |
| `ReturnToMinor` | 6-8, no fit for new suit | 3m | Sign-off | 120 | Return to agreed minor |

---

### C. After I Limit Raised Opener's Major (1M->3M->rebid->?)

I showed 10-12 support pts, 3+ trumps. Opener accepted or declined.

#### C1. After Acceptance (1M->3M->4M->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterAcceptedLimitRaise` | Always | Pass | -- | 55 | Game reached |

#### C2. After Decline (1M->3M->Pass)

Auction over. No reresponse needed.

---

### D. After I Limit Raised Opener's Minor (1m->3m->rebid->?)

#### D1. After 3NT (1m->3m->3NT->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterMinorLimitRaise3NT` | Always | Pass | -- | 55 | Game reached |

#### D2. After 5m (1m->3m->5m->?) or Pass

Auction over or game reached. Pass.

---

### E. After Jacoby 2NT (1M->2NT->rebid->?)

I showed 4+ trumps, 13+ support pts. Game forcing -- trump suit established. My job: decide between game and slam based on opener's rebid.

#### E1. After Shortness Shown (1M->2NT->3x->?)

Opener showed singleton/void in x.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Blackwood4NTAfterShortness` | 16+ support pts, no wasted values in short suit | 4NT | GF | 450 | Slam try via Blackwood |
| `CueBidAfterShortness` | 16+ support pts, void (Blackwood unreliable) | Cue bid cheapest control | GF | 445 | Slam try via cue bid |
| `Bid4MAfterShortness` | 13-15 support pts | 4M | Game | 330 | Settle for game |

#### E2. After Source of Tricks (1M->2NT->4x->?)

Opener showed 5+ card side suit (source of tricks).

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Blackwood4NTAfterSource` | 16+ support pts, fitting honors in source suit | 4NT | GF | 448 | Slam try |
| `Bid4MAfterSource` | 13-15 support pts | 4M | Game | 325 | Settle for game |

#### E3. After 3M Maximum (1M->2NT->3M->?)

Opener showed 18+ HCP, no shortness.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Blackwood4NTAfterMax` | 15+ support pts | 4NT | GF | 446 | Slam try |
| `Bid4MAfterMax` | 13-14 support pts | 4M | Game | 320 | Game only |

#### E4. After 3NT Medium (1M->2NT->3NT->?)

Opener showed 15-17 HCP, no shortness.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Bid4MAfter3NTMedium` | 13-17 support pts | 4M | Game | 315 | Correct to 4M (trump suit agreed) |
| `Blackwood4NTAfter3NTMedium` | 18+ support pts | 4NT | GF | 440 | Slam try |

#### E5. After 4M Minimum (1M->2NT->4M->?)

Opener showed 12-14 HCP, no shortness.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterJacoby4M` | 13-17 support pts | Pass | -- | 55 | Game reached, no slam |
| `Blackwood4NTAfterJacoby4M` | 18+ support pts | 4NT | GF | 435 | Slam try with maximum |

---

### F. After I Bid a New Suit at 1-Level (1x->1y->rebid->?)

I showed 6+ HCP, 4+ cards in my suit. Wide range -- reresponse must classify my hand:
- **Minimum (6-10 HCP)**: Sign off or give preference
- **Invitational (11-12 HCP)**: Invite game
- **Game-forcing (13+ HCP)**: Reach game or explore slam

#### F1. After Opener Rebid 1NT (1x->1y->1NT->?)

Opener showed 12-14 HCP, balanced. Combined range: 18-28. Responder classifies:

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfter1NTRebid` | 13-15 HCP, balanced | 3NT | Game | 340 | Game in NT |
| `4MAfter1NTRebid` | 13+ HCP, 6+ card major | 4M | Game | 345 | Game in own major |
| `JumpOwnSuitAfter1NT` | 13+ HCP, 5+ card major (not 6) | 3y (jump) | GF | 335 | GF, 5+ suit, asks opener to choose 3NT or 4M |
| `NewSuitAfter1NTForcing` | 13+ HCP, 4+ card new suit | New suit | Forcing | 330 | Fourth suit forcing or natural new suit |
| `2NTAfter1NTRebid` | 11-12 HCP | 2NT | Invit. | 250 | Invitational to 3NT |
| `JumpRebidAfter1NT` | 11-12 HCP, 6+ card suit | 3y | Invit. | 245 | Invitational, 6+ cards |
| `NewSuitWeakAfter1NT` | 6-10 HCP, 4+ card new suit (lower than y) | 2-level new suit | Non-forcing | 160 | Weak, shows 4+ cards, non-forcing |
| `RebidOwnSuitAfter1NT` | 6-10 HCP, 6+ card suit | 2y | Non-forcing | 155 | Weak sign-off, 6+ cards |
| `PassAfter1NTRebid` | 6-10 HCP, no 6+ suit, no 4-card side suit | Pass | -- | 60 | Content with 1NT |

#### F2. After Opener Raised My Suit (1x->1y->2y->?)

Opener showed 4+ support, minimum (12-16 pts).

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterRaise` | 13+ HCP (combined 25+), major | 4M | Game | 350 | Bid game in major |
| `3NTAfterRaise` | 13+ HCP, minor, balanced | 3NT | Game | 345 | Bid game in NT (minor raise) |
| `3yInviteAfterRaise` | 11-12 HCP | 3y | Invit. | 255 | Invitational |
| `PassAfterRaise` | 6-10 HCP | Pass | -- | 62 | Content with partscore |

#### F3. After Opener Jump Raised My Suit (1x->1y->3y->?)

Opener showed 4+ support, 17-18 pts. Invitational.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Accept3yJumpRaise` | 9+ HCP, major | 4M | Game | 310 | Accept invitation |
| `Accept3yJumpRaise3NT` | 9+ HCP, minor | 3NT | Game | 308 | Accept in NT (minor) |
| `Decline3yJumpRaise` | 6-8 HCP | Pass | -- | 130 | Decline invitation |

#### F4. After Opener Double Jump Raised (1x->1y->4y->?)

Opener showed 19-21 pts, 4+ support. Game reached.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterDoubleJumpRaise` | Always | Pass | -- | 55 | Game reached |

#### F5. After Opener Rebid Own Suit (1x->1y->2x->?)

Opener showed 6+ cards in opening suit, minimum (12-16 pts).

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfterOwnSuit` | 13+ HCP, balanced, stoppers | 3NT | Game | 340 | Game in NT |
| `4MAfterOwnSuitMajor` | 13+ HCP, 3+ support, opening suit is major | 4M | Game | 345 | Game in opener's major |
| `FourthSuitAfterOwnSuit` | 13+ HCP, no clear bid | Fourth suit | Forcing | 335 | FSF, asks opener to clarify |
| `2NTAfterOwnSuit` | 11-12 HCP | 2NT | Invit. | 250 | Invitational |
| `3xInviteAfterOwnSuit` | 11-12 HCP, 3+ support for opener's suit | 3x | Invit. | 248 | Invitational raise |
| `RebidOwnSuitAfterOwnSuit` | 6-10 HCP, 6+ cards in my suit | 2y | Non-forcing | 155 | Preference for own suit |
| `PreferenceAfterOwnSuit` | 6-10 HCP, 2+ in opener's suit | Pass | -- | 65 | Content with opener's suit |

Note: With 6-10 and preference between opener's two "suits" (first suit rebid), passing 2x is preference. Bidding 2y shows 6+ cards and prefers own suit.

#### F6. After Opener Jump Rebid Own Suit (1x->1y->3x->?)

Opener showed 6+ cards, 17-18 pts. Invitational.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterJumpRebid` | 8+ HCP, 3+ support, major | 4M | Game | 310 | Accept game invitation |
| `3NTAfterJumpRebid` | 8+ HCP, no support for major / minor | 3NT | Game | 308 | Game in NT |
| `PassAfterJumpRebid` | 6-7 HCP | Pass | -- | 130 | Decline invitation |

#### F7. After Opener Bid New Suit Non-Reverse (1x->1y->2z->?)

Opener showed 4+ cards in z, minimum-to-medium (12-18 pts). z ranks below x.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterNewSuit` | 13+ HCP, 5+ own suit, major | 4M | Game | 350 | Game in own major |
| `3NTAfterNewSuit` | 13+ HCP, balanced, stoppers | 3NT | Game | 345 | Game in NT |
| `FourthSuitForcing` | 13+ HCP, no clear game bid | Fourth suit | Forcing | 340 | Ask opener to describe further |
| `RaiseNewSuitInvite` | 11-12 HCP, 4+ support for z | 3z | Invit. | 260 | Invitational raise of second suit |
| `2NTAfterNewSuit` | 11-12 HCP, balanced | 2NT | Invit. | 250 | Invitational |
| `PreferenceToOpenerFirst` | 6-10 HCP, 3+ in opener's first suit | 2x (preference) | Non-forcing | 165 | Preference to opener's first suit |
| `RebidOwnSuitAfterNewSuit` | 6-10 HCP, 6+ cards in my suit | 2y | Non-forcing | 160 | Show long suit |
| `PassAfterNewSuit` | 6-10 HCP, tolerance for z | Pass | -- | 60 | Content with 2z |

#### F8. After Opener Reversed (1x->1y->2z reverse->?)

Opener showed 17+ HCP, first suit longer than second. **Forcing one round** -- responder must bid.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfterReverse` | 13+ HCP, balanced, stoppers | 3NT | Game | 350 | Game in NT |
| `RaiseReverseSuit` | 10+ HCP, 4+ in reverse suit | 3z (raise) | Invit./GF | 280 | Show fit for reverse suit |
| `JumpInOwnSuitAfterReverse` | 10-12 HCP, 6+ cards | 3y | Invit. | 270 | Invitational, good suit |
| `2NTAfterReverse` | 10-12 HCP, balanced | 2NT | Invit. | 260 | Natural, invitational |
| `RebidOwnSuitAfterReverse` | 6-9 HCP, 5+ cards | 2y | Non-forcing | 170 | Cheapest in own suit, minimum |
| `PreferenceAfterReverse` | 6-9 HCP, 3+ in opener's first suit | 3x (cheapest) | Non-forcing | 165 | Cheapest preference, minimum |

SAYC note: After a reverse, responder MUST bid. The cheapest bid in a previously-bid suit (2y or 3x) shows a minimum. 2NT is natural and invitational (11-12).

#### F9. After Opener Jump Shifted (1x->1y->3z->?)

Opener showed 19+ pts, 4+ cards in z. Game forcing.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `RaiseJumpShiftSuit` | 4+ support for z | 4z or raise | GF | 380 | Support opener's second suit |
| `SupportOpenerFirstAfterJS` | 3+ in opening suit | 3x / 4x | GF | 375 | Show support for first suit |
| `RebidOwnSuitAfterJS` | 6+ cards in own suit | 3y / 4y | GF | 370 | Show long suit |
| `3NTAfterJumpShift` | Balanced, no clear fit | 3NT | Game | 365 | Natural NT game |

#### F10. After Opener Bid 2NT (1x->1y->2NT->?)

Opener showed 18-19 HCP, balanced. Combined 24-31.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfter2NTRebid` | 8+ HCP (combined 26+), no major suit agenda | 3NT | Game | 310 | Bid game |
| `4MAfter2NTRebid` | 8+ HCP, 6+ card major | 4M | Game | 315 | Game in own major |
| `3SuitAfter2NTRebid` | 8+ HCP, 5+ cards, exploring | 3-level suit | Forcing | 305 | Natural, forcing (combined 24+) |
| `PassAfter2NTRebid` | 6-7 HCP | Pass | -- | 130 | Decline, minimum |

#### F11. After Opener Bid 3NT (1x->1y->3NT->?)

Opener showed 19-21 HCP, balanced. Game reached.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfter3NTRebid` | Default | Pass | -- | 55 | Game reached |

---

### G. After I Responded 1NT (1M->1NT->rebid->? or 1m->1NT->rebid->?)

I showed 6-10 HCP. Narrow range for reresponses.

#### G1. After Opener Rebid Own Suit (1x->1NT->2x->?)

Opener showed 6+ cards, minimum.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterSuitRebid1NT` | Default | Pass | -- | 60 | Content with partscore |

Note: Responder already denied fit (didn't raise) and has 6-10 HCP. Passing is almost always correct. Extremely rarely might prefer a minor, but this is edge-case territory.

#### G2. After Opener Bid New Lower Suit (1x->1NT->2z->?)

Opener showed 4+ cards in z, minimum.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `RaiseNewSuit1NTResponse` | 8-10 HCP, 4+ support for z | 3z | Invit. | 240 | Invitational raise (max of 1NT range) |
| `PreferenceTo1stSuit1NT` | 6-10 HCP, 3+ in opener's first suit, first suit ranks higher | 2x (preference) | Non-forcing | 165 | Prefer opener's first suit |
| `PassAfterNewSuit1NT` | 6-10 HCP, tolerance for z | Pass | -- | 60 | Content with 2z |

#### G3. After Opener Bid 2NT (1x->1NT->2NT->?)

Opener showed 18-19 HCP. Combined 24-29.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfter2NTOver1NT` | 8-10 HCP | 3NT | Game | 300 | Accept invitation, game |
| `PassAfter2NTOver1NT` | 6-7 HCP | Pass | -- | 130 | Decline |

#### G4. After Opener Jump Rebid Own Suit (1x->1NT->3x->?)

Opener showed 17-18 pts, 6+ cards. Invitational.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterJumpRebidOver1NT` | 8-10, 2+ support, major | 4M | Game | 305 | Accept, game in major |
| `3NTAfterJumpRebidOver1NT` | 8-10, no major support | 3NT | Game | 302 | Accept, game in NT |
| `PassAfterJumpRebidOver1NT` | 6-7 HCP | Pass | -- | 130 | Decline |

#### G5. After Opener Bid 3NT (1x->1NT->3NT->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfter3NTOver1NT` | Default | Pass | -- | 55 | Game reached |

#### G6. After Opener Jump Shifted (1x->1NT->3z jump->?)

Opener showed 19+ pts. Game forcing.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `SupportJumpShiftOver1NT` | 4+ in z | Raise z | GF | 370 | Support opener's suit |
| `3NTAfterJSOver1NT` | No fit, balanced | 3NT | Game | 365 | NT game |
| `ReturnToOpenerSuitAfterJS1NT` | 3+ in opening suit | 3x/4x | GF | 360 | Show belated support |

---

### H. After 2-Over-1 Response (1x->2y->rebid->?)

I showed 10+ HCP. In SAYC, 2-over-1 is forcing one round (not game-forcing as in 2/1 GF systems). I promised a rebid unless opener jumped to game.

#### H1. After Opener Raised My Suit (1x->2y->3y->?)

Opener showed 4+ support.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfterRaise2Over1` | 10-12 HCP, balanced, minor suit | 3NT | Game | 340 | Game in NT |
| `4MAfterRaise2Over1` | 10+ HCP, y is major or M fit available | 4M | Game | 345 | Game in major |
| `GameInMinorAfterRaise` | 13+ HCP, minor, slam interest | 4y (minor) | GF | 380 | Slam try in minor |

#### H2. After Opener Rebid Own Suit (1x->2y->2x->?)

Opener showed 6+ cards, minimum-to-medium.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfter2Over1OwnSuit` | 12+ HCP, 3+ support, major | 4M | Game | 350 | Game in major |
| `3NTAfter2Over1OwnSuit` | 12+ HCP, balanced, stoppers | 3NT | Game | 345 | Game in NT |
| `FourthSuitAfter2Over1` | 12+ HCP, need info | Fourth suit | Forcing | 340 | FSF to clarify |
| `RaiseOpenerAfter2Over1` | 10-12 HCP, 3+ support | 3x (raise) | Invit. | 260 | Invitational raise |
| `RebidOwnSuitAfter2Over1` | 10-12 HCP, 6+ cards | 3y | Invit. | 255 | Invitational, shows extras |
| `2NTAfter2Over1` | 10-12 HCP, balanced | 2NT | Invit. | 250 | Invitational |

#### H3. After Opener Bid New Suit (1x->2y->2z->?)

Three suits now bid. Responder's fourth suit bid = Fourth Suit Forcing.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfter2Over1NewSuit` | 12+ HCP, balanced, fourth suit stopped | 3NT | Game | 345 | Game |
| `FourthSuitAfter2Over1NS` | 12+ HCP, need info | Fourth suit | Forcing | 340 | FSF |
| `RaiseOpenerNewSuit2Over1` | 10+ HCP, 4+ in z | 3z | Invit./GF | 275 | Support second suit |
| `RebidOwnAfter2Over1NS` | 10-12 HCP, 6+ cards | 3y | Invit. | 255 | Show length |
| `2NTAfter2Over1NS` | 10-12 HCP, balanced | 2NT | Invit. | 250 | Natural |

#### H4. After Opener Bid 2NT (1x->2y->2NT->?)

Opener showed 12-14 balanced.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfter2Over1_2NT` | 12+ HCP | 3NT | Game | 340 | Combined 24+ |
| `3SuitAfter2Over1_2NT` | 10-12 HCP, 5+ in a suit | 3-level suit | Forcing | 270 | Natural, exploring |
| `PassAfter2Over1_2NT` | 10-11 HCP, balanced | Pass | -- | 140 | Content with 2NT (combined 22-25) |

---

### I. After I Jump Shifted (1x->jump->rebid->?)

I showed 19+ HCP. Game forcing, slam interest. Opener described hand; now I place the contract or continue slam investigation.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Blackwood4NTAfterJS` | Fit established, 19+ pts | 4NT | GF | 460 | Slam investigation |
| `RaiseToSlamAfterJS` | Combined 33+ pts, fit | 6M/6NT | Slam | 470 | Bid slam directly |
| `4MAfterJS` | Fit, game values only | 4M | Game | 350 | Settle for game |
| `3NTAfterJS` | No fit, balanced | 3NT | Game | 345 | NT game |
| `ShowSecondSuitAfterJS` | 5-5+, exploring | New suit | GF | 380 | Show shape |

---

### J. After I Bid 2NT Over Minor (1m->2NT->rebid->?)

I showed 13-15 HCP, balanced, no 4-card major. Game forcing.

#### J1. After Opener Showed a Major (1m->2NT->3M->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Raise3MAfter2NTMinor` | 4+ in M | 4M | Game | 350 | Game in major |
| `3NTAfter2NTMinorMajor` | No fit in M | 3NT | Game | 340 | Game in NT |

#### J2. After Opener Rebid Own Minor (1m->2NT->3m->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfter2NTMinorRebid` | Default (balanced, game values) | 3NT | Game | 340 | Game in NT |

#### J3. After Opener Bid 3NT (1m->2NT->3NT->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfter2NTMinor3NT` | Default | Pass | -- | 55 | Game reached |

---

### K. After I Bid 3NT Over Major/Minor

Opener usually passes. If opener pulls to 4M or bids further:

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfter3NTResponse` | Default | Pass | -- | 55 | Let opener decide |

---

### L. After I Game Raised Opener's Major (1M->4M)

Opener passes (or explores slam, very rare). No reresponse rules needed -- this is already game.

---

### M. Catch-All Passes

For any auction path not covered by a specific rule above:

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterSuitReresponse` | _partner_opened_1_suit (guard) | Pass | -- | 50 | Catch-all pass |

---

## nt.py -- After 1NT and 2NT Openings

### A. After Stayman Over 1NT (1NT->2C->rebid->?)

I bid Stayman showing 8+ HCP with a 4-card major (or garbage Stayman).

#### A1. After 2D (No Major Found)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfterStayman2D` | 10-15 HCP, no 5-card major | 3NT | Game | 340 | Game in NT |
| `2MAfterStayman2D` | 8-9 HCP, 5-card major | 2M | Invit. | 260 | Invitational, opener can raise with fit or bid 2NT/3NT |
| `3MAfterStayman2D` | 10+ HCP, 5-card major | 3M | GF | 330 | Game forcing, 5-card suit |
| `2NTAfterStayman2D` | 8-9 HCP, no 5-card major | 2NT | Invit. | 250 | Invitational |
| `3mAfterStayman2D` | 10+ HCP, 5+ minor, slam interest | 3m | Forcing | 320 | Slam try in minor |
| `PassAfterStayman2D` | <8 HCP (garbage Stayman with 4-4 majors) | Pass | -- | 55 | Weak, play 2D |

#### A2. After 2H (4+ Hearts Found)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4HAfterStayman2H` | 10+ HCP, 4+ hearts | 4H | Game | 350 | Game in hearts |
| `3HAfterStayman2H` | 8-9 HCP, 4+ hearts | 3H | Invit. | 260 | Invitational raise |
| `3NTAfterStayman2HNoFit` | 10-15 HCP, no heart fit (had 4 spades only) | 3NT | Game | 340 | Game in NT |
| `2NTAfterStayman2HNoFit` | 8-9 HCP, no heart fit | 2NT | Invit. | 250 | Invitational NT |
| `2SAfterStayman2H` | 8-9 HCP, 5 spades (used Stayman for hearts, no fit) | 2S | Invit. | 255 | Show 5 spades, invitational |
| `PassAfterStayman2H` | <8 HCP (garbage Stayman, happy with 2H) | Pass | -- | 55 | Weak, play 2H |

#### A3. After 2S (4+ Spades Found, Denies 4 Hearts)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4SAfterStayman2S` | 10+ HCP, 4+ spades | 4S | Game | 350 | Game in spades |
| `3SAfterStayman2S` | 8-9 HCP, 4+ spades | 3S | Invit. | 260 | Invitational raise |
| `3NTAfterStayman2SNoFit` | 10-15 HCP, no spade fit (had 4 hearts only) | 3NT | Game | 340 | Game in NT |
| `2NTAfterStayman2SNoFit` | 8-9 HCP, no spade fit | 2NT | Invit. | 250 | Invitational NT |
| `PassAfterStayman2S` | <8 HCP (garbage Stayman, happy with 2S) | Pass | -- | 55 | Weak, play 2S |

---

### B. After Jacoby Transfer Over 1NT (1NT->2D/2H->completion->?)

#### B1. After Normal Completion (1NT->2D->2H or 1NT->2H->2S)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterTransfer` | 10+ HCP, 6+ card major | 4M | Game | 350 | Game in major |
| `3NTAfterTransfer` | 10-15 HCP, 5-card major (opener picks 3NT or 4M) | 3NT | Game | 340 | Offer choice |
| `3MAfterTransfer` | 8-9 HCP, 6+ card major | 3M | Invit. | 260 | Invitational |
| `2NTAfterTransfer` | 8-9 HCP, 5-card major | 2NT | Invit. | 250 | Invitational (opener picks 2NT/3M/3NT) |
| `NewSuitAfterTransfer` | 10+ HCP, 5-4+ shape, second suit | 3-level new suit | Forcing | 330 | Natural, game forcing, shows second suit |
| `PassAfterTransfer` | 0-7 HCP | Pass | -- | 55 | Weak sign-off in major |

#### B2. After Super-Accept (1NT->2D->3H or 1NT->2H->3S)

Opener showed 17 HCP maximum with 4-card support.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterSuperAccept` | 8+ HCP | 4M | Game | 350 | Game with fit confirmed |
| `SlamTryAfterSuperAccept` | 15+ HCP | 4NT (Blackwood) | GF | 440 | Slam investigation |
| `PassAfterSuperAccept` | 0-7 HCP | Pass | -- | 55 | Still too weak for game (rare) |

---

### C. After 2S Puppet Over 1NT (1NT->2S->3C->?)

Opener completed the puppet to 3C as forced.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterPuppet` | Long clubs (6+) | Pass | -- | 100 | Play 3C |
| `3DAfterPuppet` | Long diamonds (6+) | 3D | Sign-off | 110 | Correct to diamonds |

---

### D. After Gerber Ace Response Over 1NT (1NT->4C->4D/4H/4S/4NT->?)

I asked for aces; opener showed their count.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `6NTAfterGerber` | Enough aces for small slam | 6NT | Slam | 470 | Bid slam |
| `5NTKingAskAfterGerber` | All 4 aces accounted for, exploring grand | 5NT | GF | 465 | Ask for kings |
| `5NTSignoffAfterGerber` | Not enough aces, need to sign off below slam | 5NT | Sign-off | 410 | Sign-off (or bid 5 of suit) |
| `4NTSignoffAfterGerber` | Opener showed 0 aces (4D response), stop | 4NT | Sign-off | 400 | Play 4NT |

Note: Signing off after Gerber is complex. If the response is 4D (0/4 aces) and responder wants to stop, they bid 4NT. If the response was higher, signing off is harder (typically 5NT asks opener to pick a slam).

---

### E. After Texas Transfer Completion (1NT->4D->4H or 1NT->4H->4S->?)

Game reached. Transfer was a sign-off.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterTexas` | Default | Pass | -- | 55 | Game reached |

---

### F. Responses After 2NT Opening (2NT->response->rebid->?)

2NT showed 20-21 HCP, balanced. Structure mirrors 1NT but at higher level and with tighter ranges.

#### F1. After Stayman Over 2NT (2NT->3C->3D/3H/3S->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterStayman2NT` | 4+ fit for shown major | 4M | Game | 350 | Game in major |
| `3NTAfterStayman2NT` | No fit | 3NT | Game | 340 | Game in NT |
| `3MAfterStayman2NT3D` | 5-card major (after 3D = no major) | 3M | GF | 335 | Smolen: shows 5-card major (GF) |

Note: Over 2NT Stayman, responder should have GF values (5+ HCP). With 4-4 in majors, Stayman finds the fit; without, bid 3NT.

#### F2. After Jacoby Transfer Over 2NT (2NT->3D->3H or 2NT->3H->3S->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterTransfer2NT` | 5+ card major (any HCP with 2NT opener) | 4M | Game | 350 | Game in major |
| `3NTAfterTransfer2NT` | 5-card major, no slam interest | 3NT | Game | 340 | Offer choice |
| `SlamTryAfterTransfer2NT` | 10+ HCP, 6+ card major | 4NT | GF | 440 | Quantitative slam try |
| `PassAfterTransfer2NT` | Very weak, 5-card suit | Pass | -- | 55 | Extremely rare (weak with 5-card suit over 2NT) |

#### F3. After Puppet Over 2NT (2NT->3S->4C->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterPuppet2NT` | Long clubs | Pass | -- | 100 | Play 4C |
| `4DAfterPuppet2NT` | Long diamonds | 4D | Sign-off | 110 | Correct to diamonds |

#### F4. After Gerber Over 2NT (2NT->4C->response->?)

Same structure as Gerber over 1NT but at higher level.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `6NTAfterGerber2NT` | Enough aces | 6NT | Slam | 470 | Slam |
| `5NTKingAskAfterGerber2NT` | All aces, grand interest | 5NT | GF | 465 | King ask |
| `4NTSignoffAfterGerber2NT` | Not enough aces (0/4 response) | 4NT | Sign-off | 400 | Stop |

#### F5. Other 2NT Responses Already Placed

- 2NT->3NT: opener passes (game reached). No round 4.
- 2NT->4NT quantitative: opener accepts (6NT) or passes (4NT). If opener bid 6NT, pass. If opener passed, auction over.

---

### G. Catch-All Passes for NT

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterNTReresponse` | Guard: partner opened NT | Pass | -- | 50 | Catch-all |

---

## strong.py -- After 2C Opening

### A. After 2C->2D Waiting->Suit Rebid (2C->2D->2M or 3m->?)

Opener showed a strong hand with a natural suit. Game forcing (bidding must continue to at least 3 of a major or 4 of a minor).

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `RaiseOpenerSuitAfter2C` | 3+ support, any HCP | Raise (3M or 4m) | GF | 350 | Support opener's suit |
| `BidOwnSuitAfter2C` | 5+ card suit, 5+ HCP | New suit | GF | 340 | Show a real suit |
| `2NTNegativeAfter2C` | No support, no 5+ suit, 0-4 HCP | 2NT (cheapest NT) | Negative | 130 | Second negative / waiting |
| `3NTAfter2CSuit` | 5-7 HCP, balanced, no fit | 3NT | Game | 335 | Game in NT |

Note: After 2C->2D->2M, responder with 0-4 HCP and no fit bids the cheapest NT (often called "second negative"). With 5+ HCP, responder bids naturally.

### B. After 2C->2D->2NT (22-24 Balanced)

Treat as a 2NT opening equivalent. Responder's round 4 bids:

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `Stayman3CAfter2C2NT` | 4-card major, 3+ HCP | 3C | Stayman | 380 | Stayman over 22-24 NT |
| `Transfer3DAfter2C2NT` | 5+ hearts | 3D | Transfer | 370 | Transfer to hearts |
| `Transfer3HAfter2C2NT` | 5+ spades | 3H | Transfer | 370 | Transfer to spades |
| `3NTAfter2C2NT` | 3-8 HCP, balanced, no 4M / 5M | 3NT | Game | 340 | Game in NT |
| `4NTQuantAfter2C2NT` | 9-10 HCP, balanced | 4NT | Invit. | 430 | Quantitative slam try |
| `4CGerberAfter2C2NT` | 12+ HCP, slam interest | 4C | GF | 450 | Gerber ace ask |
| `PassAfter2C2NT` | 0-2 HCP | Pass | -- | 55 | Very weak, stop in 2NT |

### C. After 2C->2D->3NT (25-27 Balanced)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4CGerberAfter2C3NT` | Slam interest | 4C | GF | 450 | Gerber ace ask |
| `4NTQuantAfter2C3NT` | 5-6 HCP, balanced | 4NT | Invit. | 430 | Quantitative |
| `PassAfter2C3NT` | 0-4 HCP | Pass | -- | 55 | Content with 3NT |

### D. After 2C->Positive Response->Rebid

Opener rebid after a positive response (2H/2S/3C/3D/2NT). Game forcing throughout.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `RaiseOpenerAfterPositive2C` | 4+ support for opener's rebid suit | Raise | GF | 360 | Support opener |
| `RebidOwnSuitAfterPositive2C` | 6+ cards in own suit | Rebid suit | GF | 355 | Show extra length |
| `NewSuitAfterPositive2C` | 4+ card new suit | New suit | GF | 350 | Natural |
| `3NTAfterPositive2C` | Balanced, no fit | 3NT | Game | 340 | NT game |
| `4NTBlackwoodAfterPositive2C` | Fit established, slam interest | 4NT | GF | 450 | Blackwood |

---

## preempt.py -- After Preemptive Openings

### A. After Weak Two->Feature Ask (2M->2NT->rebid->?)

I bid 2NT (14+ HCP) asking for a feature. Opener's rebid:

#### A1. After Opener Showed Feature (2M->2NT->3x->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `3NTAfterFeature` | Stoppers in unbid suits, feature helps | 3NT | Game | 340 | Game in NT with feature |
| `4MAfterFeature` | 3+ support for opener's major | 4M | Game | 345 | Game in major |
| `PassAfterFeature3M` | Feature was 3M (rebid own suit, min) | Pass | -- | 65 | Opener showed minimum, stop |

Note: If opener rebid 3 of their own suit (e.g. 2H->2NT->3H), that means minimum, no feature. Responder can pass.

#### A2. After Opener Bid 3NT (Maximum, No Feature)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfter3NTFeatureAsk` | Default | Pass | -- | 55 | Opener placed 3NT |
| `4MAfter3NTFeatureAsk` | Prefers major game, 3+ support | 4M | Game | 340 | Correct to major |

#### A3. After Opener Rebid Own Suit (Minimum)

2M->2NT->3M means opener is minimum.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterMinFeatureAsk` | Default | Pass | -- | 60 | Stop, opener is minimum |
| `3NTAfterMinFeatureAsk` | Strong hand (16+ HCP), stoppers | 3NT | Game | 310 | Try game anyway |

---

### B. After Weak Two->New Suit Response (2M->new suit->rebid->?)

I bid a new suit (14+ HCP, 5+ cards, forcing). Opener raised or rebid.

#### B1. After Opener Raised My Suit

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterWeakTwoRaise` | Game values | 4M or game | Game | 340 | Bid game |
| `3NTAfterWeakTwoRaise` | Balanced, stoppers | 3NT | Game | 335 | NT game |
| `PassAfterWeakTwoRaise` | Content with partscore | Pass | -- | 60 | Stop |

#### B2. After Opener Rebid Own Suit

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `4MAfterWeakTwoRebid` | 3+ support, game values | 4M | Game | 340 | Game in opener's major |
| `3NTAfterWeakTwoRebid` | Stoppers, no support | 3NT | Game | 335 | NT game |
| `PassAfterWeakTwoRebid` | No game | Pass | -- | 60 | Stop |

---

### C. After 3-Level Preempt Response (3x->response->rebid->?)

Most 3-level auctions resolve in round 3. The few round 4 cases:

#### C1. After Opener Raised My Suit (3x->new suit->raise->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `GameAfter3LevelRaise` | Game values | Game bid | Game | 340 | Bid game |
| `PassAfter3LevelRaise` | Content | Pass | -- | 60 | Stop |

#### C2. After Opener Rebid Own Suit (3x->new suit->4x->?)

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfter3LevelRebid` | Default | Pass | -- | 55 | Game already reached or stop |

---

### D. After 4-Level Preempt

Auctions after 4-level preempts virtually never reach round 4.

| Rule | Conditions | Bid | Forcing | Priority | Notes |
|------|-----------|-----|---------|----------|-------|
| `PassAfterPreemptReresponse` | Guard: partner preempted | Pass | -- | 50 | Catch-all |

---

## Fourth Suit Forcing -- Special Convention

Fourth Suit Forcing (FSF) is a key responder's rebid tool that applies across multiple auction paths. When three suits have been bid naturally, responder's bid of the fourth suit is:

- **Forcing for one round**
- **May be artificial** -- does not necessarily show length
- Shows **game-invitational values or better** (11+ HCP)
- Asks opener to further describe their hand

FSF appears in suit.py rules F7, F8, H2, H3 as an option for responder with 13+ HCP. The fourth suit computation should be a shared helper:

```python
def _fourth_suit(ctx: BiddingContext) -> Suit | None:
    """The only unbid suit, or None if fewer than 3 suits have been bid."""
```

---

## Testing Strategy

1. **Per-rule unit tests**: Each rule gets at least one test with a representative hand + auction, following the pattern in existing test files.

2. **Integration tests**: Full auction sequences through `create_sayc_registry()` to verify phase detection routes to REBID_RESPONDER and the correct rule wins.

3. **Coverage tests**: For each opener rebid type, test that at least one reresponse rule matches. Use `think()` to verify no crashes.

4. **Edge cases**:
   - After opener passes (no reresponse needed)
   - After game is already reached (pass)
   - Garbage Stayman (pass after 2D/2H/2S)
   - Very weak hands after 2C opening

---

## Implementation Order

1. **suit.py** (largest, most complex) -- implement in sections:
   a. Helpers + guard conditions
   b. After raise (A, B sections) -- simplest reresponses
   c. After limit raise (C, D sections) -- mostly pass
   d. After Jacoby 2NT (E) -- slam territory
   e. After new suit at 1-level (F) -- most rules
   f. After 1NT response (G) -- narrow range
   g. After 2-over-1 (H) -- game-try territory
   h. After jump shift (I) -- slam territory
   i. After 2NT over minor (J) -- game forcing
   j. Catch-all passes

2. **nt.py** -- after Stayman, transfers, Gerber, 2NT paths

3. **strong.py** -- after 2C, relatively small

4. **preempt.py** -- after weak two, 3-level, smallest file

---

## Estimated Rule Count

| File | Rules | Notes |
|------|-------|-------|
| suit.py | ~85 | By far the largest; many opener rebid variants |
| nt.py | ~45 | Stayman/transfer continuations are well-defined |
| strong.py | ~18 | 2C paths are somewhat constrained |
| preempt.py | ~14 | Most preempt auctions end by round 3 |
| **Total** | **~162** | |

---

## SAYC Accuracy Notes

- **Fourth Suit Forcing**: Explicitly part of SAYC (research/05-conventions.md).
- **Garbage Stayman**: Standard SAYC -- using Stayman with 4-4 majors and weak hand, planning to pass any response.
- **Super-accept continuations**: After opener super-accepts a transfer, responder has game-forcing values or better.
- **2C->2D->2NT treated like 2NT opening**: Standard SAYC (research/00-overview.md notrump ladder).
- **Bergen points**: Used by opener after a fit. Responder uses support points when raising.
- **Not included**: Lebensohl (over reverses), New Minor Forcing, Bergen Raises -- these are NOT part of SAYC.
