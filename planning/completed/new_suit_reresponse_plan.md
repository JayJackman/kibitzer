# Implementation Plan: new_suit.py Fixes & Additions

Based on [new_suit_reresponse_audit.md](new_suit_reresponse_audit.md).

## Phase 1: Bug Fixes (B1, B2) --- DONE
- [x] **B1**: Fix `_partner_reversed` in `new_suit.py` and `helpers.py` — add cheapest-level check
- [x] **B2**: Fix `find_fourth_suit_bid` in `helpers.py` — add `level >= 2` check

## Phase 2: Priority Fixes (P1, P2) --- DONE
- [x] **P1**: Swap `TwoNTAfter1NTRebid` (286->278) and `JumpRebidAfter1NT` (280->288) priorities
- [x] **P2**: Fix `ThreeSuitAfter2NTRebid` (334->341) + restrict to majors + raise above `ThreeNTAfter2NTRebid` (339)

## Phase 3: Accuracy Fixes (A1, A2) --- DONE
- [x] **A1**: Add `stoppers_in_unbid` to `Accept3yJumpRaise3NT`
- [x] **A2**: Cap `RaiseReverseSuit` at `max_hcp=12` (invitational only)

## Phase 4: New Section F12 — Double-Jump Rebid Own Suit (G1, R1) --- DONE
- [x] **G1**: Add `_partner_double_jump_rebid_own_suit` guard
- [x] **R1**: Add `PassAfterDoubleJumpRebid` rule

## Phase 5: F7b — 1-Level Rebid Gaps (R2, R3, R4, R12 + fix) --- DONE
- [x] **R2**: `NewSuitAt1Level` (6+ HCP, 4+ cards biddable at 1-level, pri 262)
- [x] **R3**: `WeakRaiseNewSuit` (6-10, 4+ support for z, pri 200)
- [x] **R4**: `OneNTReresponse` (6-10, balanced, pri 100)
- [x] **R12+fix**: Fixed `RaiseNewSuitInvite` to jump one level for 1-level rebids (no separate rule needed)
- [x] Added `_partner_rebid_new_suit_1_level` guard and `_find_new_suit_at_1_level` helper

## Phase 6: F5 Gaps — After Own Suit Rebid (R5, R7) --- DONE
- [x] **R5**: `JumpRebidOwnSuitAfterOwnSuit` (11-12, 6+ own suit -> 3y, pri 284)
- [x] **R7**: `NewSuitForcingAfterOwnSuit` (13+, 4+ new suit via `find_new_suit_forcing`, pri 348)

## Phase 7: Remaining Gaps (R6, R10, R11) --- DONE
- [x] **R6**: `JumpRebidOwnSuitAfterNewSuit` (11-12, 6+ own suit -> 3y, pri 289)
- [x] **R10**: `ThreeNTAfterJumpRebidNoStoppers` (F6, catch-all 3NT, pri 335)
- [x] **R11**: `NewSuitForcingAfterMinorRaise` (F2, minor raised 13+ no stoppers, pri 355)

## Phase 8: F8 Gaps — After Reverse (R8, R9) --- DONE
- [x] **R8**: `GFRaiseReverseSuit` (13+, 4+ reverse suit -> 4M major / 3NT minor, pri 372)
- [x] **R9**: `GFAfterReverse` (13+, catch-all -> new suit forcing or 3NT, pri 360)
