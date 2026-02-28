# Exhaustive Audit: reresponse/suit/new_suit.py

## Scope

This file covers **responder's second bid after bidding a new suit at the 1-level**.
The auction shape is `1x -> 1y -> rebid -> ?` where:
- `1x` = partner's opening (1C, 1D, 1H, or 1S)
- `1y` = my new-suit response at the 1-level (y ranks above x)
- `rebid` = opener's rebid (any legal bid)
- `?` = my reresponse (what this file determines)

Guard: `_i_bid_new_suit_1level` ensures resp.level == 1, not NT, resp.suit != opening.suit.

---

## All Possible 1x -> 1y Combinations

| # | Opening | Response | Response suit type |
|---|---------|----------|--------------------|
| 1 | 1C | 1D | minor |
| 2 | 1C | 1H | major |
| 3 | 1C | 1S | major |
| 4 | 1D | 1H | major |
| 5 | 1D | 1S | major |
| 6 | 1H | 1S | major |

---

## All Possible Opener Rebids by Auction

For each 1x->1y, every legal opener rebid that SAYC theory can produce.
Bid ordering: sort_key = level*10 + suit_value (C=1,D=2,H=3,S=4,NT=5).

### After 1C -> 1D (last bid = 1D, sort_key 12)

| Rebid | Sort key | Type | Section | Guard match | Notes |
|-------|----------|------|---------|-------------|-------|
| 1H | 13 | New suit at 1-level | F7 | `partner_rebid_new_suit` (level==1) | Min |
| 1S | 14 | New suit at 1-level | F7 | `partner_rebid_new_suit` (level==1) | Min |
| 1NT | 15 | NT rebid | F1 | `_partner_rebid_1nt` | Min 12-14 |
| 2C | 21 | Rebid own suit | F5 | `partner_rebid_own_suit` | Min |
| 2D | 22 | Raise my suit | F2 | `partner_raised_my_suit` | Min |
| 2H | 23 | Jump shift | F9 | `partner_jump_shifted` (cheapest H=1H, jumped) | Max 19-21 |
| 2S | 24 | Jump shift | F9 | `partner_jump_shifted` (cheapest S=1S, jumped) | Max 19-21 |
| 2NT | 25 | NT rebid | F10 | `partner_rebid_2nt` | Max 18-19 |
| 3C | 31 | Jump rebid own suit | F6 | `partner_jump_rebid_own_suit` | Med 17-18 |
| 3D | 32 | Jump raise my suit | F3 | `_partner_jump_raised_my_suit` | Med 17-18 |
| 3NT | 35 | NT rebid | F11 | `partner_rebid_3nt` | Max 19-21 |
| 4C | 41 | Dbl-jump rebid own suit | **NONE** | No guard matches | Max 19-21 |
| 4D | 42 | Dbl-jump raise my suit | F4 | `_partner_double_jump_raised` | Max 19-21 |

**BUG**: 2H and 2S also match `_partner_reversed` (H>C/S>C, level 2), but they are jump shifts.
No true reverse is possible after 1C->1D (all suits > C available at 1-level above 1D).

### After 1C -> 1H (last bid = 1H, sort_key 13)

| Rebid | Sort key | Type | Section | Guard match | Notes |
|-------|----------|------|---------|-------------|-------|
| 1S | 14 | New suit at 1-level | F7 | `partner_rebid_new_suit` (level==1) | Min |
| 1NT | 15 | NT rebid | F1 | `_partner_rebid_1nt` | Min 12-14 |
| 2C | 21 | Rebid own suit | F5 | `partner_rebid_own_suit` | Min |
| 2D | 22 | **Reverse** | F8 | `_partner_reversed` (D>C, cheapest D after 1H = 2D) | Med 17+ |
| 2H | 23 | Raise my suit | F2 | `partner_raised_my_suit` | Min |
| 2S | 24 | Jump shift | F9 | `partner_jump_shifted` (cheapest S=1S, jumped) | Max 19-21 |
| 2NT | 25 | NT rebid | F10 | `partner_rebid_2nt` | Max 18-19 |
| 3C | 31 | Jump rebid own suit | F6 | `partner_jump_rebid_own_suit` | Med 17-18 |
| 3D | 32 | Jump shift | F9 | `partner_jump_shifted` (cheapest D=2D, jumped) | Max 19-21 |
| 3H | 33 | Jump raise my suit | F3 | `_partner_jump_raised_my_suit` | Med 17-18 |
| 3NT | 35 | NT rebid | F11 | `partner_rebid_3nt` | Max 19-21 |
| 4C | 41 | Dbl-jump rebid own suit | **NONE** | No guard matches | Max 19-21 |
| 4H | 43 | Dbl-jump raise my suit | F4 | `_partner_double_jump_raised` | Max 19-21 |

**BUG**: 2S also matches `_partner_reversed` (S>C, level 2), but it is a jump shift.
True reverse: 2D only.

### After 1C -> 1S (last bid = 1S, sort_key 14)

| Rebid | Sort key | Type | Section | Guard match | Notes |
|-------|----------|------|---------|-------------|-------|
| 1NT | 15 | NT rebid | F1 | `_partner_rebid_1nt` | Min 12-14 |
| 2C | 21 | Rebid own suit | F5 | `partner_rebid_own_suit` | Min |
| 2D | 22 | **Reverse** | F8 | `_partner_reversed` (D>C, cheapest D after 1S = 2D) | Med 17+ |
| 2H | 23 | **Reverse** | F8 | `_partner_reversed` (H>C, cheapest H after 1S = 2H) | Med 17+ |
| 2S | 24 | Raise my suit | F2 | `partner_raised_my_suit` | Min |
| 2NT | 25 | NT rebid | F10 | `partner_rebid_2nt` | Max 18-19 |
| 3C | 31 | Jump rebid own suit | F6 | `partner_jump_rebid_own_suit` | Med 17-18 |
| 3D | 32 | Jump shift | F9 | `partner_jump_shifted` (cheapest D=2D, jumped) | Max 19-21 |
| 3H | 33 | Jump shift | F9 | `partner_jump_shifted` (cheapest H=2H, jumped) | Max 19-21 |
| 3S | 34 | Jump raise my suit | F3 | `_partner_jump_raised_my_suit` | Med 17-18 |
| 3NT | 35 | NT rebid | F11 | `partner_rebid_3nt` | Max 19-21 |
| 4C | 41 | Dbl-jump rebid own suit | **NONE** | No guard matches | Max 19-21 |
| 4S | 44 | Dbl-jump raise my suit | F4 | `_partner_double_jump_raised` | Max 19-21 |

No 1-level new suit possible (S is highest suit). True reverses: 2D, 2H.
No new suit non-reverse at 2-level (nothing ranks below C).

### After 1D -> 1H (last bid = 1H, sort_key 13)

| Rebid | Sort key | Type | Section | Guard match | Notes |
|-------|----------|------|---------|-------------|-------|
| 1S | 14 | New suit at 1-level | F7 | `partner_rebid_new_suit` (level==1) | Min |
| 1NT | 15 | NT rebid | F1 | `_partner_rebid_1nt` | Min 12-14 |
| 2C | 21 | New suit non-reverse | F7 | `partner_rebid_new_suit` (C<D) | Min |
| 2D | 22 | Rebid own suit | F5 | `partner_rebid_own_suit` | Min |
| 2H | 23 | Raise my suit | F2 | `partner_raised_my_suit` | Min |
| 2S | 24 | Jump shift | F9 | `partner_jump_shifted` (cheapest S=1S, jumped) | Max 19-21 |
| 2NT | 25 | NT rebid | F10 | `partner_rebid_2nt` | Max 18-19 |
| 3C | 31 | Jump shift | F9 | `partner_jump_shifted` (cheapest C=2C, jumped) | Max 19-21 |
| 3D | 32 | Jump rebid own suit | F6 | `partner_jump_rebid_own_suit` | Med 17-18 |
| 3H | 33 | Jump raise my suit | F3 | `_partner_jump_raised_my_suit` | Med 17-18 |
| 3NT | 35 | NT rebid | F11 | `partner_rebid_3nt` | Max 19-21 |
| 4D | 42 | Dbl-jump rebid own suit | **NONE** | No guard matches | Max 19-21 |
| 4H | 43 | Dbl-jump raise my suit | F4 | `_partner_double_jump_raised` | Max 19-21 |

**BUG**: 2S also matches `_partner_reversed` (S>D, level 2), but it is a jump shift.
No true reverse possible (only S>D, but cheapest S=1S at level 1).

### After 1D -> 1S (last bid = 1S, sort_key 14)

| Rebid | Sort key | Type | Section | Guard match | Notes |
|-------|----------|------|---------|-------------|-------|
| 1NT | 15 | NT rebid | F1 | `_partner_rebid_1nt` | Min 12-14 |
| 2C | 21 | New suit non-reverse | F7 | `partner_rebid_new_suit` (C<D) | Min |
| 2D | 22 | Rebid own suit | F5 | `partner_rebid_own_suit` | Min |
| 2H | 23 | **Reverse** | F8 | `_partner_reversed` (H>D, cheapest H after 1S = 2H) | Med 17+ |
| 2S | 24 | Raise my suit | F2 | `partner_raised_my_suit` | Min |
| 2NT | 25 | NT rebid | F10 | `partner_rebid_2nt` | Max 18-19 |
| 3C | 31 | Jump shift | F9 | `partner_jump_shifted` (cheapest C=2C, jumped) | Max 19-21 |
| 3D | 32 | Jump rebid own suit | F6 | `partner_jump_rebid_own_suit` | Med 17-18 |
| 3H | 33 | Jump shift | F9 | `partner_jump_shifted` (cheapest H=2H, jumped) | Max 19-21 |
| 3S | 34 | Jump raise my suit | F3 | `_partner_jump_raised_my_suit` | Med 17-18 |
| 3NT | 35 | NT rebid | F11 | `partner_rebid_3nt` | Max 19-21 |
| 4D | 42 | Dbl-jump rebid own suit | **NONE** | No guard matches | Max 19-21 |
| 4S | 44 | Dbl-jump raise my suit | F4 | `_partner_double_jump_raised` | Max 19-21 |

