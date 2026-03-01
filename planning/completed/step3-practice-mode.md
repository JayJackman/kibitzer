# Step 3: Web Practice Mode — Detailed Implementation Plan

## Overview

Bring the CLI practice mode to the browser. A logged-in user creates a practice session, sees their dealt hand, bids in turn while the computer plays the other three seats, and can ask the engine for advice at any time.

**Scope**: Solo practice only (1 human player). The backend architecture is designed so multi-player practice (2-4 humans sharing a session) can be added later without rework — the `PracticeSession` class models seats as `user_id | None`, and the API schemas support multiple occupied seats. But for this step, we build and test the solo path end-to-end.

**Goal**: A user can log in, click "Practice", and play through complete bidding auctions in the browser with the same functionality as the CLI.

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Scope** | Solo-only (1 player) | Proves full stack fastest. Multi-player added later. |
| **Dealer rotation** | Auto-rotate clockwise each hand | Realistic bridge progression (N, E, S, W, N, ...). |
| **Vulnerability** | Random each hand | Simple, exposes player to all vulnerability states. |
| **Bid input** | Button grid (7x5 + Pass/Dbl/Rdbl) | Visual, no typing needed. Illegal bids disabled. |
| **End of hand** | Show all 4 hands + contract + "New Hand" | Matches CLI. Bid-by-bid review added later. |
| **Session storage** | In-memory (dict keyed by session ID) | Fast, simple. No DB persistence needed for practice. |
| **Frontend state** | React Router loaders + actions | Matches existing patterns. Loader fetches state, actions mutate. |

---

## Architecture

### State Flow

```
Browser                          FastAPI                         Engine
  |                                |                                |
  |  POST /api/practice            |                                |
  |  {seat: "S"}                   |                                |
  |------------------------------->|  create PracticeSession         |
  |                                |  deal() -> 4 hands             |
  |                                |  computer_bids() until human   |
  |                                |  store in sessions dict         |
  |  <-----------------------------|  {id, hand, eval, auction, ...} |
  |                                |                                |
  |  redirect to /practice/:id     |                                |
  |                                |                                |
  |  GET /api/practice/:id         |                                |
  |------------------------------->|  lookup session                 |
  |                                |  return filtered state          |
  |  <-----------------------------|  {hand, eval, auction, ...}     |
  |                                |                                |
  |  POST /api/practice/:id/bid    |                                |
  |  {bid: "1S"}                   |                                |
  |------------------------------->|  validate & add player bid      |
  |                                |  computer_bids() until human   |---> advisor.advise()
  |                                |  check if auction complete      |
  |  <-----------------------------|  {matched, feedback, ...}       |
  |                                |                                |
  |  GET /api/practice/:id/advise  |                                |
  |------------------------------->|  advisor.advise(hand, auction) |---> engine pipeline
  |  <-----------------------------|  {recommended, alternatives,    |
  |                                |   thought_process}             |
  |                                |                                |
  |  POST /api/practice/:id/redeal |                                |
  |------------------------------->|  deal new hands, reset auction  |
  |                                |  computer_bids() until human   |
  |  <-----------------------------|  {hand, eval, auction, ...}     |
```

### Backend: Session lives in memory

```python
# In-memory store (practice/state.py)
_sessions: dict[str, PracticeSession] = {}
```

No database table for practice sessions. They live only in server memory. Restarting the server clears all sessions. This is fine — practice sessions are ephemeral.

The `PracticeSession` class is designed for N players (1-4), but this step only exercises the solo path. The class stores `players: dict[Seat, int | None]` where `int` is a user ID and `None` means computer-controlled. For solo practice, exactly one seat has a user ID.

### Frontend: Loader/Action pattern

The practice page uses the same React Router data patterns as login/register:

- **Loader** (`GET /api/practice/:id`): Fetches session state before the page renders. No loading spinners needed.
- **Action** (`POST /api/practice/:id/bid` and `POST /api/practice/:id/redeal`): Handles bid submission and redeal. After the action completes, React Router automatically re-runs the loader, so the page updates with fresh state.
- **Fetcher** (`GET /api/practice/:id/advise`): The "Advise Me" button fetches advice without navigating. Uses `useFetcher()` to load advice data into component state.

---

## Backend Implementation

### File Structure

```
src/bridge/api/practice/
    __init__.py
    router.py          # API endpoints
    schemas.py         # Pydantic request/response models
    session.py         # PracticeSession class (business logic)
    state.py           # In-memory session store + helpers
```

### PracticeSession Class (`session.py`)

The core state machine. Manages hands, auction, computer bidding, and advice.

