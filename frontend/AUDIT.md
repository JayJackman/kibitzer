# Frontend Audit Report

Thorough review of all 24 TypeScript/TSX files (~3,660 lines) in `frontend/src/`.

---

## File Size Summary

| File | Lines | Verdict |
|------|------:|---------|
| `pages/Practice.tsx` | 778 | Too large -- should be split |
| `App.tsx` | 354 | Acceptable (routing config) |
| `hooks/useBidKeyboard.ts` | 250 | Acceptable (self-contained hook) |
| `components/auction/AuctionGrid.tsx` | 232 | Acceptable |
| `components/auction/BidControls.tsx` | 227 | Acceptable |
| `pages/Lobby.tsx` | 226 | Acceptable |
| `api/endpoints.ts` | 210 | Acceptable |
| `api/types.ts` | 172 | Acceptable |
| `components/advice/AdvicePanel.tsx` | 160 | Acceptable |
| `api/client.ts` | 114 | Acceptable |
| Everything else | <110 | Fine |

---

## 1. Duplicated Code

### 1a. Bid formatting logic (3 copies)

The same "convert bid string to suit symbol with color" logic exists in three places:

- **`AdvicePanel.tsx:35-44`** -- `formatBid()` function returns `{ text, color }`
- **`AuctionGrid.tsx:72-102`** -- `BidCell` component does the same inline
- **`Practice.tsx:638-648`** -- `ContractSuit` component does the suit-symbol-with-color part

All three take a bid/suit string, check the last character for S/H/D/C, and render the Unicode symbol in the suit's color. This should be a single shared utility or component.

**Recommendation:** Create a `formatBid(bid: string): { text: string; color: string | null }` utility in `lib/constants.ts` (or a new `lib/bridge.ts`), and a `<BidText bid="1S" />` component in `components/ui/` that handles the rendering. All three call sites can then use the same code.

### 1b. Seat arrays defined 3 times

The exact same array `["N", "E", "S", "W"]` appears under three names:

- `Practice.tsx:655` -- `ALL_SEATS`
- `Lobby.tsx:29` -- `SEATS`
- `AuctionGrid.tsx:20` -- `SEAT_ORDER`

**Recommendation:** Add `ALL_SEATS` to `lib/constants.ts` alongside `SEAT_LABELS`, and import from there.

### 1c. Action error handling (App.tsx)

`loginAction`, `registerAction`, and `joinByCodeAction` all have nearly identical catch blocks:

```ts
if (err instanceof AxiosError && err.response?.data?.detail) {
  return { error: err.response.data.detail as string };
}
return { error: "Something went wrong. Please try again." };
```

**Recommendation:** Extract a small helper:

```ts
function actionError(err: unknown): { error: string } {
  if (err instanceof AxiosError && err.response?.data?.detail) {
    return { error: err.response.data.detail as string };
  }
  return { error: "Something went wrong. Please try again." };
}
```

This is a minor DRY improvement (saves ~6 lines x3), but it also centralizes the error message wording.

---

## 2. Reusable Components / Extraction Opportunities

### 2a. Practice.tsx needs to be broken up (778 lines)

`Practice.tsx` defines **9 components** and **7 helper functions/constants** all in one file. Most of these are only used within Practice, but several are substantial enough to warrant extraction:

| Component/Block | Lines | Recommendation |
|-----------------|------:|----------------|
| `HandEntryForm` + rank parsing helpers | ~155 | Extract to `components/hand/HandEntryForm.tsx` |
| `AuctionHistory` | ~60 | Extract to `components/auction/AuctionHistory.tsx` |
| `AuctionComplete` + `ContractDisplay` + `ContractSuit` | ~95 | Extract to `components/auction/AuctionComplete.tsx` |
| `JoinPanel` | ~50 | Extract to `components/session/JoinPanel.tsx` |
| `SessionHeader` | ~57 | Extract to `components/session/SessionHeader.tsx` |
| `countHcp`, `EMPTY_HAND`, `DECLARER_ARROW` | ~15 | Move to `lib/bridge.ts` or keep with `AuctionComplete` |

After extraction, `Practice.tsx` would shrink to ~250 lines (just `PracticePage` + `PracticeView`), making it much easier to navigate and maintain.

### 2b. SeatPicker (Lobby.tsx:176-198)

`SeatPicker` is defined inside Lobby but is generic enough to reuse elsewhere (e.g., if the JoinPanel ever gets a seat preference picker). It's a clean, self-contained toggle button group.

**Recommendation:** Move to `components/ui/SeatPicker.tsx`. Low priority -- it's only used in Lobby today.

---

## 3. Code Smells

### 3a. Dead constant: `showSessionHeader = true`