True reverse: 2H only.

### After 1H -> 1S (last bid = 1S, sort_key 14)

| Rebid | Sort key | Type | Section | Guard match | Notes |
|-------|----------|------|---------|-------------|-------|
| 1NT | 15 | NT rebid | F1 | `_partner_rebid_1nt` | Min 12-14 |
| 2C | 21 | New suit non-reverse | F7 | `partner_rebid_new_suit` (C<H) | Min |
| 2D | 22 | New suit non-reverse | F7 | `partner_rebid_new_suit` (D<H) | Min |
| 2H | 23 | Rebid own suit | F5 | `partner_rebid_own_suit` | Min |
| 2S | 24 | Raise my suit | F2 | `partner_raised_my_suit` | Min |
| 2NT | 25 | NT rebid | F10 | `partner_rebid_2nt` | Max 18-19 |
| 3C | 31 | Jump shift | F9 | `partner_jump_shifted` (cheapest C=2C, jumped) | Max 19-21 |
| 3D | 32 | Jump shift | F9 | `partner_jump_shifted` (cheapest D=2D, jumped) | Max 19-21 |
| 3H | 33 | Jump rebid own suit | F6 | `partner_jump_rebid_own_suit` | Med 17-18 |
| 3S | 34 | Jump raise my suit | F3 | `_partner_jump_raised_my_suit` | Med 17-18 |
| 3NT | 35 | NT rebid | F11 | `partner_rebid_3nt` | Max 19-21 |
| 4H | 43 | Dbl-jump rebid own suit | **NONE** | No guard matches | Max 19-21 |
| 4S | 44 | Dbl-jump raise my suit | F4 | `_partner_double_jump_raised` | Max 19-21 |

No reverse possible (no suit ranks above H except S which is response suit).

---

## Bugs

### BUG 1: `_partner_reversed` over-matches jump shifts

**Location**: new_suit.py lines 110-120, helpers.py lines 117-123

The condition only checks `rebid.suit > opening.suit and rebid.level == 2`. It does NOT verify the bid is at the cheapest level in that suit. When the new suit ranks above the response suit, the cheapest bid is at the 1-level, and a 2-level bid is a jump -- not a reverse.

**Affected auctions** (where `_partner_reversed` incorrectly returns True):
- 1C->1D->2H (jump shift, not reverse)
- 1C->1D->2S (jump shift, not reverse)
- 1C->1H->2S (jump shift, not reverse)
- 1D->1H->2S (jump shift, not reverse)

**Impact**: In practice, F9 (jump shift) rules have higher priorities (375-444) than F8 (reverse) rules (198-368), so the correct rules fire. But F8 rules ALSO match, polluting thought output and creating fragile correctness.

**Fix**: Add cheapest-level check to both `_partner_reversed` (new_suit.py) and `partner_reversed` (helpers.py):
```python
cheapest = cheapest_bid_in_suit(rebid.suit, my_response(ctx))
return rebid.suit > opening_suit(ctx) and rebid.level == cheapest.level
```

**True reverses** (where the fix preserves correct behavior):
- 1C->1H->2D: cheapest D after 1H = 2D, level matches. Correct.
- 1C->1S->2D: cheapest D after 1S = 2D. Correct.
- 1C->1S->2H: cheapest H after 1S = 2H. Correct.
- 1D->1S->2H: cheapest H after 1S = 2H. Correct.

### BUG 2: Fourth Suit Forcing can produce a 1-level bid

**Location**: helpers.py `find_fourth_suit_bid()`, used by `FourthSuitForcing` and `FourthSuitAfterOwnSuit`

Per SAYC (research/03-rebids.md line 167): "a bid of the only unbid suit **at the 2-level or higher** is forcing for one round and may be artificial." At the 1-level, a new suit bid is natural, not FSF.

**Affected auctions**:
- 1C->1D->1H->? : 4th suit = S, cheapest S after 1H = **1S** (level 1!)
- 1C->1D->1S->? : 4th suit = H, cheapest H after 1S = **2H** (OK, level 2)
- 1C->1H->1S->? : 4th suit = D, cheapest D after 1S = **2D** (OK, level 2)
- 1D->1H->1S->? : 4th suit = C, cheapest C after 1S = **2C** (OK, level 2)

Only 1C->1D->1H is affected. After that auction, bidding 1S is natural (showing 4+ spades), NOT artificial FSF. The rule should be a natural "new suit at 1-level" rule instead.

**Fix**: Add `bid.level >= 2` check in `find_fourth_suit_bid()`, or filter in the rule's conditions.

---

## Priority Issues

### PRIORITY 1: F1 TwoNTAfter1NTRebid (286) > JumpRebidAfter1NT (280)

With 11-12 HCP and 6+ in the response suit, 2NT fires instead of the jump rebid (3y). With a 6+ card major, 3M invitational is more descriptive and more standard than 2NT. JumpRebidAfter1NT should have higher priority than TwoNTAfter1NTRebid.

**Fix**: Swap priorities (jump rebid ~288, 2NT ~278) or make jump rebid priority 288.

### PRIORITY 2: F10 ThreeNTAfter2NTRebid (339) kills ThreeSuitAfter2NTRebid (334)

Both require 8+ HCP after 2NT rebid. ThreeNT has higher priority and strictly wider conditions (no suit length check). ThreeSuitAfter2NTRebid is **dead code** -- it can never fire. With a 5-card major, bidding 3M lets opener choose between 3NT and 4M.

**Fix**: Give ThreeSuitAfter2NTRebid higher priority than ThreeNTAfter2NTRebid (e.g., 341 vs 339), or restrict ThreeNT to hands without a 5+ card major.

---

## Coverage Gaps

### GAP 1: No guard for opener's double-jump rebid of own suit

Opener can double-jump rebid their suit (e.g., 1H->1S->4H, showing 19-21 self-supporting 6+ suit). No classifier matches:
- `partner_rebid_own_suit`: needs cheapest level (2H) -- fails
- `partner_jump_rebid_own_suit`: needs cheapest+1 (3H) -- fails

**Affected auctions**: 1C->*->4C, 1D->*->4D, 1H->*->4H (if response was 1S)

**Fix**: Add `partner_double_jump_rebid_own_suit` guard and `PassAfterGameInOwnSuit` rule. For majors (4H/4S), game is reached so Pass. For minors (4C/4D), game is NOT reached -- may need 5m or 3NT with extras.

### GAP 2: F1 -- 13+ HCP, long minor, unbalanced, no higher suit after 1NT

After 1x->1y->1NT, with 13+ HCP but: not balanced strict, response was a minor (1D), no 4+ card suit ranking above the response suit.

**Example**: 1C->1D->1NT, hand is 1=3=6=3 with 13 HCP. No rule fires:
- ThreeNTAfter1NTRebid: Balanced(strict=True) fails (6-card suit)
- JumpOwnMajorAfter1NT: response is minor, fails
- FourMAfter1NTRebid: response is minor, fails
- NewSuitAfter1NTForcing: no 4+ suit above D (3 hearts, 3 spades), fails

**How common**: Uncommon. Many such hands would have responded 2NT (over minor with 13+ balanced) rather than 1D. But unbalanced hands with a long minor do respond 1D.

**Fix**: Add a game-forcing jump rebid of own minor (3D/3C) for 13+ HCP, or relax ThreeNTAfter1NTRebid to Balanced(strict=False).

### GAP 3: F2 -- 13+ HCP, minor raised, no stoppers

After 1x->1y->2y (y is minor), with 13+ HCP and no stoppers in unbid suits.

**Example**: 1C->1D->2D, hand is 1=2=6=4, 13 HCP, no stopper in hearts.
- FourMAfterRaise: response is minor, fails
- ThreeNTAfterRaise: stoppers_in_unbid fails

**Fix**: Add a new-suit forcing bid (e.g., 3H asking for stopper), or add 5m game bid. Alternatively, relax the stopper check -- responder with 13+ and a fit can gamble on 3NT.

### GAP 4: F5 -- 13+ HCP after own suit rebid, only 2 distinct suits bid

After 1x->1y->2x (e.g., 1H->1S->2H), only 2 suits have been bid (x and y). `fourth_suit()` returns None (2 unbid suits, not 1). With 13+ HCP, no 3+ support for opener, not balanced with stoppers: no rule fires.

**Example**: 1H->1S->2H, hand is 1=2=4=6, 13 HCP. Has 6 clubs, 4 diamonds, 2 hearts, 1 spade.
- ThreeNTAfterOwnSuit: not balanced, singleton, fails
- FourMAfterOwnSuitMajor: only 2 hearts, fails
- FourthSuitAfterOwnSuit: fourth_suit returns None (C and D both unbid), fails

**Fix**: Add a "new suit forcing" rule for 13+ HCP after opener's own suit rebid. Bid longest unbid suit as a forcing new suit. This is a natural forcing bid (new suit by responder = forcing one round in SAYC), NOT FSF.

### GAP 5: F5/F7 -- 11-12 HCP invitational jump rebid of own suit

