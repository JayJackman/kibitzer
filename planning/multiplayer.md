# Multiplayer & Helper Mode Planning Document

## Context

The practice mode currently supports solo play (1 human + 3 computer opponents). We want to add two capabilities:

1. **Multiplayer Practice** — 1-4 humans in a practice session, with computers filling remaining seats. Same random-deal, engine-feedback experience, just with friends.
2. **Helper Mode** — A companion for physical bridge. Players enter their real hands, enter bids as they happen at the table, and get engine advice when confused. 1-4 players, drop in/out freely.

Both modes share the existing practice UI (HandDisplay, AuctionGrid, BidControls, AdvicePanel). The `PracticeSession` class is already documented as "multi-player ready" — `players: dict[Seat, int | None]` maps seats to user_ids, and all methods take `user_id` to look up the seat.

## Design Decisions

| Decision | Choice |
|----------|--------|
| **Joining** | Share URL (`/practice/{id}`) + 6-character join code (both) |
| **Real-time sync** | Polling via `useRevalidator()` every 2s when waiting |
| **Helper dealer/vuln** | Manually set by session creator |
| **Architecture** | Extend `PracticeSession` with a `mode` field (not a new class) |
| **Hand entry format** | PBN text input (`AKJ52.KQ3.84.A73`) — `Hand.from_pbn()` already exists |

## Feature Comparison

| Behavior | Practice (solo/multiplayer) | Helper |
|----------|---------------------------|--------|
| Hands | Random deal via `deal()` | Manually entered via `set_hand()` |
| Computer auto-bidding | Yes, for unoccupied seats | No |
| Proxy bidding | No | Yes, any player can bid for unoccupied seats |
| Dealer/vulnerability | Auto-assigned + rotated on redeal | Manually set by creator |
| Engine feedback | Matched/missed on all human bids | Available but secondary |
| Redeal | Yes (rotate dealer, new hands) | Reset (clear bids, keep/re-enter hands) |
| Advice | On demand | On demand (primary purpose) |

---

## Part A: Multiplayer Practice

### Backend Changes

**`session.py` — PracticeSession**

Add `SessionMode` enum (`"practice"` / `"helper"`), `join_code` field, and new methods:

```python
join(user_id, seat)      # Claim an unoccupied seat
leave(user_id)           # Revert seat to computer control
available_seats()        # List unoccupied seats
```

New exceptions: `SeatOccupiedError`, `AlreadySeatedError`.

Add to `PracticeState` dataclass:
- `mode: SessionMode`
- `join_code: str`
- `players: dict[Seat, str | None]` — username per seat (None = computer)
- `waiting_for: Seat | None` — which human seat we're waiting on

**`state.py` — Session store**

Add join code index: `_join_codes: dict[str, str]` mapping code → session_id. Generate 6-char codes from `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (no ambiguous I/O/0/1). Add `get_session_by_code(code)` lookup. Extend `create_session()` to accept `mode`.

**`router.py` — New endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/{id}/info` | GET | Lightweight session info for join UI (seats, mode, code) |
| `/{id}/join` | POST | Join session at a specific seat |
| `/{id}/leave` | POST | Leave session (seat reverts to computer) |
| `/join/{code}` | GET | Look up session by join code → returns session info |

**`schemas.py` — New schemas**

- `CreatePracticeRequest`: add `mode` field (default `"practice"`)
- `CreatePracticeResponse`: add `join_code`
- `JoinSessionRequest`: `{ seat: "N" }`
- `SessionInfoResponse`: `{ id, mode, join_code, players, available_seats }`
- `PracticeStateResponse`: add `mode`, `join_code`, `players`, `waiting_for`

### Frontend Changes

**Join flow — visiting a session you're not in:**

1. `practiceLoader` calls `GET /api/practice/{id}`
2. Backend returns 403 (not seated)
3. Loader catches 403, calls `GET /api/practice/{id}/info`
4. Returns `{ needsJoin: true, info: SessionInfo }`
5. `PracticePage` renders `JoinPanel` showing available seats
6. User picks seat → POST `/{id}/join` → loader revalidates → full practice UI