**File:** `Practice.tsx:169`

```tsx
const showSessionHeader = true;
// ...
{showSessionHeader && <SessionHeader ... />}
```

This was likely a conditional at some point but is now always `true`. The variable adds indirection for no reason.

**Fix:** Remove the variable and the conditional -- just render `<SessionHeader>` directly.

### 3b. Dead code in ThoughtProcess.tsx

**File:** `ThoughtProcess.tsx:42`

```tsx
!step.passed && "opacity-50",
```

This condition can never be true. The caller in `AdvicePanel.tsx:138` pre-filters to only passed steps:

```tsx
<ThoughtProcess steps={advice.thought_process.steps.filter((s) => s.passed)} />
```

So every `step.passed` is always `true`, and the opacity class never applies.

**Fix:** Either remove the dead opacity logic from `ThoughtProcess`, or stop pre-filtering in `AdvicePanel` and let `ThoughtProcess` handle the visual distinction itself (showing all rules, dimming the failing ones). The latter might actually be more useful for the user -- they'd see which rules *almost* matched.

### 3c. HCP calculation duplicates backend logic

**File:** `Practice.tsx:70-78`

```tsx
const HCP_VALUES: Record<string, number> = { A: 4, K: 3, Q: 2, J: 1 };
function countHcp(hand: Hand): number { ... }
```

This manually counts HCP from rank strings. It's used only in `AuctionComplete.titleFor()` to show HCP next to each seat label in the 4-hand compass display.

The backend already computes `hand_evaluation.hcp` for the player's hand. For the all-hands display, individual evaluations aren't sent, so the frontend recalculates.

**Recommendation:** This works but is fragile -- if HCP calculation ever changes on the backend, the frontend copy would drift. Consider either:
- Having the API include evaluations for all 4 hands in the `all_hands` response, or
- Accepting the duplication with a comment noting it mirrors the backend

### 3d. AppLayout links to wrong route

**File:** `AppLayout.tsx:37`

```tsx
<Link to="/lobby" className="text-2xl font-bold hover:opacity-80">
  Kibitzer
</Link>
```

The lobby route is at `/`, not `/lobby`. The catch-all route (`path: "*"`) redirects unknown paths to `/`, so this works by accident, but it triggers an unnecessary redirect.

**Fix:** Change `to="/lobby"` to `to="/"`.

### 3e. `legalBidsKey` pattern repeated

Both `Practice.tsx:157` and `useBidKeyboard.ts:124` independently compute `legalBids.join(",")` as a stable key for `useEffect` dependencies. This is minor and pragmatic -- not worth abstracting -- but worth noting that both places need to stay in sync if the serialization ever changes.

---

## 4. Outdated Comments

### 4a. client.ts references deleted ProtectedRoute

**File:** `client.ts:99-103`

```ts
// We don't redirect here; React's ProtectedRoute component
// handles the redirect to /login when user is null.
```

`ProtectedRoute` was replaced by the `protectedLoader` pattern in `App.tsx`. The comment should say:

```ts
// We don't redirect here; the protectedLoader in App.tsx
// handles the redirect to /login on 401.
```

### 4b. ThoughtProcess.tsx docstring is misleading

**File:** `ThoughtProcess.tsx:6-7`

> "The winning rule (the one that produced the recommended bid) is shown prominently; other rules are muted."

But `ThoughtProcess` only receives pre-filtered steps (all with `passed === true`), so there are no "other rules" to mute. The comment describes behavior that was either removed or never implemented here.

**Fix:** Update to: "Each step is a rule that matched, with a list of conditions. All steps shown here passed the engine's evaluation."

---

## 5. Summary of Recommended Actions

### High impact (do first)
1. **Split Practice.tsx** -- Extract `HandEntryForm`, `AuctionHistory`, `AuctionComplete`, `JoinPanel`, `SessionHeader` into separate files. Reduces Practice.tsx from 778 to ~250 lines.
2. **Unify bid formatting** -- Create shared `formatBid()` utility + `<BidText>` component. Eliminates 3 copies of the same logic.
3. **Move `ALL_SEATS` to constants** -- Eliminates 3 duplicate arrays.

### Medium impact
4. **Fix AppLayout link** -- Change `/lobby` to `/`.
5. **Remove `showSessionHeader = true`** dead indirection.
6. **Extract action error helper** in App.tsx.
7. **Fix outdated comment** in client.ts about ProtectedRoute.

### Low impact (nice to have)
8. **Fix ThoughtProcess dead code** -- Either remove opacity logic or stop pre-filtering steps.
9. **Update ThoughtProcess docstring**.
10. **Move SeatPicker** to its own component file.