After opener's own suit rebid or new suit rebid, with 11-12 HCP and 6+ in response suit but no support for opener: no invitational jump rebid exists.

**Example**: 1H->1S->2H->? with 11 HCP, 6 spades: should bid 3S (invitational). Currently falls to 2NT.
**Example**: 1H->1S->2C->? with 11 HCP, 6 spades: should bid 3S. Currently falls to 2NT.

**Fix**: Add `JumpRebidOwnSuitAfterOwnSuit` (11-12, 6+, priority ~284) and `JumpRebidOwnSuitAfterNewSuit` (11-12, 6+, priority ~289). Both bid 3y invitational.

### GAP 6: F6 -- 8+ HCP after jump rebid of minor, or without stoppers

After opener jump-rebids a minor (e.g., 1C->1H->3C), with 8+ HCP:
- FourMAfterJumpRebid: requires opening_is_major, fails
- ThreeNTAfterJumpRebid: requires stoppers_in_unbid, may fail

An 8-9 HCP hand without stoppers has no matching rule (Pass requires max 7).

**Fix**: Either relax the stopper check on ThreeNTAfterJumpRebid (accept the risk with 8+ HCP), or add a raise-to-5m rule for minor openings, or add a catch-all 3NT without stopper check at a lower priority.

### GAP 7: F8 -- 13+ HCP after reverse, without balanced/stoppers

After a reverse (17+), with 13+ HCP (combined 30+):
- ThreeNTAfterReverse: needs balanced + stoppers, may fail
- RaiseReverseSuit (10+, 4+ support): fires but bids only to cheapest level (invitational), not game-forcing

**Fix**: Add a game-forcing raise of reverse suit (13+ HCP, 4+ support), and a general GF new-suit bid for 13+ without fit. Also cap RaiseReverseSuit at max_hcp=12 (invitational only).

### GAP 8: F7-1LEVEL -- Missing rules for 1-level rebid auctions

When opener rebids a new suit at the 1-level (1C->1D->1H, 1C->1D->1S, 1C->1H->1S, 1D->1H->1S), the F7 rules apply but were designed for 2-level auctions. Three common bid types are missing:

**a) New suit at 1-level (4+ cards, forcing)**:
After 1C->1D->1H, bidding 1S with 4+ spades is natural and forcing. No rule exists.

**b) Weak raise of opener's new suit (6-10, 4+ support)**:
After 1C->1D->1H, raising to 2H with 4+ hearts and 6-10 HCP. No rule exists. (RaiseNewSuitInvite requires 11-12.)

**c) 1NT reresponse (6-10, balanced, no fit)**:
After 1C->1D->1H, bidding 1NT as a sign-off with balanced minimum. No rule exists.

**Fix**: Add three new rules:
- `NewSuitAt1LevelAfterNewSuit`: 6+ HCP, 4+ card suit biddable at 1-level, forcing one round. High priority (~262) since it's the most economical descriptive bid.
- `WeakRaiseNewSuit`: 6-10 HCP, 4+ support for opener's new suit, raise to 2z. Priority ~200.
- `OneNTAfterNewSuit1Level`: 6-10 HCP, balanced, no fit, no new suit. Priority ~100 (above pass).

---

## Accuracy Issues

### ACCURACY 1: Accept3yJumpRaise3NT lacks stopper check

After 1x->1y->3y (jump raise of minor), Accept3yJumpRaise3NT bids 3NT without checking stoppers. With a minor fit and no stoppers, 3NT is risky.

**Fix**: Add `stoppers_in_unbid` condition to Accept3yJumpRaise3NT. If no stoppers, pass (play 3y) or explore.

### ACCURACY 2: RaiseReverseSuit has no max HCP

RaiseReverseSuit has HcpRange(min_hcp=10) with no maximum. A 13+ HCP hand with 4+ in the reverse suit gets an invitational raise when game values are present (opener has 17+ for the reverse, combined 30+).

**Fix**: Cap at max_hcp=12 for invitational, add separate GF raise rule for 13+.

---

## Master Path Table

### How to read this table

- **Auction**: The specific 3-bid sequence (opening -> response -> rebid)
- **HCP**: Responder's HCP range for the reresponse
- **Conditions**: Shape or suit requirements
- **Reresponse**: The specific bid responder should make
- **Rule**: The rule name that covers this path, or **MISSING** if no rule exists
- **Priority**: Rule priority (higher = fires first among matching rules)

Within each section, paths are ordered by priority (highest first). The lowest-priority rule in each section is the catch-all (Pass).

---

### F1: After Opener Rebid 1NT

Applies to: 1C->1D->1NT, 1C->1H->1NT, 1C->1S->1NT, 1D->1H->1NT, 1D->1S->1NT, 1H->1S->1NT

Opener shows 12-14 HCP balanced.

| Auction | HCP | Conditions | Reresponse | Rule | Pri |
|---------|-----|------------|------------|------|-----|
| 1C->1D->1NT | 13+ | 6+ D | **MISSING** (FourMAfter1NTRebid requires major) | **GAP** | - |
| 1C->1D->1NT | 13-15 | balanced strict | 3NT | ThreeNTAfter1NTRebid | 356 |
| 1C->1D->1NT | 13+ | 4+ new suit above D (H or S) | new suit (2H or 2S) | NewSuitAfter1NTForcing | 347 |
| 1C->1D->1NT | 11-12 | any | 2NT | TwoNTAfter1NTRebid | 286 |
| 1C->1D->1NT | 11-12 | 6+ D | 3D | JumpRebidAfter1NT | 280 |
| 1C->1D->1NT | 6-10 | 4+ new suit below D | **impossible** (no suit below D except C = opening) | - | - |
| 1C->1D->1NT | 6-10 | 6+ D | 2D | RebidOwnSuitAfter1NT | 193 |
| 1C->1D->1NT | 6-10 | catch-all | Pass | PassAfter1NTRebid | 97 |
| | | | | | |
| 1C->1H->1NT | 13+ | 6+ H | 4H | FourMAfter1NTRebid | 367 |
| 1C->1H->1NT | 13-15 | balanced strict | 3NT | ThreeNTAfter1NTRebid | 356 |
| 1C->1H->1NT | 13+ | exactly 5 H | 3H | JumpOwnMajorAfter1NT | 349 |
| 1C->1H->1NT | 13+ | 4+ new suit above H (S only) | 2S | NewSuitAfter1NTForcing | 347 |
| 1C->1H->1NT | 11-12 | any | 2NT | TwoNTAfter1NTRebid | 286 |
| 1C->1H->1NT | 11-12 | 6+ H | 3H | JumpRebidAfter1NT | 280 |
| 1C->1H->1NT | 6-10 | 4+ D (below H, not opening C) | 2D | NewSuitWeakAfter1NT | 195 |
| 1C->1H->1NT | 6-10 | 6+ H | 2H | RebidOwnSuitAfter1NT | 193 |
| 1C->1H->1NT | 6-10 | catch-all | Pass | PassAfter1NTRebid | 97 |
| | | | | | |
| 1C->1S->1NT | 13+ | 6+ S | 4S | FourMAfter1NTRebid | 367 |
| 1C->1S->1NT | 13-15 | balanced strict | 3NT | ThreeNTAfter1NTRebid | 356 |
| 1C->1S->1NT | 13+ | exactly 5 S | 3S | JumpOwnMajorAfter1NT | 349 |
| 1C->1S->1NT | 13+ | no higher suit above S | **no NewSuitForcing possible** (S is highest) | - | - |
| 1C->1S->1NT | 11-12 | any | 2NT | TwoNTAfter1NTRebid | 286 |
| 1C->1S->1NT | 11-12 | 6+ S | 3S | JumpRebidAfter1NT | 280 |
| 1C->1S->1NT | 6-10 | 4+ D or 4+ H (below S, not opening C) | 2D or 2H | NewSuitWeakAfter1NT | 195 |
| 1C->1S->1NT | 6-10 | 6+ S | 2S | RebidOwnSuitAfter1NT | 193 |
| 1C->1S->1NT | 6-10 | catch-all | Pass | PassAfter1NTRebid | 97 |
| | | | | | |
| 1D->1H->1NT | 13+ | 6+ H | 4H | FourMAfter1NTRebid | 367 |
| 1D->1H->1NT | 13-15 | balanced strict | 3NT | ThreeNTAfter1NTRebid | 356 |
| 1D->1H->1NT | 13+ | exactly 5 H | 3H | JumpOwnMajorAfter1NT | 349 |
| 1D->1H->1NT | 13+ | 4+ S (above H) | 2S | NewSuitAfter1NTForcing | 347 |
| 1D->1H->1NT | 11-12 | any | 2NT | TwoNTAfter1NTRebid | 286 |
| 1D->1H->1NT | 11-12 | 6+ H | 3H | JumpRebidAfter1NT | 280 |
| 1D->1H->1NT | 6-10 | 4+ C (below H, not opening D) | 2C | NewSuitWeakAfter1NT | 195 |
| 1D->1H->1NT | 6-10 | 6+ H | 2H | RebidOwnSuitAfter1NT | 193 |
| 1D->1H->1NT | 6-10 | catch-all | Pass | PassAfter1NTRebid | 97 |
| | | | | | |
| 1D->1S->1NT | 13+ | 6+ S | 4S | FourMAfter1NTRebid | 367 |
| 1D->1S->1NT | 13-15 | balanced strict | 3NT | ThreeNTAfter1NTRebid | 356 |
| 1D->1S->1NT | 13+ | exactly 5 S | 3S | JumpOwnMajorAfter1NT | 349 |
| 1D->1S->1NT | 13+ | no higher suit above S | **no NewSuitForcing possible** | - | - |
| 1D->1S->1NT | 11-12 | any | 2NT | TwoNTAfter1NTRebid | 286 |
| 1D->1S->1NT | 11-12 | 6+ S | 3S | JumpRebidAfter1NT | 280 |
| 1D->1S->1NT | 6-10 | 4+ C or H (below S, not opening D) | 2C or 2H | NewSuitWeakAfter1NT | 195 |
| 1D->1S->1NT | 6-10 | 6+ S | 2S | RebidOwnSuitAfter1NT | 193 |
| 1D->1S->1NT | 6-10 | catch-all | Pass | PassAfter1NTRebid | 97 |
| | | | | | |
| 1H->1S->1NT | 13+ | 6+ S | 4S | FourMAfter1NTRebid | 367 |
| 1H->1S->1NT | 13-15 | balanced strict | 3NT | ThreeNTAfter1NTRebid | 356 |
| 1H->1S->1NT | 13+ | exactly 5 S | 3S | JumpOwnMajorAfter1NT | 349 |
| 1H->1S->1NT | 13+ | no higher suit above S | **no NewSuitForcing possible** | - | - |
| 1H->1S->1NT | 11-12 | any | 2NT | TwoNTAfter1NTRebid | 286 |
| 1H->1S->1NT | 11-12 | 6+ S | 3S | JumpRebidAfter1NT | 280 |
| 1H->1S->1NT | 6-10 | 4+ C or D (below S, not opening H) | 2C or 2D | NewSuitWeakAfter1NT | 195 |
| 1H->1S->1NT | 6-10 | 6+ S | 2S | RebidOwnSuitAfter1NT | 193 |
| 1H->1S->1NT | 6-10 | catch-all | Pass | PassAfter1NTRebid | 97 |