**Join flow — via code from lobby:**

1. User enters code on lobby page
2. Form submits, action calls `GET /api/practice/join/{code}` → gets session ID
3. Redirects to `/practice/{id}` → continues join flow above

**New components:**

- **`JoinPanel`** — Seat picker for available seats, shown when `needsJoin` is true
- **`SessionHeader`** — Shows join code (with copy button), player names at each seat, "Leave" button

**Polling:**

```tsx
// In PracticePage, when waiting for another human's bid
const revalidator = useRevalidator();
useEffect(() => {
  if (!state.is_my_turn && !state.auction.is_complete && state.waiting_for) {
    const interval = setInterval(() => {
      if (revalidator.state === "idle") revalidator.revalidate();
    }, 2000);
    return () => clearInterval(interval);
  }
}, [state.is_my_turn, state.auction.is_complete, state.waiting_for]);
```

**Lobby changes:**

- Add "Multiplayer Practice" card (same seat picker + mode hidden field)
- Add "Join Session" card (code input → form submit)
- Current "Solo Practice" card stays as-is

---

## Part B: Helper Mode

### Backend Changes

**`session.py` — Helper mode behavior**

In `__init__` when `mode == HELPER`:
- Don't call `deal()` — `self.hands = {s: None for s in Seat}` (empty dict with None values)
- Accept `dealer` and `vulnerability` parameters from creator
- Don't call `_run_computer_bids()`

Type change: `self.hands` becomes `dict[Seat, Hand | None]` to support incremental hand entry.

New method:
```python
def set_hand(self, seat: Seat, hand: Hand) -> None:
    """Set hand for a seat (helper mode only).
    Validates no duplicate cards across all entered hands."""
```

Modify `place_bid()` — add `for_seat: Seat | None = None` parameter:
- When `for_seat` is set and mode is HELPER, allow any seated player to bid for an unoccupied seat
- Validate the target seat is the current bidder

Modify `get_state()` — add helper-specific fields:
- `can_proxy_bid: bool` — true when an unoccupied seat needs to bid
- `proxy_seat: Seat | None` — which seat the proxy bid is for

Modify `get_advice()` — raise `HandNotSetError` if hand is None.

Skip `_run_computer_bids()` entirely when mode is HELPER.