```python
class PracticeSession:
    id: str                                    # UUID
    host_user_id: int                          # Who created it
    players: dict[Seat, int | None]            # Seat -> user_id or None (computer)
    hands: dict[Seat, Hand]                    # All 4 hands (dealt by server)
    auction: AuctionState                      # Current auction state
    advisor: BiddingAdvisor                    # Shared engine instance
    hand_number: int                           # Tracks deal count (for dealer rotation)
```

No `player_seat` field — the `players` dict is the single source of truth for who sits where. Methods that need a user's seat look it up via `user_id` in `players`. This keeps the model multi-player-ready.

Key methods:

| Method | Purpose | Returns |
|--------|---------|---------|
| `__init__(user_id, seat, advisor)` | Create session, deal hands, run computer bids | -- |
| `get_state(user_id)` | Filtered view: only the human's hand, full auction | `PracticeState` |
| `place_bid(user_id, bid_str)` | Validate + add human bid, run computer bids | `BidResult` |
| `get_advice(user_id)` | Engine recommendation for human's current position | `BiddingAdvice` |
| `redeal()` | New hands, rotate dealer, random vuln, run computer bids | -- |

#### Computer Bidding Logic

After any state change (creation, player bid, redeal), the session auto-advances computer seats:

```python
def _run_computer_bids(self) -> list[ComputerBidRecord]:
    """Advance all computer seats until it's the human's turn or auction ends."""
    computer_bids = []
    while not self.auction.is_complete:
        current = self.auction.current_seat
        if self.players[current] is not None:
            break  # Human's turn
        advice = self.advisor.advise(self.hands[current], self.auction)
        self.auction.add_bid(advice.recommended.bid)
        computer_bids.append(ComputerBidRecord(
            seat=current,
            bid=advice.recommended.bid,
            explanation=advice.recommended.explanation,
        ))
    return computer_bids
```

#### Dealer Rotation & Vulnerability

```python
def _next_dealer(self) -> Seat:
    """Rotate dealer clockwise: N -> E -> S -> W -> N -> ..."""
    return Seat((self.auction.dealer.value + 1) % 4)

def _random_vulnerability(self) -> Vulnerability:
    """Pick a random vulnerability for the next hand."""
    return random.choice([
        NO_VULNERABILITY, NS_VULNERABLE, EW_VULNERABLE, BOTH_VULNERABLE,
    ])
```

#### Bid Feedback

When the human bids, the session compares their bid against the engine's recommendation:

```python
@dataclass
class BidResult:
    matched_engine: bool           # Did the human bid match the engine?
    engine_bid: str                # What the engine recommended (e.g. "1S")
    engine_explanation: str        # Why the engine chose that bid
    computer_bids: list[...]       # Computer bids that followed
    auction_complete: bool         # Is the auction now over?
    contract: Contract | None      # Final contract (if complete)
```

### In-Memory State Store (`state.py`)

```python
_sessions: dict[str, PracticeSession] = {}

def create_session(user_id: int, seat: Seat, advisor: BiddingAdvisor) -> PracticeSession: ...
def get_session(session_id: str) -> PracticeSession | None: ...
def delete_session(session_id: str) -> None: ...
```

Simple module-level dict. Thread-safe enough for development (FastAPI runs in a single thread with uvicorn in dev mode). For production, we'd move to a proper store, but that's not needed now.

#### Multi-player readiness

The `players` dict supports multiple human seats. When we add multi-player:
- `join(seat, user_id)` assigns a human to a seat
- `leave(seat)` reverts a seat to computer control
- `_run_computer_bids()` already skips any seat with a user_id
- State filtering already scopes hand visibility per user

No structural changes needed -- just new endpoints and UI flows.

### API Endpoints (`router.py`)

```
POST   /api/practice                 Create a new practice session
GET    /api/practice/{id}            Get current session state
POST   /api/practice/{id}/bid        Place a bid
GET    /api/practice/{id}/advise     Get engine advice
POST   /api/practice/{id}/redeal     Deal new hands
```

#### `POST /api/practice` -- Create Session

Request:
```json
{"seat": "S"}
```

Response (201):
```json
{
  "id": "abc123"
}
```

The frontend action redirects to `/practice/abc123`. The loader then fetches the full state.

#### `GET /api/practice/{id}` -- Get State

