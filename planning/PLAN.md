# Bridge Bidding Assistant — Live Table & User-Facing Applications

## Context

The bridge bidding engine is mature: 126 SAYC rules, 739 tests, covering 3 rounds of uninterrupted bidding (opening, response, opener rebid). The engine works but has no user-facing interface — the service layer and CLI are empty placeholders. This plan pauses further rule development and focuses on delivering usable applications for a bridge group learning tool.

The key design choice: instead of a stateless "advise me once" model, the system tracks a **live auction** across multiple players. Each player has the app on their device, selects a seat, enters their hand, and bids in turn. The advisor is opt-in — tap "Advise Me" when you want help.

---

## Project Structure

### Current

```
bridge/
├── pyproject.toml
├── src/bridge/
│   ├── model/                  # Pure domain objects
│   │   ├── card.py             #   Card, Rank, Suit
│   │   ├── hand.py             #   Hand
│   │   ├── bid.py              #   Bid union type (SuitBid | PassBid | DoubleBid | RedoubleBid)
│   │   ├── auction.py          #   AuctionState, Seat
│   │   └── board.py            #   Board, Vulnerability
│   ├── evaluate/               # Hand metrics
│   │   └── hand_eval.py        #   HCP, distribution pts, quick tricks, LTC, controls
│   ├── engine/                 # Rule engine
│   │   ├── rule.py             #   Base Rule class, RuleResult
│   │   ├── registry.py         #   RuleRegistry (collects rules, indexes by category)
│   │   ├── selector.py         #   BidSelector (phase detection, priority resolution)
│   │   ├── context.py          #   BiddingContext (hand eval + auction state)
│   │   ├── sayc.py             #   Wires all SAYC rules into one registry
│   │   └── rules/sayc/         #   126 SAYC bidding rules
│   │       ├── opening/        #     Round 1: suit.py, nt.py, strong.py, preempt.py
│   │       ├── response/       #     Round 2: suit.py, nt.py, strong.py, preempt.py
│   │       └── rebid/          #     Round 3: suit.py, nt.py, strong.py, preempt.py
│   ├── llm/                    # Claude API integration (placeholder)
│   ├── service/                # Service layer (placeholder)
│   └── cli/                    # CLI (placeholder)
└── tests/                      # 739 tests (pytest + hypothesis)
    ├── model/
    ├── evaluate/
    └── engine/
```

### Proposed Additions

```
src/bridge/
│   ├── service/                    # Phase 0: Foundation layer
│   │   ├── advisor.py              #   BiddingAdvisor — wraps engine for bid advice
│   │   ├── models.py               #   BiddingAdvice, HandEvaluation, TableView, etc.
│   │   ├── table.py                #   Table — stateful game session
│   │   ├── lobby.py                #   Lobby — table management
│   │   ├── deal.py                 #   Random deal generator
│   │   └── thought_process.py      #   Deterministic thought-process generator
│   ├── cli/                        # Phase 1: CLI interface
│   │   ├── app.py                  #   Typer commands (advise, practice)
│   │   └── display.py              #   Rich output formatting
│   ├── api/                        # Phase 2: Web backend
│   │   ├── main.py                 #   FastAPI app
│   │   ├── routes.py               #   REST endpoints
│   │   ├── ws.py                   #   WebSocket handler
│   │   └── schemas.py              #   Pydantic request/response models
│   ├── engine/rules/sayc/          # Engine rule development (ongoing)
│   │   ├── reresponse/             #   Round 4: responder's rebids
│   │   ├── further/                #   Round 5+: later bidding
│   │   └── competitive/            #   Overcalls, doubles (cross-cutting)
frontend/                           # Phase 2: Web frontend (React or HTMX)
ios/                                # Phase 3: iOS app (SwiftUI)
```

---

## Core Concepts

### Table
A shared game session for up to 4 players. Tracks:
- Seat assignments (who is sitting where)
- Hands (private per player — server knows all, clients see only their own)
- Auction state (shared — all bids visible to everyone)
- Whose turn it is (derived from auction state)
- Final contract (when auction completes: 3 consecutive passes after an opening bid)

### Lobby
A persistent, private lobby for your friend group. Always accessible — no invite codes needed each session. Shows:
- Available tables (1 for now, infrastructure supports N)
- Who is seated where
- Table status (waiting for players, in progress, completed)

### Modes