**F1 priority note**: TwoNTAfter1NTRebid (286) fires before JumpRebidAfter1NT (280). With 11-12 and 6+ in a major, the jump rebid is more descriptive. Fix: swap priorities.

**F1 gap note**: 13+ HCP with minor response (1D), unbalanced, no higher 4+ suit: no rule. Rare but real.

---

### F2: After Opener Raised My Suit

Applies to: 1C->1D->2D, 1C->1H->2H, 1C->1S->2S, 1D->1H->2H, 1D->1S->2S, 1H->1S->2S

Opener shows 12-16 points with 4-card support.

| Auction | HCP | Conditions | Reresponse | Rule | Pri |
|---------|-----|------------|------------|------|-----|
| 1C->1D->2D | 13+ | stoppers in unbid | 3NT | ThreeNTAfterRaise | 360 |
| 1C->1D->2D | 13+ | no stoppers | **MISSING** | **GAP** | - |
| 1C->1D->2D | 11-12 | any | 3D | ThreeYInviteAfterRaise | 287 |
| 1C->1D->2D | 6-10 | catch-all | Pass | PassAfterRaise | 98 |
| | | | | | |
| 1C->1H->2H | 13+ | major | 4H | FourMAfterRaise | 370 |
| 1C->1H->2H | 11-12 | any | 3H | ThreeYInviteAfterRaise | 287 |
| 1C->1H->2H | 6-10 | catch-all | Pass | PassAfterRaise | 98 |
| | | | | | |
| 1C->1S->2S | 13+ | major | 4S | FourMAfterRaise | 370 |
| 1C->1S->2S | 11-12 | any | 3S | ThreeYInviteAfterRaise | 287 |
| 1C->1S->2S | 6-10 | catch-all | Pass | PassAfterRaise | 98 |
| | | | | | |
| 1D->1H->2H | 13+ | major | 4H | FourMAfterRaise | 370 |
| 1D->1H->2H | 11-12 | any | 3H | ThreeYInviteAfterRaise | 287 |
| 1D->1H->2H | 6-10 | catch-all | Pass | PassAfterRaise | 98 |
| | | | | | |
| 1D->1S->2S | 13+ | major | 4S | FourMAfterRaise | 370 |
| 1D->1S->2S | 11-12 | any | 3S | ThreeYInviteAfterRaise | 287 |
| 1D->1S->2S | 6-10 | catch-all | Pass | PassAfterRaise | 98 |
| | | | | | |
| 1H->1S->2S | 13+ | major | 4S | FourMAfterRaise | 370 |
| 1H->1S->2S | 11-12 | any | 3S | ThreeYInviteAfterRaise | 287 |
| 1H->1S->2S | 6-10 | catch-all | Pass | PassAfterRaise | 98 |

**F2 gap**: Only 1C->1D->2D has the gap (minor raised, 13+, no stoppers). All major-suit raises are fully covered.

---

### F3: After Opener Jump Raised My Suit

Applies to: 1C->1D->3D, 1C->1H->3H, 1C->1S->3S, 1D->1H->3H, 1D->1S->3S, 1H->1S->3S

Opener shows 17-18 points with 4-card support (invitational).

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1C->1D->3D | 9+ | minor | 3NT | Accept3yJumpRaise3NT | 338 | **No stopper check!** |
| 1C->1D->3D | 6-8 | catch-all | Pass | Decline3yJumpRaise | 188 | |
| | | | | | | |
| 1C->1H->3H | 9+ | major | 4H | Accept3yJumpRaise | 342 | |
| 1C->1H->3H | 6-8 | catch-all | Pass | Decline3yJumpRaise | 188 | |
| | | | | | | |
| 1C->1S->3S | 9+ | major | 4S | Accept3yJumpRaise | 342 | |
| 1C->1S->3S | 6-8 | catch-all | Pass | Decline3yJumpRaise | 188 | |
| | | | | | | |
| 1D->1H->3H | 9+ | major | 4H | Accept3yJumpRaise | 342 | |
| 1D->1H->3H | 6-8 | catch-all | Pass | Decline3yJumpRaise | 188 | |
| | | | | | | |
| 1D->1S->3S | 9+ | major | 4S | Accept3yJumpRaise | 342 | |
| 1D->1S->3S | 6-8 | catch-all | Pass | Decline3yJumpRaise | 188 | |
| | | | | | | |
| 1H->1S->3S | 9+ | major | 4S | Accept3yJumpRaise | 342 | |
| 1H->1S->3S | 6-8 | catch-all | Pass | Decline3yJumpRaise | 188 | |

**Accuracy issue**: Accept3yJumpRaise3NT (for minors) should check stoppers_in_unbid.

---

### F4: After Opener Double-Jump Raised My Suit

Applies to: 1C->1D->4D, 1C->1H->4H, 1C->1S->4S, 1D->1H->4H, 1D->1S->4S, 1H->1S->4S

Opener shows 19-21 points with 4-card support. For majors, game is reached.

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1C->1D->4D | any | catch-all | Pass | PassAfterDoubleJumpRaise | 87 | 4D is NOT game; may need 5D with extras |
| 1C->1H->4H | any | catch-all | Pass | PassAfterDoubleJumpRaise | 87 | Game reached |
| 1C->1S->4S | any | catch-all | Pass | PassAfterDoubleJumpRaise | 87 | Game reached |
| 1D->1H->4H | any | catch-all | Pass | PassAfterDoubleJumpRaise | 87 | Game reached |
| 1D->1S->4S | any | catch-all | Pass | PassAfterDoubleJumpRaise | 87 | Game reached |
| 1H->1S->4S | any | catch-all | Pass | PassAfterDoubleJumpRaise | 87 | Game reached |

**Note**: 1C->1D->4D is the only minor case. 4D is not game -- may need separate handling for slam exploration, but acceptable to pass for now (opener has already bid aggressively).

---

### F5: After Opener Rebid Own Suit

Applies to: 1C->1D->2C, 1C->1H->2C, 1C->1S->2C, 1D->1H->2D, 1D->1S->2D, 1H->1S->2H