Response (200):
```json
{
  "id": "abc123",
  "your_seat": "S",
  "hand": {
    "spades": ["A", "K", "J", "5", "2"],
    "hearts": ["K", "Q", "3"],
    "diamonds": ["8", "4"],
    "clubs": ["A", "7", "3"]
  },
  "hand_evaluation": {
    "hcp": 15,
    "length_points": 1,
    "total_points": 16,
    "distribution_points": 1,
    "controls": 6,
    "quick_tricks": 3.5,
    "losers": 6,
    "shape": [5, 3, 2, 3],
    "is_balanced": false
  },
  "auction": {
    "dealer": "N",
    "vulnerability": "None",
    "bids": [
      {"seat": "N", "bid": "1D", "explanation": "4+ diamonds, 12-21 HCP"},
      {"seat": "E", "bid": "Pass"}
    ],
    "is_complete": false,
    "current_seat": "S",
    "contract": null
  },
  "computer_bids": [
    {"seat": "N", "bid": "1D", "explanation": "4+ diamonds, 12-21 HCP"}
  ],
  "is_my_turn": true,
  "legal_bids": ["1D", "1H", "1S", "1NT", "2C", "2D", "...", "Pass"],
  "last_feedback": null,
  "all_hands": null,
  "hand_number": 1
}
```

Notes:
- `hand` shows only the human's cards. Other hands are hidden.
- `computer_bids` lists bids made by computer seats since the human's last action. Displayed as notifications.
- `legal_bids` is the list of all legal bids at this point. The frontend uses this to enable/disable buttons.
- `all_hands` is `null` during bidding, populated when `auction.is_complete` is true (reveals all 4 hands).
- `last_feedback` carries the result of the previous bid ("matched engine" / "engine recommends X").

#### `POST /api/practice/{id}/bid` -- Place Bid

Request:
```json
{"bid": "1S"}
```

Response (200):
```json
{
  "matched_engine": false,
  "engine_bid": "2D",
  "engine_explanation": "New suit at 2-level, 10+ HCP, forcing one round"
}
```

After the action completes, the frontend re-runs the loader which returns the updated state (including any computer bids that followed, auction completion, etc.).

#### `GET /api/practice/{id}/advise` -- Get Advice

Response (200):
```json
{
  "recommended": {
    "bid": "2D",
    "rule_name": "response.new_suit_2_level",
    "explanation": "New suit at 2-level, 10+ HCP, forcing one round",
    "forcing": true,
    "alerts": []
  },
  "alternatives": [
    {
      "bid": "1S",
      "rule_name": "response.new_suit_1_level",
      "explanation": "New suit at 1-level, 6+ HCP",
      "forcing": true,
      "alerts": []
    }
  ],
  "thought_process": {
    "steps": [
      {
        "rule_name": "response.new_suit_2_level",
        "passed": true,
        "bid": "2D",
        "conditions": [
          {"label": "HCP >= 10", "detail": "15 HCP", "passed": true},
          {"label": "4+ suit", "detail": "2 diamonds", "passed": false}
        ]
      }
    ]
  },
  "phase": "response"
}
```

#### `POST /api/practice/{id}/redeal` -- New Hand

Response (200):
```json
{"ok": true}
```

The frontend revalidates the loader to get the new state.

### Pydantic Schemas (`schemas.py`)

Request models:
- `CreatePracticeRequest` -- `seat: str`
- `PlaceBidRequest` -- `bid: str`

Response models:
- `CreatePracticeResponse` -- `id: str`
- `PracticeStateResponse` -- full session state (hand, eval, auction, etc.)
- `BidResultResponse` -- feedback from placing a bid
- `AdviceResponse` -- engine recommendation + thought process
- `HandResponse` -- cards grouped by suit
- `HandEvalResponse` -- HCP, shape, etc.
- `AuctionResponse` -- bids, dealer, vulnerability, completion
- `AuctionBidResponse` -- single bid entry (seat, bid string, explanation or null)
- `ComputerBidResponse` -- seat, bid string, explanation
- `BidFeedbackResponse` -- matched_engine, engine_bid, engine_explanation
- `ContractResponse` -- level, suit, declarer, doubled/redoubled, passed_out
- `ThoughtProcessResponse` -- steps with condition results
- `ThoughtStepResponse` -- rule name, passed, bid, conditions
- `ConditionResponse` -- label, detail, passed
- `RuleResultResponse` -- bid, rule_name, explanation, forcing, alerts

#### Serialization Notes

The domain model uses frozen dataclasses and enums. The Pydantic schemas translate these to JSON-friendly shapes:

- `Bid` (union type) -> string (`"1S"`, `"Pass"`, `"X"`, `"XX"`)
- `Seat` (IntEnum) -> string (`"N"`, `"E"`, `"S"`, `"W"`)
- `Suit` (IntEnum) -> string (`"S"`, `"H"`, `"D"`, `"C"`)
- `Hand` (frozenset of Cards) -> `HandResponse` with suit arrays of rank strings
- `Contract` -> `ContractResponse` with string fields
- `ThoughtStep` -> `ThoughtStepResponse` with serialized conditions