**Multiplayer (primary):** 1-4 human players at a table. Each enters their own hand (manual text, or camera scan on iOS). Dealer bids first; play proceeds clockwise. Advisor available on-demand via "Advise Me" button.

**Proxy bidding:** Any seated player can enter bids for unoccupied seats. This allows 1, 2, or 3 players to run a full auction even when not everyone is logged in. For example, two friends at a real bridge table can each enter their own hand and bid, while also entering bids for the opponents sitting across from them. The "Advise Me" feature is only available for your own seat (not when proxy-bidding for others).

**Solo Practice (1-3 players):** App deals random hands for all seats. Computer bids for any seat without a human player using the engine. Human players try to find the correct bid each turn. "Advise Me" available for human seats. Works as a bidding quiz for 1 player, or a team exercise for 2-3 players practicing together.

> **Note — Solo mode limitation:** Computer opponents always pass when SAYC rules don't cover the situation. Once competitive bidding rules are implemented, computer opponents can make competitive bids. Until then, solo mode effectively practices uncontested auctions.

---

## Phase 0: Foundation Layer

The shared API surface that all UIs consume.

### 0A: Service/Advisor Layer

**File:** `src/bridge/service/advisor.py`

```python
class BiddingAdvisor:
    def advise(hand, auction_state) -> BiddingAdvice
```

**`BiddingAdvice` response object** (new dataclass):
- `recommended: RuleResult` — the top bid with explanation
- `alternatives: list[RuleResult]` — other matching rules
- `hand_evaluation: HandEvaluation` — HCP, total points, shape, etc.
- `phase: Category` — which bidding phase was detected

**`HandEvaluation` dataclass** (new):
- HCP, length points, total points, distribution points, support points
- Shape description, balanced/semi-balanced flags
- Quick tricks, LTC, controls

### 0B: Table/Session Management

**File:** `src/bridge/service/table.py`

Core state management for a live table:

```python
class Table:
    id: str
    seats: dict[Seat, Player | None]  # who is sitting where
    hands: dict[Seat, Hand | None]     # private per player
    auction: AuctionState
    status: TableStatus  # WAITING, IN_PROGRESS, COMPLETED

    def join(seat, player) -> None
    def leave(seat) -> None
    def set_hand(seat, hand) -> None
    def make_bid(seat, bid) -> None  # validates turn order; any seated player can bid for unoccupied seats
    def get_state(seat) -> TableView  # filtered: only your hand + shared auction
    def get_advice(seat) -> BiddingAdvice  # uses advisor internally
    def reset() -> None  # clear hands/auction, keep seats
```