Opener shows 12-16 with 6+ cards in opening suit.
Note: Only 2 distinct suits bid (x and y), so `fourth_suit()` returns None.

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1C->1D->2C | 13+ | 3+ C, C is major? No (minor) | - | - | - | |
| 1C->1D->2C | 13+ | balanced + stoppers | 3NT | ThreeNTAfterOwnSuit | 352 | |
| 1C->1D->2C | 13+ | FSF | None (2 unbid suits) | **GAP** | - | |
| 1C->1D->2C | 13+ | **no fit, no stoppers, no FSF** | **MISSING** | **GAP** | - | Need new-suit forcing |
| 1C->1D->2C | 11-12 | 3+ C | 3C | ThreeXInviteAfterOwnSuit | 281 | |
| 1C->1D->2C | 11-12 | any | 2NT | TwoNTAfterOwnSuit | 282 | |
| 1C->1D->2C | 11-12 | 6+ D | **MISSING** (no jump rebid 3D) | **GAP** | - | Need invitational 3D |
| 1C->1D->2C | 6-10 | 6+ D | 2D | RebidOwnSuitAfterOwnSuit | 192 | |
| 1C->1D->2C | 6-10 | catch-all | Pass | PreferenceAfterOwnSuit | 99 | |
| | | | | | | |
| 1C->1H->2C | 13+ | balanced + stoppers | 3NT | ThreeNTAfterOwnSuit | 352 | |
| 1C->1H->2C | 13+ | **no fit, no stoppers** | **MISSING** | **GAP** | - | |
| 1C->1H->2C | 11-12 | 3+ C | 3C | ThreeXInviteAfterOwnSuit | 281 | |
| 1C->1H->2C | 11-12 | any | 2NT | TwoNTAfterOwnSuit | 282 | |
| 1C->1H->2C | 11-12 | 6+ H | **MISSING** | **GAP** | - | Need invitational 3H |
| 1C->1H->2C | 6-10 | 6+ H | 2H | RebidOwnSuitAfterOwnSuit | 192 | |
| 1C->1H->2C | 6-10 | catch-all | Pass | PreferenceAfterOwnSuit | 99 | |
| | | | | | | |
| 1C->1S->2C | 13+ | balanced + stoppers | 3NT | ThreeNTAfterOwnSuit | 352 | |
| 1C->1S->2C | 13+ | **no fit, no stoppers** | **MISSING** | **GAP** | - | |
| 1C->1S->2C | 11-12 | 3+ C | 3C | ThreeXInviteAfterOwnSuit | 281 | |
| 1C->1S->2C | 11-12 | any | 2NT | TwoNTAfterOwnSuit | 282 | |
| 1C->1S->2C | 11-12 | 6+ S | **MISSING** | **GAP** | - | Need invitational 3S |
| 1C->1S->2C | 6-10 | 6+ S | 2S | RebidOwnSuitAfterOwnSuit | 192 | |
| 1C->1S->2C | 6-10 | catch-all | Pass | PreferenceAfterOwnSuit | 99 | |
| | | | | | | |
| 1D->1H->2D | 13+ | balanced + stoppers | 3NT | ThreeNTAfterOwnSuit | 352 | |
| 1D->1H->2D | 13+ | **no fit, no stoppers** | **MISSING** | **GAP** | - | |
| 1D->1H->2D | 11-12 | 3+ D | 3D | ThreeXInviteAfterOwnSuit | 281 | |
| 1D->1H->2D | 11-12 | any | 2NT | TwoNTAfterOwnSuit | 282 | |
| 1D->1H->2D | 11-12 | 6+ H | **MISSING** | **GAP** | - | Need invitational 3H |
| 1D->1H->2D | 6-10 | 6+ H | 2H | RebidOwnSuitAfterOwnSuit | 192 | |
| 1D->1H->2D | 6-10 | catch-all | Pass | PreferenceAfterOwnSuit | 99 | |
| | | | | | | |
| 1D->1S->2D | 13+ | balanced + stoppers | 3NT | ThreeNTAfterOwnSuit | 352 | |
| 1D->1S->2D | 13+ | **no fit, no stoppers** | **MISSING** | **GAP** | - | |
| 1D->1S->2D | 11-12 | 3+ D | 3D | ThreeXInviteAfterOwnSuit | 281 | |
| 1D->1S->2D | 11-12 | any | 2NT | TwoNTAfterOwnSuit | 282 | |
| 1D->1S->2D | 11-12 | 6+ S | **MISSING** | **GAP** | - | Need invitational 3S |
| 1D->1S->2D | 6-10 | 6+ S | 2S | RebidOwnSuitAfterOwnSuit | 192 | |
| 1D->1S->2D | 6-10 | catch-all | Pass | PreferenceAfterOwnSuit | 99 | |
| | | | | | | |
| 1H->1S->2H | 13+ | 3+ H (major) | 4H | FourMAfterOwnSuitMajor | 366 | |
| 1H->1S->2H | 13+ | balanced + stoppers | 3NT | ThreeNTAfterOwnSuit | 352 | |
| 1H->1S->2H | 13+ | **no 3+ H, no stoppers** | **MISSING** | **GAP** | - | |
| 1H->1S->2H | 11-12 | 3+ H | 3H | ThreeXInviteAfterOwnSuit | 281 | |
| 1H->1S->2H | 11-12 | any | 2NT | TwoNTAfterOwnSuit | 282 | |
| 1H->1S->2H | 11-12 | 6+ S | **MISSING** | **GAP** | - | Need invitational 3S |
| 1H->1S->2H | 6-10 | 6+ S | 2S | RebidOwnSuitAfterOwnSuit | 192 | |
| 1H->1S->2H | 6-10 | catch-all | Pass | PreferenceAfterOwnSuit | 99 | |

**Note**: FourMAfterOwnSuitMajor only applies when opening suit is a major (1H->1S->2H). For minor openings, no game-in-opener's-suit rule exists, but that's correct (4C/4D is not game).

---

### F6: After Opener Jump Rebid Own Suit

Applies to: 1C->1D->3C, 1C->1H->3C, 1C->1S->3C, 1D->1H->3D, 1D->1S->3D, 1H->1S->3H

Opener shows 17-18 points with 6+ cards (invitational).

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1C->1D->3C | 8+ | C is minor, no `opening_is_major` | - | - | - | FourMAfterJumpRebid won't fire |
| 1C->1D->3C | 8+ | stoppers in unbid | 3NT | ThreeNTAfterJumpRebid | 337 | |
| 1C->1D->3C | 8+ | no stoppers | **MISSING** | **GAP** | - | Need 5C or catch-all 3NT |
| 1C->1D->3C | 6-7 | catch-all | Pass | PassAfterJumpRebid | 184 | |
| | | | | | | |
| 1C->1H->3C | 8+ | C is minor | - | - | - | FourMAfterJumpRebid won't fire |
| 1C->1H->3C | 8+ | stoppers in unbid | 3NT | ThreeNTAfterJumpRebid | 337 | |
| 1C->1H->3C | 8+ | no stoppers | **MISSING** | **GAP** | - | |
| 1C->1H->3C | 6-7 | catch-all | Pass | PassAfterJumpRebid | 184 | |
| | | | | | | |
| 1C->1S->3C | 8+ | C is minor | - | - | - | FourMAfterJumpRebid won't fire |
| 1C->1S->3C | 8+ | stoppers in unbid | 3NT | ThreeNTAfterJumpRebid | 337 | |
| 1C->1S->3C | 8+ | no stoppers | **MISSING** | **GAP** | - | |
| 1C->1S->3C | 6-7 | catch-all | Pass | PassAfterJumpRebid | 184 | |
| | | | | | | |
| 1D->1H->3D | 8+ | D is minor | - | - | - | FourMAfterJumpRebid won't fire |
| 1D->1H->3D | 8+ | stoppers in unbid | 3NT | ThreeNTAfterJumpRebid | 337 | |
| 1D->1H->3D | 8+ | no stoppers | **MISSING** | **GAP** | - | |
| 1D->1H->3D | 6-7 | catch-all | Pass | PassAfterJumpRebid | 184 | |
| | | | | | | |
| 1D->1S->3D | 8+ | D is minor | - | - | - | FourMAfterJumpRebid won't fire |
| 1D->1S->3D | 8+ | stoppers in unbid | 3NT | ThreeNTAfterJumpRebid | 337 | |
| 1D->1S->3D | 8+ | no stoppers | **MISSING** | **GAP** | - | |
| 1D->1S->3D | 6-7 | catch-all | Pass | PassAfterJumpRebid | 184 | |
| | | | | | | |
| 1H->1S->3H | 8+ | 3+ H, H is major | 4H | FourMAfterJumpRebid | 340 | |
| 1H->1S->3H | 8+ | stoppers in unbid | 3NT | ThreeNTAfterJumpRebid | 337 | |
| 1H->1S->3H | 8+ | no 3+ H, no stoppers | **MISSING** | **GAP** | - | |
| 1H->1S->3H | 6-7 | catch-all | Pass | PassAfterJumpRebid | 184 | |

**F6 gap**: FourMAfterJumpRebid only fires for 1H->1S->3H (the only major opening that gets a 1-level new suit response). All minor openings lack a game bid when stoppers are missing. Recommend a catch-all 3NT without stopper check at lower priority (~335), or 5m bid.

---

### F7: After Opener Bid New Suit (Non-Reverse)

This section covers TWO different rebid types:
- **2-level non-reverse**: opener bids a new suit ranking below their opening suit at the 2-level (e.g., 1H->1S->2C, 1H->1S->2D, 1D->1H->2C, 1D->1S->2C)
- **1-level new suit**: opener bids a new suit at the 1-level (e.g., 1C->1D->1H, 1C->1D->1S, 1C->1H->1S, 1D->1H->1S)

Both match `partner_rebid_new_suit`. The 1-level case has the auction still at the 1-level, which creates unique reresponse options.

**Specific auctions that reach F7:**

| Auction | Rebid level | Suits bid | 4th suit | Notes |
|---------|-------------|-----------|----------|-------|
| 1C->1D->1H | 1 | C,D,H | S | 1-level; can bid 1S |
| 1C->1D->1S | 1 | C,D,S | H | 1-level |
| 1C->1H->1S | 1 | C,H,S | D | 1-level |
| 1D->1H->1S | 1 | D,H,S | C | 1-level |
| 1D->1H->2C | 2 | D,H,C | S | 2-level; standard |
| 1D->1S->2C | 2 | D,S,C | H | 2-level |
| 1H->1S->2C | 2 | H,S,C | D | 2-level |
| 1H->1S->2D | 2 | H,S,D | C | 2-level |