We'll write serialization helpers (e.g., `format_bid_str(bid: Bid) -> str`) in `schemas.py` to keep the router clean.

### Legal Bids Computation

The frontend needs to know which bids are legal to enable/disable buttons. The backend computes this directly — no trial-and-error needed:

```python
def compute_legal_bids(auction: AuctionState) -> list[str]:
    """Return all legal bid strings for the current position."""
    legal = ["Pass"]
    last = auction.last_contract_bid
    for level in range(1, 8):
        for suit in Suit:  # C, D, H, S, NT — already in bidding rank order
            bid = SuitBid(level, suit)
            if last is None or bid > last:
                legal.append(format_bid_str(bid))
    if can_double(auction):
        legal.append("X")
    if can_redouble(auction):
        legal.append("XX")
    return legal
```

### Registration in `main.py`

Add to the existing `main.py`:

```python
from .practice.router import router as practice_router
app.include_router(practice_router)
```

### Shared BiddingAdvisor Instance

The `BiddingAdvisor` is stateless and expensive to construct (builds the full rule registry). We create one instance at startup and inject it into all sessions:

```python
# In main.py lifespan or deps.py
advisor = BiddingAdvisor()

def get_advisor() -> BiddingAdvisor:
    return advisor
```

Each `PracticeSession` receives this shared advisor via its constructor.

---

## Frontend Implementation

### File Structure

```
frontend/src/
    api/
        endpoints.ts           # Add practice API functions + types
    pages/
        Practice.tsx           # Practice session page
    components/
        hand/
            HandDisplay.tsx    # 13 cards arranged by suit
            CardRow.tsx        # Single suit row (symbol + ranks)
        auction/
            AuctionGrid.tsx    # 4-column bid history table
            BidControls.tsx    # 7x5 button grid + Pass/Dbl/Rdbl
        advice/
            AdvicePanel.tsx    # Recommendation + explanation
            ThoughtProcess.tsx # Condition trace
    App.tsx                    # Add practice routes + loader/actions
```

### New shadcn/ui Components Needed

Before building, install these additional shadcn components:
- **Badge** -- for bid display in the auction grid (colored per suit)
- **Separator** -- dividing sections within panels
- **Tooltip** -- hover info on bid buttons
- **ScrollArea** -- for auction history when it gets long

### Route Setup (`App.tsx`)

Add to the router configuration:

```typescript
import PracticePage from "@/pages/Practice";

// Inside the protected layout children:
{ path: "/practice/:id", element: <PracticePage />, loader: practiceLoader, action: practiceAction },

// Advice loader (used by useFetcher, no page element):
{ path: "/practice/:id/advise", loader: adviceLoader },

// Action-only route: POST creates the session, redirects to /practice/:id
{ path: "/practice/new", action: createPracticeAction },
```

### API Endpoints (`endpoints.ts`)

Add TypeScript interfaces and typed functions for each practice endpoint:

```typescript
// --- Practice types ---

interface HandData {
  spades: string[];
  hearts: string[];
  diamonds: string[];
  clubs: string[];
}

interface HandEvaluation {
  hcp: number;
  length_points: number;
  total_points: number;
  distribution_points: number;
  controls: number;
  quick_tricks: number;
  losers: number;
  shape: number[];
  is_balanced: boolean;
}

interface AuctionBid {
  seat: string;
  bid: string;
  explanation: string | null;
}

interface AuctionData {
  dealer: string;
  vulnerability: string;
  bids: AuctionBid[];
  is_complete: boolean;
  current_seat: string | null;
  contract: ContractData | null;
}

interface ContractData {
  level: number;
  suit: string;
  declarer: string;
  doubled: boolean;
  redoubled: boolean;
  passed_out: boolean;
}

interface ComputerBid {
  seat: string;
  bid: string;
  explanation: string;
}

interface BidFeedback {
  matched_engine: boolean;
  engine_bid: string;
  engine_explanation: string;
}

interface PracticeState {
  id: string;
  player_seat: string;
  hand: HandData;
  hand_evaluation: HandEvaluation;
  auction: AuctionData;
  computer_bids: ComputerBid[];
  is_my_turn: boolean;
  legal_bids: string[];
  last_feedback: BidFeedback | null;
  all_hands: Record<string, HandData> | null;
  hand_number: number;
}

interface RuleResultData {
  bid: string;
  rule_name: string;
  explanation: string;
  forcing: boolean;
  alerts: string[];
}

interface ConditionData {
  label: string;
  detail: string;
  passed: boolean;
}

interface ThoughtStepData {
  rule_name: string;
  passed: boolean;
  bid: string | null;
  conditions: ConditionData[];
}

interface AdviceData {
  recommended: RuleResultData;
  alternatives: RuleResultData[];
  thought_process: { steps: ThoughtStepData[] };
  phase: string;
}

// --- Practice endpoint functions ---

export async function createPractice(seat: string): Promise<{ id: string }>;
export async function getPracticeState(id: string): Promise<PracticeState>;
export async function placeBid(id: string, bid: string): Promise<BidFeedback>;
export async function getAdvice(id: string): Promise<AdviceData>;
export async function redealPractice(id: string): Promise<void>;
```