**`router.py` — New endpoint**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/{id}/hand` | POST | Set hand for your seat (PBN format) |

**`schemas.py`**

- `CreatePracticeRequest`: add optional `dealer`, `vulnerability` fields (helper mode)
- `SetHandRequest`: `{ hand_pbn: "AKJ52.KQ3.84.A73" }`
- `PlaceBidRequest`: add optional `for_seat` field (proxy bidding)
- `PracticeStateResponse`: add `can_proxy_bid`, `proxy_seat`; make `hand` and `hand_evaluation` nullable

### Frontend Changes

**Hand entry form** — shown instead of `HandDisplay` when `hand` is null and mode is helper:

```
+---------------------------+
| Enter Your Hand           |
|                           |
| [AKJ52.KQ3.84.A73    ]   |
| Format: Spades.Hearts.    |
|         Diamonds.Clubs    |
|                           |
| [Submit Hand]             |
+---------------------------+
```

Text input → POST `/{id}/hand` → loader revalidates → hand + evaluation appear.

**Proxy bid UI** — when `can_proxy_bid` is true:
- Show `BidControls` with banner: "Bid for [Seat Name]"
- Form includes hidden `for_seat` field
- Same button grid, same keyboard shortcuts

**Lobby changes:**
- Add "Helper Mode" card with:
  - Seat picker
  - Dealer picker (N/E/S/W buttons)
  - Vulnerability picker (None/NS/EW/Both)
  - "Create Session" button

---

## Implementation Phases

### Phase 1: Backend multiplayer foundation
- Add `SessionMode`, `join_code` to `PracticeSession.__init__`
- Add `join()`, `leave()`, `available_seats()` methods
- Add `players`, `mode`, `join_code`, `waiting_for` to `PracticeState`
- Add join code index to `state.py`
- Add endpoints: `GET /{id}/info`, `POST /{id}/join`, `POST /{id}/leave`, `GET /join/{code}`
- Modify `CreatePracticeRequest/Response` schemas
- Add `SessionInfoResponse` schema
- Extend `PracticeStateResponse` with new fields
- Update serialization in `serialize_practice_state()`
- Unit tests for new session methods
- Integration tests for new endpoints

### Phase 2: Frontend multiplayer
- Add `SessionInfo` type and new API functions
- Modify `practiceLoader` for 403 → join flow
- Build `JoinPanel` component (seat picker for non-members)
- Build `SessionHeader` component (join code + player names + leave button)
- Add polling via `useRevalidator()` when waiting for another human
- Add "Join Session" card to Lobby (code input)
- Add "Multiplayer Practice" card to Lobby
- Add `/join/:code` route

### Phase 3: Backend helper mode
- Handle `mode=HELPER` in `__init__` (no deal, manual dealer/vuln)
- Change `hands` type to `dict[Seat, Hand | None]`
- Add `set_hand()` method with cross-hand duplicate validation
- Modify `place_bid()` for proxy bidding (`for_seat` param)
- Add `can_proxy_bid`, `proxy_seat` to `PracticeState`
- Skip `_run_computer_bids()` when mode is HELPER
- Guard `get_advice()` against None hands
- Add `POST /{id}/hand` endpoint
- Add `SetHandRequest` schema; modify `PlaceBidRequest`
- Make `hand`/`hand_evaluation` nullable in response schema
- Tests

### Phase 4: Frontend helper mode
- Build `HandEntryForm` component (PBN text input)
- Add dealer/vulnerability pickers to Lobby
- Add "Helper Mode" card to Lobby
- Modify `PracticePage` to show `HandEntryForm` when hand is null
- Build proxy bid UI (banner + `for_seat` hidden field)
- Modify types for nullable hand/evaluation

## Key Files

| File | Changes |
|------|---------|
| `src/bridge/api/practice/session.py` | SessionMode, join/leave/set_hand, proxy bidding, nullable hands |
| `src/bridge/api/practice/state.py` | Join code index, extended create_session |
| `src/bridge/api/practice/router.py` | 4 new endpoints, modified bid endpoint |
| `src/bridge/api/practice/schemas.py` | New request/response schemas, extended state response |
| `frontend/src/api/types.ts` | SessionInfo, SessionMode, extended PracticeState |
| `frontend/src/api/endpoints.ts` | New API functions (join, leave, setHand, getInfo) |
| `frontend/src/App.tsx` | Modified practiceLoader, new /join/:code route |
| `frontend/src/pages/Lobby.tsx` | Multiplayer + helper + join-by-code cards |
| `frontend/src/pages/Practice.tsx` | JoinPanel, SessionHeader, polling, proxy bids, hand entry |

## Existing Code to Reuse

- `Hand.from_pbn()` in `src/bridge/model/hand.py` — PBN hand parsing (already validates 13 cards)
- `_run_computer_bids()` in session.py — already stops at any human seat (works for N humans)
- `seat_for(user_id)` — lookup pattern works for any number of humans
- `get_state(user_id)` — per-user filtering already in place
- `compute_legal_bids()` — works regardless of who is bidding
- `BidControls` component — reusable for proxy bids with banner addition
- `useBidKeyboard` hook — works for proxy bids (just needs legal bids list)

## Verification

- `pdm run check` — lint + typecheck + tests pass
- `cd frontend && npx tsc --noEmit && npm run build` — frontend builds clean
- Manual test: create multiplayer session, join from second browser, bid alternately
- Manual test: create helper session, enter hands, proxy bid, get advice
- Manual test: join by code from lobby
- Manual test: leave session mid-auction, verify computer takes over (practice mode)