#### F7a: 2-Level Non-Reverse New Suit Rebids

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1D->1H->2C | 13+ | 5+ H (major) | 4H | FourMAfterNewSuit | 371 | |
| 1D->1H->2C | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1D->1H->2C | 13+ | FSF (4th=S, bid 2S) | 2S | FourthSuitForcing | 357 | |
| 1D->1H->2C | 11-12 | 4+ C | 3C | RaiseNewSuitInvite | 292 | |
| 1D->1H->2C | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1D->1H->2C | 11-12 | 6+ H | **MISSING** (no 3H invite) | **GAP** | - | |
| 1D->1H->2C | 6-10 | 3+ D | 2D | PreferenceToOpenerFirst | 196 | |
| 1D->1H->2C | 6-10 | 6+ H | 2H | RebidOwnSuitAfterNewSuit | 194 | |
| 1D->1H->2C | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |
| | | | | | | |
| 1D->1S->2C | 13+ | 5+ S (major) | 4S | FourMAfterNewSuit | 371 | |
| 1D->1S->2C | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1D->1S->2C | 13+ | FSF (4th=H, bid 2H) | 2H | FourthSuitForcing | 357 | |
| 1D->1S->2C | 11-12 | 4+ C | 3C | RaiseNewSuitInvite | 292 | |
| 1D->1S->2C | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1D->1S->2C | 11-12 | 6+ S | **MISSING** | **GAP** | - | |
| 1D->1S->2C | 6-10 | 3+ D | 2D | PreferenceToOpenerFirst | 196 | |
| 1D->1S->2C | 6-10 | 6+ S | 2S | RebidOwnSuitAfterNewSuit | 194 | |
| 1D->1S->2C | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |
| | | | | | | |
| 1H->1S->2C | 13+ | 5+ S (major) | 4S | FourMAfterNewSuit | 371 | |
| 1H->1S->2C | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1H->1S->2C | 13+ | FSF (4th=D, bid 2D) | 2D | FourthSuitForcing | 357 | |
| 1H->1S->2C | 11-12 | 4+ C | 3C | RaiseNewSuitInvite | 292 | |
| 1H->1S->2C | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1H->1S->2C | 11-12 | 6+ S | **MISSING** | **GAP** | - | |
| 1H->1S->2C | 6-10 | 3+ H | 2H | PreferenceToOpenerFirst | 196 | |
| 1H->1S->2C | 6-10 | 6+ S | 2S | RebidOwnSuitAfterNewSuit | 194 | |
| 1H->1S->2C | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |
| | | | | | | |
| 1H->1S->2D | 13+ | 5+ S (major) | 4S | FourMAfterNewSuit | 371 | |
| 1H->1S->2D | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1H->1S->2D | 13+ | FSF (4th=C, bid 3C) | 3C | FourthSuitForcing | 357 | Note: 3-level FSF |
| 1H->1S->2D | 11-12 | 4+ D | 3D | RaiseNewSuitInvite | 292 | |
| 1H->1S->2D | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1H->1S->2D | 11-12 | 6+ S | **MISSING** | **GAP** | - | |
| 1H->1S->2D | 6-10 | 3+ H | 2H | PreferenceToOpenerFirst | 196 | |
| 1H->1S->2D | 6-10 | 6+ S | 2S | RebidOwnSuitAfterNewSuit | 194 | |
| 1H->1S->2D | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |

#### F7b: 1-Level New Suit Rebids (SIGNIFICANT GAPS)

These auctions have the bidding at the 1-level, allowing cheap exploration.
The F7 rules were designed for 2-level rebids and miss several standard bid types.

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| **1C->1D->1H** | | | | | | 4th suit = S |
| 1C->1D->1H | 6+ | 4+ S | 1S | **MISSING** | **GAP** | Natural, forcing, up-the-line |
| 1C->1D->1H | 13+ | 5+ D (minor, not major) | **MISSING** | **GAP** | No 4M for minor; need 3NT or 3D GF |
| 1C->1D->1H | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1C->1D->1H | 13+ | FSF (4th=S, bid **1S**) | 1S | FourthSuitForcing | 357 | **BUG**: 1S is natural, not FSF |
| 1C->1D->1H | 11-12 | 4+ H | 2H | RaiseNewSuitInvite | 292 | Wait -- RaiseNewSuitInvite bids 3H (cheapest + 1)? No: it bids cheapest_bid_in_suit(H, rebid=1H) = 2H. So it raises to 2H. But 2H at 11-12 is invitational? In the code, RaiseNewSuitInvite bids cheapest in z after rebid. After 1H rebid, cheapest H is 2H. So 2H. But the rule explanation says "invitational raise". A simple raise to 2H is competitive, not invitational. The JUMP to 3H would be invitational. **This may be an accuracy issue for 1-level rebids.** |
| 1C->1D->1H | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1C->1D->1H | 6-10 | 4+ H | **MISSING** | **GAP** | Need simple raise 2H |
| 1C->1D->1H | 6-10 | balanced, no fit | **MISSING** | **GAP** | Need 1NT reresponse |
| 1C->1D->1H | 6-10 | 3+ C | 2C | PreferenceToOpenerFirst | 196 | |
| 1C->1D->1H | 6-10 | 6+ D | 2D | RebidOwnSuitAfterNewSuit | 194 | |
| 1C->1D->1H | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |
| | | | | | | |
| **1C->1D->1S** | | | | | | 4th suit = H |
| 1C->1D->1S | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1C->1D->1S | 13+ | FSF (4th=H, bid 2H) | 2H | FourthSuitForcing | 357 | Level 2, OK |
| 1C->1D->1S | 11-12 | 4+ S | 2S | RaiseNewSuitInvite | 292 | Same accuracy concern: 2S = simple raise, not invitational jump |
| 1C->1D->1S | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1C->1D->1S | 6-10 | 4+ S | **MISSING** | **GAP** | Need simple raise 2S (same bid as 11-12 but different meaning) |
| 1C->1D->1S | 6-10 | 4+ H (new suit) | **MISSING** | **GAP** | Natural 2H, forcing |
| 1C->1D->1S | 6-10 | balanced, no fit | **MISSING** | **GAP** | Need 1NT reresponse |
| 1C->1D->1S | 6-10 | 3+ C | 2C | PreferenceToOpenerFirst | 196 | |
| 1C->1D->1S | 6-10 | 6+ D | 2D | RebidOwnSuitAfterNewSuit | 194 | |
| 1C->1D->1S | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |
| | | | | | | |
| **1C->1H->1S** | | | | | | 4th suit = D |
| 1C->1H->1S | 13+ | 5+ H (major) | 4H | FourMAfterNewSuit | 371 | |
| 1C->1H->1S | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1C->1H->1S | 13+ | FSF (4th=D, bid 2D) | 2D | FourthSuitForcing | 357 | Level 2, OK |
| 1C->1H->1S | 11-12 | 4+ S | 2S | RaiseNewSuitInvite | 292 | Same accuracy concern |
| 1C->1H->1S | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1C->1H->1S | 6-10 | 4+ S | **MISSING** | **GAP** | Need simple raise 2S |
| 1C->1H->1S | 6-10 | balanced, no fit | **MISSING** | **GAP** | Need 1NT reresponse |
| 1C->1H->1S | 6-10 | 3+ C | 2C | PreferenceToOpenerFirst | 196 | |
| 1C->1H->1S | 6-10 | 6+ H | 2H | RebidOwnSuitAfterNewSuit | 194 | |
| 1C->1H->1S | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |
| | | | | | | |
| **1D->1H->1S** | | | | | | 4th suit = C |
| 1D->1H->1S | 13+ | 5+ H (major) | 4H | FourMAfterNewSuit | 371 | |
| 1D->1H->1S | 13+ | balanced + stoppers | 3NT | ThreeNTAfterNewSuit | 361 | |
| 1D->1H->1S | 13+ | FSF (4th=C, bid 2C) | 2C | FourthSuitForcing | 357 | Level 2, OK |
| 1D->1H->1S | 11-12 | 4+ S | 2S | RaiseNewSuitInvite | 292 | Same accuracy concern |
| 1D->1H->1S | 11-12 | any | 2NT | TwoNTAfterNewSuit | 283 | |
| 1D->1H->1S | 6-10 | 4+ S | **MISSING** | **GAP** | Need simple raise 2S |
| 1D->1H->1S | 6-10 | balanced, no fit | **MISSING** | **GAP** | Need 1NT reresponse |
| 1D->1H->1S | 6-10 | 3+ D | 2D | PreferenceToOpenerFirst | 196 | |
| 1D->1H->1S | 6-10 | 6+ H | 2H | RebidOwnSuitAfterNewSuit | 194 | |
| 1D->1H->1S | 6-10 | catch-all | Pass | PassAfterNewSuit | 96 | |

**F7 accuracy concern for 1-level rebids**: `RaiseNewSuitInvite` bids cheapest_bid_in_suit(z, rebid). After a 1-level rebid like 1H, cheapest in H is 2H. The rule produces a SIMPLE RAISE (2H), not a JUMP RAISE (3H). At 11-12 HCP, an invitational raise should be a jump (3H), not a simple raise (2H). The 6-10 simple raise (2H) and 11-12 invitational raise (3H) should be distinct bids but currently they produce the same bid (2H).

**F7 key gaps for 1-level rebids**:
1. **NewSuitAt1Level**: 6+ HCP, 4+ card suit biddable at 1-level above the rebid. Natural, forcing. Only possible after 1C->1D->1H (bid 1S). Priority ~262.
2. **WeakRaiseNewSuit**: 6-10 HCP, 4+ support for z, raise to cheapest. Priority ~200.
3. **OneNTReresponse**: 6-10 HCP, balanced, no fit, no new suit at 1-level. Priority ~100.
4. **Fix RaiseNewSuitInvite for 1-level**: At 11-12, the invitational raise should JUMP one level above cheapest. Currently bids cheapest (which is correct for 2-level rebids where cheapest IS a jump, but wrong for 1-level rebids).

---

### F8: After Opener Reversed