### Practice Page Layout (`Practice.tsx`)

Desktop layout (side-by-side):

```
+--------------------------------------------------+
|  PRACTICE MODE          Hand #3     [New Hand]    |
+------------------------+-------------------------+
|                        |                         |
|  YOUR HAND             |  AUCTION                |
|  S: A K J 5 2          |  W    N    E    S       |
|  H: K Q 3              |       1D  Pass   ?      |
|  D: 8 4                |                         |
|  C: A 7 3              |  FEEDBACK               |
|                        |  "Engine recommends 2D" |
|  HCP: 15  Pts: 16      |                         |
|  Shape: 5-3-2-3        |  COMPUTER BIDS          |
|  Balanced: No          |  North bid 1D:          |
|                        |    4+ diamonds, 12-21   |
|  [Advise Me]           |                         |
+------------------------+-------------------------+
|                                                  |
|  BID CONTROLS                                    |
|  [Pass]         [Double]         [Redouble]      |
|                                                  |
|     C      D      H      S      NT              |
|   [1C]   [1D]   [1H]   [1S]   [1NT]            |
|   [2C]   [2D]   [2H]   [2S]   [2NT]            |
|   [3C]   [3D]   [3H]   [3S]   [3NT]            |
|   [4C]   [4D]   [4H]   [4S]   [4NT]            |
|   [5C]   [5D]   [5H]   [5S]   [5NT]            |
|   [6C]   [6D]   [6H]   [6S]   [6NT]            |
|   [7C]   [7D]   [7H]   [7S]   [7NT]            |
+--------------------------------------------------+
```

On narrow screens, the panels stack vertically (hand on top, auction below).

When the auction is complete, the bid controls are hidden and replaced with all 4 hands in a bridge diagram layout:

```
+--------------------------------------------------+
|  PRACTICE MODE          Hand #3     [New Hand]    |
+------------------------+-------------------------+
|                        |                         |
|  YOUR HAND             |  AUCTION (complete)     |
|  S: A K J 5 2          |  W    N    E    S       |
|  H: K Q 3              |       1D  Pass  1S      |
|  D: 8 4                | Pass  2S  Pass  Pass    |
|  C: A 7 3              | Pass                    |
|                        |                         |
|  HCP: 15  Pts: 16      |  Contract: 2S by South  |
+------------------------+-------------------------+
|                                                  |
|  ALL HANDS                                       |
|               North                              |
|          S: Q 9 7 6                              |
|          H: 8 4                                  |
|          D: A K J 5 2                            |
|          C: 9 4                                  |
|  West                        East                |
|  S: 8 4              S: T 3                      |
|  H: T 9 2            H: J 8 7 6                 |
|  D: T 9              D: Q 7 3                    |
|  C: T 9 6 2          C: K 8 5                    |
|               South                              |
|          S: A K J 5 2                            |
|          H: K Q 3                                |
|          D: 8 4                                  |
|          C: A 7 3                                |
+--------------------------------------------------+
```

### Data Flow in React Router

**Loader** (`practiceLoader`):
```typescript
// Runs before PracticePage renders.
// Fetches GET /api/practice/:id and returns the state.
async function practiceLoader({ params }: LoaderFunctionArgs) {
  const state = await getPracticeState(params.id!);
  return { state };
}
```

**Action** (`practiceAction`):
```typescript
// Handles form submissions from BidControls and the redeal button.
// Reads a hidden "intent" field to distinguish bid vs redeal.
async function practiceAction({ request, params }: ActionFunctionArgs) {
  const formData = await request.formData();
  const intent = formData.get("intent");

  if (intent === "bid") {
    const result = await placeBid(params.id!, formData.get("bid") as string);
    // Return feedback -- the page reads it via useActionData()
    return result;
  }
  if (intent === "redeal") {
    await redealPractice(params.id!);
    // Redirect to same page -- triggers loader revalidation
    return redirect(`/practice/${params.id}`);
  }
}
```