**`TableView`** — what a client sees (no other players' hands):
- Your seat, your hand
- All seat assignments (names)
- Full auction history
- Whose turn it is
- Contract result (if auction complete)

### 0C: Lobby Management

**File:** `src/bridge/service/lobby.py`

```python
class Lobby:
    tables: list[Table]

    def create_table() -> Table
    def get_table(table_id) -> Table
    def list_tables() -> list[TableSummary]
```

For now, a single in-memory lobby with one table. Infrastructure supports multiple tables — the list/create API is there, but the UI only needs to show one.

### 0D: Hand & Auction Input Parsing

Enhance hand input to support multiple formats:
- **PBN** (existing): `AKJ52.KQ3.84.A73`
- **Labeled** (existing): `S:AKJ52 H:KQ3 D:84 C:A73`

Auction parsing utility:
- `parse_auction("1H P 2H P", dealer=Seat.NORTH) -> AuctionState`
- Handles: suit bids (`1H`, `3NT`), pass (`P`), double (`X`), redouble (`XX`)

### 0E: Random Deal Generator

**File:** `src/bridge/service/deal.py`

```python
def deal() -> dict[Seat, Hand]  # deal 52 cards into 4 hands of 13
```

Used by solo practice mode and optionally by multiplayer ("deal for us").

**Key files to create/modify:**
- `src/bridge/service/advisor.py` (new)
- `src/bridge/service/models.py` (new — BiddingAdvice, HandEvaluation, TableView, etc.)
- `src/bridge/service/table.py` (new)
- `src/bridge/service/lobby.py` (new)
- `src/bridge/service/deal.py` (new)
- `src/bridge/service/__init__.py` (exports)
- `src/bridge/model/auction.py` (add parse_auction)
- Tests for all of the above

---

## Phase 1: CLI Interface

Interactive terminal application using typer + rich (already dependencies). Primarily for testing the service layer and solo practice. The CLI won't support multiplayer (that needs a server), but it validates the full advise flow.

### 1A: Single-Shot Mode (`bridge advise`)

```bash
bridge advise --hand "AKJ52.KQ3.84.A73" --auction "1H P"
```

The engine infers your seat from the auction (it's always the next to act). Calls the advisor and prints results.

### 1B: Solo Practice Mode (`bridge practice`)

Interactive loop:
1. App deals a random hand, shows it to you
2. Shows the auction so far (computer bids for other seats)
3. Prompts you for your bid
4. Optionally shows advice if you ask
5. Tells you if your bid matches the engine's recommendation
6. Repeats until auction completes, then shows final contract

### 1C: Output Design

Rich-formatted terminal output:

```
--- Your Hand ---------------------------------
  S: A K J 5 2
  H: K Q 3
  D: 8 4
  C: A 7 3

  HCP: 15   Length Pts: 1   Total: 16
  Shape: 5-3-2-3   Quick Tricks: 3.5
--------------------------------------------------

--- Auction -----------------------------------
  N     E     S     W
  1H    P     ?
--------------------------------------------------

--- Recommended Bid: 1S ----------------------
  5+ spades, new suit at 1-level (forcing)
  SAYC: new suit response at 1-level

  THOUGHT PROCESS:
  - You have 15 HCP with a 5-card spade suit
  - Partner opened 1H, you need to respond
  - Bid your longest suit; 1S is forcing for one round
  - With this strength, you'll show spade length first
    and support hearts later if appropriate

--- Alternatives ------------------------------
  2H  - Single raise (3+ support, 6-10 pts)
        But you have 15 HCP, too strong for a single raise
  2NT - 13-15 HCP balanced, no 4-card major
        But you have a 5-card major to show first
--------------------------------------------------
```

### 1D: Thought Process Generation

Deterministic thought-process generator (no LLM needed):
1. Lists relevant hand metrics
2. Explains why the chosen rule matched
3. Explains why obvious alternatives were rejected
4. References SAYC guidelines

Each rule category gets a thought-process template.

**Key files:**
- `src/bridge/cli/app.py` (typer commands)
- `src/bridge/cli/display.py` (rich output)
- `src/bridge/service/thought_process.py` (thought process generator)
- Tests

---

## Phase 2: Web Application (FastAPI + HTMX or React)

The primary multiplayer interface. All devices connect to a shared server.

### 2A: FastAPI Backend

REST + WebSocket API wrapping the service layer:

```
# Lobby
GET  /api/tables              -> list of tables with status
POST /api/tables              -> create a new table

# Table management
POST /api/tables/{id}/join    -> join a seat
POST /api/tables/{id}/leave   -> leave your seat
POST /api/tables/{id}/hand    -> upload your hand
POST /api/tables/{id}/bid     -> make a bid (validates turn; any player can bid for unoccupied seats)
POST /api/tables/{id}/reset   -> reset for next hand
GET  /api/tables/{id}/state   -> get current table view (filtered to your seat)
GET  /api/tables/{id}/advise  -> get bid advice for your seat

# Real-time
WS   /api/tables/{id}/ws      -> WebSocket for live updates
```

WebSocket pushes events to all connected clients:
- Player joined/left
- Hand submitted (not the hand itself — just "North has entered their hand")
- Bid made (the bid is public)
- Auction complete (contract announcement)

### 2B: Frontend

Screens:
1. **Lobby** — see tables, join one, pick a seat
2. **Table** — your hand, auction grid, bid controls, "Advise Me" button
3. **Results** — after auction completes, shows contract and full history

The table screen shows:
- Your 13 cards (sorted by suit)
- The 4-seat auction grid filling in as bids are made
- Whose turn it is (highlighted)
- Bid input (buttons for pass/double/redouble, dropdown or grid for suit bids)
- "Advise Me" button that reveals recommendation + thought process
- Hand evaluation sidebar

### 2C: Authentication (Minimal)

For a private friend group, keep it simple:
- Player name stored in browser (localStorage)
- Optional: simple shared password to access the lobby
- No full auth system needed initially

### 2D: Solo Practice (Web)

Same as CLI solo mode but in the browser:
- App deals a hand, shows it
- Computer bids for other seats
- Player bids via the UI
- Shows if the bid was correct
- "Advise Me" available

**Key files:**
- `src/bridge/api/` (new package)
- `src/bridge/api/main.py` (FastAPI app)
- `src/bridge/api/routes.py` (REST endpoints)
- `src/bridge/api/ws.py` (WebSocket handler)
- `src/bridge/api/schemas.py` (Pydantic request/response)
- `frontend/` (React or HTMX at project root)

---

## Phase 3: iOS App (Swift Native)

### 3A: Core App

SwiftUI app connecting to the FastAPI backend (Phase 2):
- Lobby screen — see tables, pick a seat
- Table screen — hand display, auction grid, bid controls
- Advise Me — tap for recommendations
- Solo practice mode

### 3B: Camera Hand Scanning

Key differentiator for the iOS app:
- Use Vision framework to recognize playing cards from camera
- Scan a 13-card hand laid out on a table
- Parse recognized cards into hand format
- Auto-populate the hand input

### 3C: Offline Mode (Future)

- Embed a lightweight version of the engine for solo practice without a server
- Multiplayer always requires the server

**Key files:**
- Separate Xcode project or `ios/` directory
- Swift/SwiftUI views
- Networking layer to call FastAPI + WebSocket

---

## Phase 4: Desktop Application (PyQt6)

### 4A: Core Window

Same interaction model as the web app, but native desktop:
- Connect to the FastAPI backend for multiplayer
- Standalone mode for solo practice (uses engine directly, no server needed)
- Hand input (text entry)
- Auction display, bid controls, advisor

---

## Phase 5: LLM Enhancement (Future)

After all UIs are working with rule-based explanations:
- Integrate Claude API for richer, conversational explanations
- "Ask Claude" button for deeper analysis
- Alternative bid analysis with trade-off discussion
- Uses the existing `src/bridge/llm/` placeholder

---

## Engine Rule Development (Ongoing)

The engine currently covers 3 rounds of uncontested bidding (opening, response, opener rebid) with 126 rules. The following rule work remains and can proceed in parallel with UI development.

### Responder's Rebids (Round 4)

Rules in `reresponse/`. After opener rebids, responder must:
- Sign off, invite, or bid game based on combined information
- Handle game tries from opener's side (accept/reject)
- Place the final contract in many common auctions

Files: `src/bridge/engine/rules/sayc/reresponse/`

### Further Bidding (Round 5+)

Rules in `further/`. Rare but necessary for:
- Slam exploration sequences (Blackwood/Gerber continuations)
- Competitive auctions that go many rounds
- Misfit hands where both sides keep bidding

Files: `src/bridge/engine/rules/sayc/further/`

### Competitive Bidding

Cross-cutting across all rounds. Includes:
- Overcalls (simple, jump, NT)
- Takeout doubles and responses
- Negative doubles
- Balancing
- Competitive re-raises

This is the largest remaining rule area. It affects every round of bidding and unlocks realistic computer opponents in solo mode.

Files: `src/bridge/engine/rules/sayc/competitive/`

---

## Deferred Items

- **Vulnerability & dealer rotation** — not yet implemented. The model supports it, but the UI doesn't manage it. Will add board number tracking and automatic rotation later.
- **Multiple simultaneous tables** — infrastructure supports it (lobby has a list of tables), but UI only shows one table for now.
- **Player persistence/accounts** — currently just names. Could add simple login later if needed.

---

## Implementation Order

```
Phase 0  ->  Phase 1  ->  Phase 2  ->  Phase 3  ->  Phase 4
Foundation    CLI         Web+API       iOS          Desktop
 (0A-0E)    (1A-1D)     (2A-2D)      (3A-3C)       (4A)
```

Phase 0 is the most critical — it defines the shared service layer. Phase 1 proves the advisor UX. Phase 2 is the main deliverable (multiplayer). Phase 3 adds the camera feature. Phase 4 is optional/nice-to-have.

---

## Verification

After each phase:
- `pdm run check` passes (lint + typecheck + test)
- Manual testing with known hands from the test suite
- Verify output matches expected SAYC bids

Test hands:
- Balanced 15 HCP -> 1NT opening
- 5-card major with 13 HCP -> 1-major opening
- Response to partner's 1H with 10 HCP and 3-card support -> limit raise
- Weak hand with 6-card suit -> weak two opening
- Full 3-round auction: open 1S, respond 2S, rebid 3C (game try)