True reverses only occur in these auctions (where new suit > opening suit AND bid is at cheapest level):
- 1C->1H->2D (D>C, cheapest D after 1H = 2D)
- 1C->1S->2D (D>C, cheapest D after 1S = 2D)
- 1C->1S->2H (H>C, cheapest H after 1S = 2H)
- 1D->1S->2H (H>D, cheapest H after 1S = 2H)

Reverses do NOT occur after: 1C->1D (all suits available at 1-level), 1D->1H (S available at 1-level), 1H->1S (no suit > H except S = response).

Opener shows 17+ points, forcing one round. Responder MUST bid.

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| **1C->1H->2D** | | | | | | Reverse suit = D |
| 1C->1H->2D | 13+ | balanced + stoppers | 3NT | ThreeNTAfterReverse | 368 | |
| 1C->1H->2D | 13+ | 4+ D | 3D | RaiseReverseSuit | 297 | **Accuracy**: should be GF, not invite |
| 1C->1H->2D | 13+ | no fit, no stoppers | **MISSING** | **GAP** | - | Need GF new suit or cuebid |
| 1C->1H->2D | 10-12 | 4+ D | 3D | RaiseReverseSuit | 297 | Invitational raise |
| 1C->1H->2D | 10-12 | 6+ H | 3H | JumpInOwnSuitAfterReverse | 295 | |
| 1C->1H->2D | 10-12 | any | 2NT | TwoNTAfterReverse | 290 | |
| 1C->1H->2D | 6-9 | 3+ C | 3C | PreferenceAfterReverse | 199 | |
| 1C->1H->2D | 6-9 | catch-all | 2H | RebidOwnSuitAfterReverse | 198 | |
| | | | | | | |
| **1C->1S->2D** | | | | | | Reverse suit = D |
| 1C->1S->2D | 13+ | balanced + stoppers | 3NT | ThreeNTAfterReverse | 368 | |
| 1C->1S->2D | 13+ | 4+ D | 3D | RaiseReverseSuit | 297 | **Accuracy**: should be GF |
| 1C->1S->2D | 13+ | no fit, no stoppers | **MISSING** | **GAP** | - | |
| 1C->1S->2D | 10-12 | 4+ D | 3D | RaiseReverseSuit | 297 | |
| 1C->1S->2D | 10-12 | 6+ S | 3S | JumpInOwnSuitAfterReverse | 295 | |
| 1C->1S->2D | 10-12 | any | 2NT | TwoNTAfterReverse | 290 | |
| 1C->1S->2D | 6-9 | 3+ C | 3C | PreferenceAfterReverse | 199 | |
| 1C->1S->2D | 6-9 | catch-all | 2S | RebidOwnSuitAfterReverse | 198 | |
| | | | | | | |
| **1C->1S->2H** | | | | | | Reverse suit = H |
| 1C->1S->2H | 13+ | balanced + stoppers | 3NT | ThreeNTAfterReverse | 368 | |
| 1C->1S->2H | 13+ | 4+ H | 3H | RaiseReverseSuit | 297 | **Accuracy**: should be GF |
| 1C->1S->2H | 13+ | no fit, no stoppers | **MISSING** | **GAP** | - | |
| 1C->1S->2H | 10-12 | 4+ H | 3H | RaiseReverseSuit | 297 | |
| 1C->1S->2H | 10-12 | 6+ S | 3S | JumpInOwnSuitAfterReverse | 295 | |
| 1C->1S->2H | 10-12 | any | 2NT | TwoNTAfterReverse | 290 | |
| 1C->1S->2H | 6-9 | 3+ C | 3C | PreferenceAfterReverse | 199 | |
| 1C->1S->2H | 6-9 | catch-all | 2S | RebidOwnSuitAfterReverse | 198 | |
| | | | | | | |
| **1D->1S->2H** | | | | | | Reverse suit = H |
| 1D->1S->2H | 13+ | balanced + stoppers | 3NT | ThreeNTAfterReverse | 368 | |
| 1D->1S->2H | 13+ | 4+ H | 3H | RaiseReverseSuit | 297 | **Accuracy**: should be GF |
| 1D->1S->2H | 13+ | no fit, no stoppers | **MISSING** | **GAP** | - | |
| 1D->1S->2H | 10-12 | 4+ H | 3H | RaiseReverseSuit | 297 | |
| 1D->1S->2H | 10-12 | 6+ S | 3S | JumpInOwnSuitAfterReverse | 295 | |
| 1D->1S->2H | 10-12 | any | 2NT | TwoNTAfterReverse | 290 | |
| 1D->1S->2H | 6-9 | 3+ D | 3D | PreferenceAfterReverse | 199 | |
| 1D->1S->2H | 6-9 | catch-all | 2S | RebidOwnSuitAfterReverse | 198 | |

**F8 accuracy**: RaiseReverseSuit has HcpRange(min_hcp=10) with no max. With 13+ HCP after a reverse (17+), combined 30+ -- this should be a GF raise, not invitational. Fix: cap RaiseReverseSuit at max_hcp=12, add GF raise at 13+.

**F8 gap**: 13+ HCP without balanced/stoppers and without 4+ in reverse suit has no rule. Need a forcing new-suit bid or game-in-major bid.

---

### F9: After Opener Jump Shifted

Jump shifts by opener (19-21 points, 4+ cards in new suit). Game forcing -- responder cooperates regardless of HCP.

**Specific auctions:**

| Auction | Jump shift suit | cheapest_bid was | Notes |
|---------|---------------|------------------|-------|
| 1C->1D->2H | H | 1H | Jump to 2H |
| 1C->1D->2S | S | 1S | Jump to 2S |
| 1C->1H->2S | S | 1S | Jump to 2S |
| 1C->1H->3D | D | 2D | Jump to 3D |
| 1C->1S->3D | D | 2D | Jump to 3D |
| 1C->1S->3H | H | 2H | Jump to 3H |
| 1D->1H->2S | S | 1S | Jump to 2S |
| 1D->1H->3C | C | 2C | Jump to 3C |
| 1D->1S->3C | C | 2C | Jump to 3C |
| 1D->1S->3H | H | 2H | Jump to 3H |
| 1H->1S->3C | C | 2C | Jump to 3C |
| 1H->1S->3D | D | 2D | Jump to 3D |

All are game-forcing. Responder describes hand; no HCP checks needed.

| Auction(s) | Conditions | Reresponse | Rule | Pri |
|------------|------------|------------|------|-----|
| All F9 auctions | 4+ in jump-shift suit | raise z (cheapest) | RaiseJumpShiftSuit | 444 |
| All F9 auctions | 3+ in opening suit x | support x (cheapest) | SupportOpenerFirstAfterJS | 379 |
| All F9 auctions | 6+ in own suit y | rebid y (cheapest) | RebidOwnSuitAfterJS | 378 |
| All F9 auctions | catch-all | 3NT | ThreeNTAfterJumpShift | 375 |

**Specific reresponse bids by auction:**

| Auction | Raise z | Support x | Rebid y | 3NT |
|---------|---------|-----------|---------|-----|
| 1C->1D->2H (z=H) | 3H | 2C->err? cheapest C above 2H = 3C | 2D->err? cheapest D above 2H = 3D | 3NT |
| 1C->1D->2S (z=S) | 3S | cheapest C above 2S = 3C | cheapest D above 2S = 3D | 3NT |
| 1C->1H->2S (z=S) | 3S | cheapest C above 2S = 3C | cheapest H above 2S = 3H | 3NT |
| 1C->1H->3D (z=D) | 4D | cheapest C above 3D = 4C | cheapest H above 3D = 3H | 3NT |
| 1C->1S->3D (z=D) | 4D | cheapest C above 3D = 4C | cheapest S above 3D = 3S | 3NT |
| 1C->1S->3H (z=H) | 4H | cheapest C above 3H = 4C | cheapest S above 3H = 3S | 3NT |
| 1D->1H->2S (z=S) | 3S | cheapest D above 2S = 3D | cheapest H above 2S = 3H | 3NT |
| 1D->1H->3C (z=C) | 4C | cheapest D above 3C = 3D | cheapest H above 3C = 3H | 3NT |
| 1D->1S->3C (z=C) | 4C | cheapest D above 3C = 3D | cheapest S above 3C = 3S | 3NT |
| 1D->1S->3H (z=H) | 4H | cheapest D above 3H = 4D | cheapest S above 3H = 3S | 3NT |
| 1H->1S->3C (z=C) | 4C | cheapest H above 3C = 3H | cheapest S above 3C = 3S | 3NT |
| 1H->1S->3D (z=D) | 4D | cheapest H above 3D = 3H | cheapest S above 3D = 3S | 3NT |

F9 is fully covered. No gaps.

---

### F10: After Opener Bid 2NT

Applies to: 1C->1D->2NT, 1C->1H->2NT, 1C->1S->2NT, 1D->1H->2NT, 1D->1S->2NT, 1H->1S->2NT