**Advice Fetcher** (inside PracticePage):
```typescript
// useFetcher for non-navigation data loading.
// Clicking "Advise Me" triggers a GET without a full page navigation.
const adviceFetcher = useFetcher();

function handleAdvise() {
  adviceFetcher.load(`/practice/${id}/advise`);
}
// adviceFetcher.data contains the AdviceData when loaded.
```

### Bid Feedback Display

When the player bids, the action returns a `BidFeedback`. The page reads it via `useActionData()`:
- **Match**: green text -- "Matched the engine's recommendation."
- **Mismatch**: amber text -- "You bid 1S. The engine recommends 2D: new suit at 2-level, 10+ HCP."

This feedback persists on screen until the next bid or redeal.

### Component Details

#### `HandDisplay.tsx`

Displays the player's 13 cards grouped by suit. Uses `CardRow` for each suit.

Props:
```typescript
interface HandDisplayProps {
  hand: HandData;
  evaluation?: HandEvaluation;  // Optional: shows HCP, shape, etc. below cards
}
```

Layout: Card (shadcn) containing a vertical stack of 4 `CardRow` components (S, H, D, C from top to bottom). If `evaluation` is provided, shows metrics below the cards.

#### `CardRow.tsx`

A single suit row: colored suit symbol + space-separated rank characters.

Props:
```typescript
interface CardRowProps {
  suit: "S" | "H" | "D" | "C";
  ranks: string[];  // ["A", "K", "J", "5", "2"]
}
```

Renders: `[suit-symbol] A K J 5 2` with the suit symbol and ranks colored per `SUIT_COLORS` from constants.

#### `AuctionGrid.tsx`

4-column table showing the bid history. Columns are always W, N, E, S (standard bridge order). The grid pads empty cells at the start based on the dealer position (e.g., if dealer is East, W and N columns get an empty cell in row 1).

Props:
```typescript
interface AuctionGridProps {
  bids: AuctionBid[];
  dealer: string;
  currentSeat: string | null;   // null when auction is complete
  isComplete: boolean;
}
```

Each bid cell shows the bid text with suit coloring. The current seat shows "?" to indicate it's their turn. Completed auctions show no marker.

#### `BidControls.tsx`

The button grid. Pass/Double/Redouble across the top, then a 7-row x 5-column grid of suit bids.

Props:
```typescript
interface BidControlsProps {
  legalBids: string[];          // ["1H", "1S", ..., "Pass"]
  disabled: boolean;            // Disable everything if not player's turn
}
```

Each button submits a form with hidden fields:
```html
<Form method="post">
  <input type="hidden" name="intent" value="bid" />
  <button type="submit" name="bid" value="1S" disabled={!legalBids.includes("1S")}>
    1[spade-symbol]
  </button>
</Form>
```

Suit-colored text on buttons. Disabled/illegal buttons get muted `opacity-30` styling. The entire grid is hidden when the auction is complete (replaced by all-hands display).

#### `AdvicePanel.tsx`

Shows the engine's recommendation. Appears inline when the user clicks "Advise Me".

Props:
```typescript
interface AdvicePanelProps {
  advice: AdviceData | null;   // null when not yet requested
  isLoading: boolean;          // True while fetcher is loading
}
```

Layout (inside a Card):
- **Recommended bid** (large, colored by suit)
- **Explanation** text
- **Forcing** indicator (Badge component)
- **Phase** label (e.g., "Response")
- **Alternatives** list (bid + explanation for each)

#### `ThoughtProcess.tsx`

Shows how the engine reached its decision. Displayed below the advice panel.

Props:
```typescript
interface ThoughtProcessProps {
  steps: ThoughtStepData[];
}
```

Shows the winning rule prominently, with its conditions listed as checkmark/X indicators. Other evaluated rules listed below in muted style. Uses Separator between rules.

### Lobby Integration

The Lobby page gets a practice section with a seat picker:

```
+--------------------------------------+
|  Solo Practice                       |
|                                      |
|  Pick your seat:                     |
|  (N) (E) [S] (W)                    |
|                                      |
|  [Start Practice]                    |
+--------------------------------------+
```

The seat defaults to South. Submitting posts to `/practice/new`, which creates the session and redirects.

---

## Testing

### Backend Tests

#### `tests/api/test_practice_session.py` -- Unit tests (no HTTP)

| Test | What it verifies |
|------|-----------------|
| `test_init_deals_hands` | Constructor deals 4 hands of 13 cards each |
| `test_init_runs_computer_bids` | Constructor advances to human's turn |
| `test_get_state_shows_own_hand` | State includes human's hand |
| `test_get_state_hides_other_hands` | State does not include other hands during bidding |
| `test_get_state_reveals_all_when_complete` | All hands visible after auction ends |
| `test_place_bid_adds_to_auction` | Bid appears in auction history |
| `test_place_bid_runs_computer_bids` | Computer seats bid after human |
| `test_place_bid_feedback_match` | Reports match when bid equals engine recommendation |
| `test_place_bid_feedback_mismatch` | Reports mismatch with engine's bid and explanation |
| `test_get_advice` | Returns recommendation, alternatives, thought process |
| `test_redeal_rotates_dealer` | Dealer advances clockwise |
| `test_redeal_new_hands` | New hands are dealt (different from previous) |
| `test_redeal_preserves_seat` | Player seat stays the same after redeal |
| `test_legal_bids_correct` | Legal bids list matches what AuctionState allows |
| `test_auction_completes` | Three passes end the auction correctly |

#### `tests/api/test_practice.py` -- Integration tests (HTTP via TestClient)

| Test | What it verifies |
|------|-----------------|
| `test_create_session` | POST creates a session, returns ID |
| `test_create_session_unauthenticated` | 401 without login |
| `test_get_state` | GET returns hand, eval, auction, legal bids |
| `test_get_state_other_user` | 403 for wrong user accessing someone's session |
| `test_get_state_not_found` | 404 for bad session ID |
| `test_place_bid_valid` | POST bid succeeds, returns feedback |
| `test_place_bid_illegal` | 422 for illegal bid (e.g., bidding lower than current) |
| `test_place_bid_not_your_turn` | 409 when it's not the human's turn |
| `test_get_advice` | Returns recommendation with thought process |
| `test_get_advice_not_your_turn` | 409 when auction is complete |
| `test_redeal` | New hands dealt, dealer rotated |
| `test_full_auction_lifecycle` | Create -> bid through completion -> see all hands |

**Test fixture**: Mock `deal()` to return fixed hands for deterministic tests (same pattern as CLI tests).

---

## Implementation Order

The steps below are ordered for incremental, testable progress. Each sub-step produces something that can be verified before moving on.

### Sub-step 3.1: PracticeSession class + unit tests

**Files to create:**
- `src/bridge/api/practice/__init__.py`
- `src/bridge/api/practice/session.py`
- `src/bridge/api/practice/state.py`
- `tests/api/__init__.py` (if not exists)
- `tests/api/test_practice_session.py`

**What:**
Build the `PracticeSession` class with all methods (init, get_state, place_bid, get_advice, redeal, _run_computer_bids). Build the in-memory session store. Write unit tests that exercise the full lifecycle without HTTP.

**Verify:** `pdm run pytest tests/api/test_practice_session.py` passes.

### Sub-step 3.2: Pydantic schemas + serialization helpers

**Files to create:**
- `src/bridge/api/practice/schemas.py`

**What:**
Define all Pydantic request/response models. Write serialization helpers to convert domain objects (Bid, Hand, Seat, ThoughtProcess, etc.) to the JSON response shapes. These convert frozen dataclasses and enums into Pydantic-friendly dicts/strings.

**Verify:** Types pass `pdm run typecheck`. Schemas can be instantiated with sample data.

### Sub-step 3.3: API router + integration tests

**Files to create:**
- `src/bridge/api/practice/router.py`
- `tests/api/test_practice.py`

**Files to modify:**
- `src/bridge/api/main.py` (register practice router, create shared advisor)

**What:**
Wire up the 5 endpoints. Each endpoint is thin -- parse request, call session method, serialize response. Register the router in main.py. Write integration tests using `TestClient`.

**Verify:** `pdm run check` passes (lint + typecheck + all tests).

### Sub-step 3.4: Frontend API functions + types

**Files to modify:**
- `frontend/src/api/endpoints.ts` (add practice interfaces and functions)

**What:**
Add TypeScript interfaces mirroring the Pydantic response schemas. Add typed API call functions for each practice endpoint.

**Verify:** `npm run build` succeeds (TypeScript compiles with no errors).

### Sub-step 3.5: HandDisplay + CardRow components

**Files to create:**
- `frontend/src/components/hand/HandDisplay.tsx`
- `frontend/src/components/hand/CardRow.tsx`

**What:**
Build the hand display components. Use `SUIT_SYMBOLS` and `SUIT_COLORS` from constants. Wrap in a Card (shadcn). Include optional hand evaluation display below the cards.

**Verify:** Visual test by temporarily rendering with hardcoded data.

### Sub-step 3.6: AuctionGrid component

**Files to create:**
- `frontend/src/components/auction/AuctionGrid.tsx`