Opener shows 18-19 HCP balanced (jump to 2NT). Game forcing with 8+ HCP (combined 26+).

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1C->1D->2NT | 8+ | 6+ D (minor) | **3NT fires first** | ThreeNTAfter2NTRebid | 339 | FourM needs major |
| 1C->1D->2NT | 8+ | 5+ D | 3D | ThreeSuitAfter2NTRebid | 334 | **DEAD**: 3NT at 339 fires first |
| 1C->1D->2NT | 8+ | any | 3NT | ThreeNTAfter2NTRebid | 339 | |
| 1C->1D->2NT | 6-7 | catch-all | Pass | PassAfter2NTRebid | 185 | |
| | | | | | | |
| 1C->1H->2NT | 8+ | 6+ H (major) | 4H | FourMAfter2NTRebid | 343 | |
| 1C->1H->2NT | 8+ | 5+ H | 3H | ThreeSuitAfter2NTRebid | 334 | **DEAD** |
| 1C->1H->2NT | 8+ | any | 3NT | ThreeNTAfter2NTRebid | 339 | |
| 1C->1H->2NT | 6-7 | catch-all | Pass | PassAfter2NTRebid | 185 | |
| | | | | | | |
| 1C->1S->2NT | 8+ | 6+ S (major) | 4S | FourMAfter2NTRebid | 343 | |
| 1C->1S->2NT | 8+ | 5+ S | 3S | ThreeSuitAfter2NTRebid | 334 | **DEAD** |
| 1C->1S->2NT | 8+ | any | 3NT | ThreeNTAfter2NTRebid | 339 | |
| 1C->1S->2NT | 6-7 | catch-all | Pass | PassAfter2NTRebid | 185 | |
| | | | | | | |
| 1D->1H->2NT | 8+ | 6+ H (major) | 4H | FourMAfter2NTRebid | 343 | |
| 1D->1H->2NT | 8+ | 5+ H | 3H | ThreeSuitAfter2NTRebid | 334 | **DEAD** |
| 1D->1H->2NT | 8+ | any | 3NT | ThreeNTAfter2NTRebid | 339 | |
| 1D->1H->2NT | 6-7 | catch-all | Pass | PassAfter2NTRebid | 185 | |
| | | | | | | |
| 1D->1S->2NT | 8+ | 6+ S (major) | 4S | FourMAfter2NTRebid | 343 | |
| 1D->1S->2NT | 8+ | 5+ S | 3S | ThreeSuitAfter2NTRebid | 334 | **DEAD** |
| 1D->1S->2NT | 8+ | any | 3NT | ThreeNTAfter2NTRebid | 339 | |
| 1D->1S->2NT | 6-7 | catch-all | Pass | PassAfter2NTRebid | 185 | |
| | | | | | | |
| 1H->1S->2NT | 8+ | 6+ S (major) | 4S | FourMAfter2NTRebid | 343 | |
| 1H->1S->2NT | 8+ | 5+ S | 3S | ThreeSuitAfter2NTRebid | 334 | **DEAD** |
| 1H->1S->2NT | 8+ | any | 3NT | ThreeNTAfter2NTRebid | 339 | |
| 1H->1S->2NT | 6-7 | catch-all | Pass | PassAfter2NTRebid | 185 | |

**F10 priority fix**: ThreeSuitAfter2NTRebid (334) is dead code -- ThreeNTAfter2NTRebid (339) always fires first. For major response suits, 3M is more descriptive (lets opener choose 3NT vs 4M). Fix: give ThreeSuitAfter2NTRebid higher priority (~341) when response is a major, or restrict ThreeNTAfter2NTRebid to hands without a 5+ card major.

---

### F11: After Opener Bid 3NT

Applies to: 1C->1D->3NT, 1C->1H->3NT, 1C->1S->3NT, 1D->1H->3NT, 1D->1S->3NT, 1H->1S->3NT

Opener shows 19-21 HCP balanced. Game reached.

| Auction | HCP | Conditions | Reresponse | Rule | Pri |
|---------|-----|------------|------------|------|-----|
| All 6 auctions | any | catch-all | Pass | PassAfter3NTRebid | 90 |

Fully covered. (Slam exploration with 13+ HCP is future work.)

---

### MISSING SECTION: After Opener Double-Jump Rebid Own Suit

Applies to: 1C->*->4C, 1D->*->4D, 1H->1S->4H

Opener shows 19-21 points with self-supporting 6+ card suit. For majors, game is reached.

**Specific auctions:**

| Auction | Game reached? | Notes |
|---------|--------------|-------|
| 1C->1D->4C | No (5C = game) | Rare; may need 5C with extras |
| 1C->1H->4C | No | Rare |
| 1C->1S->4C | No | Rare |
| 1D->1H->4D | No (5D = game) | Rare |
| 1D->1S->4D | No | Rare |
| 1H->1S->4H | **Yes** (4H = game) | Most common case |

| Auction | HCP | Conditions | Reresponse | Rule | Pri | Notes |
|---------|-----|------------|------------|------|-----|-------|
| 1H->1S->4H | any | game reached | Pass | **MISSING** | **GAP** | Need PassAfterGameInOwnSuit |
| 1C->1D->4C | any | 4C not game | Pass or 5C | **MISSING** | **GAP** | Pass is pragmatic |
| 1C->1H->4C | any | 4C not game | Pass or 5C | **MISSING** | **GAP** | |
| 1C->1S->4C | any | 4C not game | Pass or 5C | **MISSING** | **GAP** | |
| 1D->1H->4D | any | 4D not game | Pass or 5D | **MISSING** | **GAP** | |
| 1D->1S->4D | any | 4D not game | Pass or 5D | **MISSING** | **GAP** | |

**Fix**: Add guard `_partner_double_jump_rebid_own_suit` and `PassAfterGameInOwnSuit` rule. For simplicity, pass on all (opener bid aggressively; 5m is rarely right). Can add 5m rule later for 10+ HCP with 3+ support after a minor double-jump.

---

## Summary of All Needed Changes

### Bug Fixes (2)

| # | Bug | Location | Fix |
|---|-----|----------|-----|
| B1 | `_partner_reversed` matches jump shifts | new_suit.py:110, helpers.py:117 | Add `cheapest_bid_in_suit` check: `rebid.level == cheapest.level` |
| B2 | FSF at 1-level (1C->1D->1H->1S) | helpers.py `find_fourth_suit_bid` | Add `bid.level >= 2` check |

### Priority Fixes (2)

| # | Issue | Current | Fix |
|---|-------|---------|-----|
| P1 | TwoNTAfter1NTRebid > JumpRebidAfter1NT | 286 > 280 | Swap: jump rebid ~288, 2NT ~278 |
| P2 | ThreeNTAfter2NTRebid kills ThreeSuitAfter2NTRebid | 339 > 334 | Give ThreeSuit ~341 (at least for majors) |

### Accuracy Fixes (2)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| A1 | Accept3yJumpRaise3NT no stopper check | Accept3yJumpRaise3NT | Add `stoppers_in_unbid` condition |
| A2 | RaiseReverseSuit no max HCP | RaiseReverseSuit | Cap at max_hcp=12 |

### New Guards Needed (2)

| # | Guard | Definition |
|---|-------|------------|
| G1 | `_partner_double_jump_rebid_own_suit` | `rebid.suit == opening.suit and rebid.level == cheapest.level + 2` |
| G2 | `_partner_rebid_new_suit_1_level` | `partner_rebid_new_suit AND rebid.level == 1` (optional, for distinguishing 1-level from 2-level) |

### New Rules Needed (12)

| # | Rule name | Section | HCP | Conditions | Bid | Priority |
|---|-----------|---------|-----|------------|-----|----------|
| R1 | `PassAfterGameInOwnSuit` | New (F12) | any | `_partner_double_jump_rebid_own_suit` | Pass | ~88 |
| R2 | `NewSuitAt1Level` | F7b | 6+ | 4+ card suit biddable at 1-level above rebid; `partner_rebid_new_suit` level==1 | 1-level suit | ~262 |
| R3 | `WeakRaiseNewSuit` | F7 | 6-10 | 4+ support for z | cheapest z | ~200 |
| R4 | `OneNTReresponse` | F7b | 6-10 | balanced, no fit, no new suit; `partner_rebid_new_suit` level==1 | 1NT | ~100 |
| R5 | `JumpRebidOwnSuitAfterOwnSuit` | F5 | 11-12 | 6+ in y | jump y (3y) | ~284 |
| R6 | `JumpRebidOwnSuitAfterNewSuit` | F7 | 11-12 | 6+ in y | jump y (3y) | ~289 |
| R7 | `NewSuitForcingAfterOwnSuit` | F5 | 13+ | 4+ in new suit, no FSF available | cheapest new suit | ~348 |
| R8 | `GFRaiseReverseSuit` | F8 | 13+ | 4+ in reverse suit | game in z or 4z | ~365 |
| R9 | `GFAfterReverse` | F8 | 13+ | no fit, no balanced/stoppers | new suit or 3NT | ~360 |
| R10 | `ThreeNTAfterJumpRebidNoStoppers` | F6 | 8+ | catch-all (no stoppers) | 3NT | ~335 |
| R11 | `GFMinorNoStoppers` | F2 | 13+ | minor raised, no stoppers | new suit forcing or 5m | ~355 |
| R12 | `InviteJumpRaiseNewSuit` | F7b | 11-12 | 4+ z, after 1-level rebid | jump raise z (3z) | ~293 |

### RaiseNewSuitInvite Accuracy Fix for 1-Level Rebids

`RaiseNewSuitInvite` bids `cheapest_bid_in_suit(z, rebid)`. After a 2-level rebid (e.g., 1H->1S->2C), cheapest in C above 2C is 3C -- correct invitational jump. But after a 1-level rebid (e.g., 1C->1D->1H), cheapest in H above 1H is 2H -- a SIMPLE raise, not invitational.

**Fix options**:
1. Make RaiseNewSuitInvite explicitly bid `cheapest + 1` level (a jump), not just cheapest.
2. Add a separate `WeakRaiseNewSuit` for 6-10 at cheapest level, and ensure `RaiseNewSuitInvite` always jumps one level above cheapest.
3. Add guard `_partner_rebid_new_suit_2_level` to RaiseNewSuitInvite, and handle 1-level with separate R12 (`InviteJumpRaiseNewSuit`).