**What:**
Build the 4-column bid history table. Handle dealer offset (empty cells before dealer's first bid). Color bids by suit. Show "?" marker for current seat during active auctions.

**Verify:** Visual test with sample auction data (empty, partial, complete).

### Sub-step 3.7: BidControls component

**Files to create:**
- `frontend/src/components/auction/BidControls.tsx`

**What:**
Build the 7x5 + Pass/Dbl/Rdbl button grid. Each button is a form submission. Disabled styling for illegal bids. Suit-colored text on bid buttons.

**Verify:** Visual test. Buttons render correctly, disabled state visible.

### Sub-step 3.8: AdvicePanel + ThoughtProcess components

**Files to create:**
- `frontend/src/components/advice/AdvicePanel.tsx`
- `frontend/src/components/advice/ThoughtProcess.tsx`

**What:**
Build advice display components. AdvicePanel shows recommendation + alternatives. ThoughtProcess shows the rule evaluation trace with pass/fail indicators.

**Verify:** Visual test with sample advice data.

### Sub-step 3.9: Practice page + routing (full wiring)

**Files to create:**
- `frontend/src/pages/Practice.tsx`

**Files to modify:**
- `frontend/src/App.tsx` (add practice routes, loader, actions, advice loader)
- `frontend/src/pages/Lobby.tsx` (add practice section with seat picker)

**What:**
Compose all components into the Practice page. Wire up the loader (fetch state), action (bid + redeal), and advice fetcher. Add routes to the router. Add the practice entry point to the Lobby page.

Install any needed shadcn components (Badge, Separator, Tooltip, ScrollArea).

**Verify:** Full end-to-end manual test:
1. `pdm run uvicorn bridge.api.main:app --reload --port 8000`
2. `cd frontend && npm run dev`
3. Register/login
4. Click "Solo Practice", pick seat, start
5. See dealt hand + evaluation + auction
6. Computer bids appear for other seats
7. Click a bid button -- see feedback (match/mismatch)
8. Click "Advise Me" -- see recommendation + thought process
9. Complete an auction -- see all 4 hands + contract
10. Click "New Hand" -- new deal, dealer rotated

### Sub-step 3.10: Final checks + polish

**What:**
- `pdm run check` passes (lint + typecheck + all tests)
- `npm run build` succeeds
- Review responsive behavior at different widths
- Polish spacing, colors, alignment
- Ensure all frontend code has verbose comments (per CLAUDE.md)

### Sub-step 3.11: Keyboard shortcuts for bid selection

**What:**
Keyboard-driven bid highlighting when it's the human's turn. Keys filter the bid grid to help the player find bids quickly without a mouse.

**Behavior:**

| Key | Effect |
|-----|--------|
| `1`-`7` | Highlight all legal bids at that level |
| `C`, `D`, `H`, `S`, `N` | Highlight all legal bids in that suit (N = NT) |
| `P` | Highlight Pass |
| `X` | Highlight Double |

**Combining keys** (sequential, not simultaneous):
- `2` then `H` → highlights just 2H (if legal)
- `2` then `3` → replaces: highlights all legal 3-level bids (level overrides level)
- `H` then `2` → highlights just 2H (if legal)

**Toggle/cancel behavior:**
- Re-entering the same key untoggles that filter. E.g. `2` then `2` → back to default (nothing highlighted). `H` then `H` → back to default.
- This applies to each filter axis independently. E.g. `2` then `H` then `2` → only heart bids highlighted (level filter removed, suit filter remains).

**Special keys:**
- `X` then `X` → first X highlights Double, second X highlights Redouble (if legal). Third X clears.
- `P` then `P` → toggles off, back to default.

**Enter/Space** confirms the highlighted bid if exactly one bid is highlighted.

**Implementation notes:**
- Only active when it's the human's turn (ignore keystrokes otherwise)
- Pure frontend logic — no backend changes needed
- Track two pieces of state: `activeLevel: number | null` and `activeSuit: string | null`
- Highlighted = intersection of active filters applied to legal bids list
- Use `useEffect` with `keydown` listener, clean up on unmount

---

## Open Questions (deferred, not blockers)

These don't need answers now but are noted for future steps:

1. **Session cleanup**: Practice sessions accumulate in memory. Add a TTL or cleanup on logout? (Not critical for solo dev use.)
2. ~~**Keyboard shortcuts**~~: Resolved — see Sub-step 3.11.
3. **Bid-by-bid review**: Step through completed auction seeing engine advice at each point. (Confirmed as a future feature.)
4. **Sound effects**: Subtle audio feedback on bid? (Way later.)
5. **Practice statistics**: Track match rate over time? (Future feature, would need DB persistence.)
