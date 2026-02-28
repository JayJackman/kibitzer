# Phase 2: Web Application — Detailed Implementation Plan

## Overview

Full-stack web application for multiplayer bridge bidding practice. FastAPI backend + React frontend, designed for a friend group learning SAYC together.

Players create accounts, join a shared table, enter their hands, and bid in turn. The "Advise Me" feature provides SAYC-accurate recommendations with thought-process explanations. Solo practice mode lets individual players drill against the engine.

---

## Technology Decisions

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI | Modern Python web framework, native OpenAPI spec, async-capable |
| **Frontend** | React + TypeScript (Vite) | Industry standard for production SPAs, rich ecosystem |
| **UI Components** | shadcn/ui + Tailwind CSS | Beautiful, accessible components. Owned code, not a dependency |
| **State Management** | zustand | Lightweight, excellent WebSocket integration |
| **Data Fetching** | @tanstack/react-query | Caching, loading states, error handling for REST calls |
| **Database** | SQLite + SQLAlchemy | Zero-config, single file, easy to migrate to PostgreSQL later |
| **Auth** | JWT (httpOnly cookies) + bcrypt | Secure, stateless, standard for SPAs |
| **Real-time** | WebSocket (native) | Live auction updates without polling |
| **Type Safety** | openapi-typescript | Auto-generate TS types from FastAPI's OpenAPI spec |
| **Dev Server** | uvicorn (backend) + Vite (frontend) | Hot reload on both sides during development |

---

## Design Principles

- **Desktop-first, mobile usable**: The web app is optimized for laptop/desktop browsers. Mobile browsers will work (responsive layout) but the iOS app (Phase 3) is the intended phone experience.
- **The service layer is the brain**: The API is a thin wrapper around `service.Table`, `service.Lobby`, and `service.BiddingAdvisor`. No business logic in the API layer.
- **Deployment-agnostic**: Works on local network or cloud. No hard-coded URLs, environment-based config.
- **Game state in-memory, users in SQLite**: Active tables live in memory (fast, simple). User accounts persist in SQLite. Game history schema designed but UI deferred.

---

## Project Structure

### Backend

```
src/bridge/api/
    __init__.py
    main.py              # FastAPI app, CORS, lifespan
    config.py            # Settings (SECRET_KEY, DB_URL, etc.)
    deps.py              # Dependency injection (get_db, get_current_user, get_lobby)
    auth/
        __init__.py
        router.py        # POST /register, /login, /logout, GET /me
        models.py        # SQLAlchemy User model
        schemas.py       # Pydantic: RegisterRequest, LoginRequest, UserResponse
        service.py       # create_user, authenticate, hash/verify password
        jwt.py           # create_token, decode_token
    tables/
        __init__.py
        router.py        # Table CRUD + bidding endpoints
        schemas.py       # Pydantic: TableResponse, JoinRequest, BidRequest, etc.
    practice/
        __init__.py
        router.py        # Solo practice endpoints
        schemas.py       # Pydantic: PracticeState, PracticeBidRequest
        session.py       # PracticeSession state management
    ws/
        __init__.py
        handler.py       # WebSocket connection manager
        events.py        # Event types (player_joined, bid_made, etc.)
    db.py                # SQLAlchemy engine, session factory, Base
```

### Frontend

```
frontend/
    package.json
    vite.config.ts
    tsconfig.json
    tailwind.config.ts
    index.html
    src/
        main.tsx
        App.tsx              # Router setup
        api/
            client.ts        # Axios/fetch wrapper with auth
            types.ts         # Auto-generated from OpenAPI
            endpoints.ts     # Typed API functions
        components/
            ui/              # shadcn base components (Button, Card, Input, Dialog, etc.)
            hand/
                HandDisplay.tsx      # 13 cards arranged by suit
                CardRow.tsx          # Single suit row (symbol + ranks)
            auction/
                AuctionGrid.tsx      # 4-column bid history
                BidControls.tsx      # Bid input (buttons + grid)
                ContractDisplay.tsx  # Final contract summary
            advice/
                AdvicePanel.tsx      # Recommended bid + explanation
                ThoughtProcess.tsx   # Condition trace display
                AlternativesPanel.tsx
            layout/
                AppLayout.tsx        # Navigation, auth status
        hooks/
            useAuth.ts           # Login state, token management
            useWebSocket.ts      # WebSocket connection + events
            useTable.ts          # Table state subscription
            usePractice.ts       # Practice session state
        pages/
            Login.tsx
            Register.tsx
            Lobby.tsx
            Table.tsx
            Practice.tsx
        store/
            authStore.ts         # User session state
            tableStore.ts        # Live table state (from WebSocket)
        lib/
            utils.ts             # Tailwind cn() helper, formatters
            constants.ts         # Suit symbols, colors, seat labels
```

---

## New Dependencies

### Python (backend)

```toml
[project.dependencies]
fastapi = ">=0.110"
uvicorn = {extras = ["standard"], version = ">=0.27"}
sqlalchemy = ">=2.0"
passlib = {extras = ["bcrypt"], version = ">=1.7"}
python-jose = {extras = ["cryptography"], version = ">=3.3"}
python-multipart = ">=0.0.9"
```

### Frontend (pnpm)

```json
{
  "dependencies": {
    "react": "^19",
    "react-dom": "^19",
    "react-router-dom": "^7",
    "@tanstack/react-query": "^5",
    "zustand": "^5",
    "axios": "^1",
    "clsx": "^2",
    "tailwind-merge": "^2"
  },
  "devDependencies": {
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "typescript": "^5",
    "vite": "^6",
    "@vitejs/plugin-react": "^4",
    "tailwindcss": "^4",
    "postcss": "^8",
    "autoprefixer": "^10",
    "openapi-typescript": "^7"
  }
}
```

---

## API Endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account (username, password) |
| POST | `/api/auth/login` | Authenticate, set access + refresh cookies |
| POST | `/api/auth/logout` | Clear both cookies |
| POST | `/api/auth/refresh` | Exchange refresh token for new access token |
| GET | `/api/auth/me` | Current user info |

### Lobby & Tables

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tables` | List all tables with status |
| POST | `/api/tables` | Create a new table |
| GET | `/api/tables/{id}` | Get table state (filtered to your seat) |
| DELETE | `/api/tables/{id}` | Delete a table |
| POST | `/api/tables/{id}/join` | Join a seat `{seat: "N"}` |
| POST | `/api/tables/{id}/leave` | Leave your seat |
| POST | `/api/tables/{id}/hand` | Set your hand `{hand: "AKJ52.KQ3.84.A73"}` |
| POST | `/api/tables/{id}/bid` | Make a bid `{bid: "1H"}` |
| GET | `/api/tables/{id}/advise` | Get bid advice for your seat |
| POST | `/api/tables/{id}/reset` | Reset for next hand |

### Practice

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/practice` | Create practice session `{seat: "N"}` |
| GET | `/api/practice/{id}` | Get practice state (filtered to your seat) |
| POST | `/api/practice/{id}/join` | Join a seat `{seat: "S"}` |
| POST | `/api/practice/{id}/leave` | Leave your seat (computer takes over) |
| POST | `/api/practice/{id}/bid` | Make a bid |
| GET | `/api/practice/{id}/advise` | Get advice for your seat |
| POST | `/api/practice/{id}/redeal` | Deal new hands (host only) |

### WebSocket

| Path | Description |
|------|-------------|
| WS `/api/tables/{id}/ws` | Live table updates |
| WS `/api/practice/{id}/ws` | Live practice updates (multi-player) |

#### WebSocket Events (server -> client)

```typescript
type WSEvent =
    | { type: "player_joined"; seat: Seat; username: string }
    | { type: "player_left"; seat: Seat }
    | { type: "hand_set"; seat: Seat }           // no hand data (private)
    | { type: "bid_made"; seat: Seat; bid: string }
    | { type: "auction_complete"; contract: Contract }
    | { type: "table_reset" }
    | { type: "error"; message: string }
```

---

## Auth System

### User Model (SQLAlchemy)

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### JWT Flow

Two tokens, both stored as httpOnly cookies:

- **Access token** — short-lived (15 minutes). Sent with every API request to identify the user.
- **Refresh token** — long-lived (7 days). Used only to get a new access token when the old one expires.

Flow:

1. User registers -> password hashed with bcrypt, stored in SQLite
2. User logs in -> credentials verified, both tokens issued as httpOnly cookies
3. Each API request -> middleware reads access token cookie, decodes JWT, injects current user
4. Access token expires -> frontend gets 401, automatically calls `/api/auth/refresh`
5. Refresh endpoint -> verifies refresh token, issues new access token (user never notices)
6. Refresh token expires -> user must log in again (happens after 7 days of inactivity)
7. Logout -> both cookies cleared

Token payload: `{"sub": username, "exp": expiry, "type": "access" | "refresh"}`.

### Config

Environment variables (with defaults for development):

```python
class Settings(BaseModel):
    secret_key: str = "dev-secret-change-in-production"
    database_url: str = "sqlite:///./bridge.db"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = ["http://localhost:5173"]
```

---

## Database Schema

### Initial (users only)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Future (game history — schema designed, not built)

```sql
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id TEXT NOT NULL,
    dealer TEXT NOT NULL,           -- N/E/S/W
    vulnerability TEXT NOT NULL,    -- None/NS/EW/Both
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE game_hands (
    game_id INTEGER REFERENCES games(id),
    seat TEXT NOT NULL,
    hand_pbn TEXT NOT NULL,        -- "AKJ52.KQ3.84.A73"
    user_id INTEGER REFERENCES users(id),
    PRIMARY KEY (game_id, seat)
);

CREATE TABLE game_bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES games(id),
    seat TEXT NOT NULL,
    bid TEXT NOT NULL,              -- "1H", "P", "X", "XX"
    sequence_num INTEGER NOT NULL
);
```

---

## UI Screens

### Login / Register

Mobile-first form. Username + password. Toggle between login and register. Error messages for duplicate username, wrong password, etc.

### Lobby

List of tables showing:
- Table name/ID
- Status (waiting / in progress / completed)
- Who's seated where (4 seat indicators)
- "Join" button

"Create Table" button at the top.

### Table (Main Screen)

The core experience. Desktop layout (side-by-side):

```
+--------------------+------------------------+
|  [Table Name]      |  AUCTION               |
|  N(Alice) E(--)    |  W     N     E     S   |
|  S(Bob)   W(--)    |        1H   Pass    ?  |
+--------------------+------------------------+
|                    |  BID CONTROLS           |
|  YOUR HAND         |  [Pass] [Dbl] [Rdbl]  |
|  S: A K J 5 2      |  [1C][1D][1H][1S][1NT]|
|  H: K Q 3          |  [2C][2D][2H][2S][2NT]|
|  D: 8 4            |  ...                   |
|  C: A 7 3          |                        |
|                    |  [Advise Me]           |
|  HCP: 15  Pts: 16  |                        |
|  Shape: 5332       |                        |
+--------------------+------------------------+
```

On narrow screens (mobile), this stacks vertically (hand on top, auction + controls below). The layout will be responsive but not specifically optimized for mobile — the iOS app (Phase 3) is the intended phone experience.

### Advice Panel (expandable)

When "Advise Me" is tapped:

```
+-----------------------------------+
|  RECOMMENDED: 1S                  |
|  5+ spades, new suit at 1-level   |
|  (forcing one round)              |
+-----------------------------------+
|  THOUGHT PROCESS                  |
|  * Partner opened 1 of a suit     |
|  * You have 15 HCP (6+ required)  |
|  * Found spades (4+ suit at 1-level)|
+-----------------------------------+
|  ALTERNATIVES                     |
|  2H - Single raise (too strong)   |
|  2NT - 13-15 balanced (have major)|
+-----------------------------------+
```

### Practice Mode

Same table UI, but the server deals all hands and the computer bids for any seat without a human player. Supports 1-4 human players:

- **Solo (1 player)**: Bidding quiz — you bid, computer handles the other 3 seats.
- **Partnership (2 players)**: Two friends practice as a partnership (e.g., N/S), computer bids E/W.
- **3-4 players**: Everyone practices together, computer fills any empty seats.

How it works:
- Host creates a practice session and picks their seat
- Other players can join remaining seats (or leave them for the computer)
- Server deals random hands — each player sees only their own
- Computer auto-bids for unoccupied seats using the engine
- "Advise Me" available for all human seats
- After each bid: shows if you matched the engine recommendation
- "New Hand" button to redeal (available to the host)

### Hand Input

For multiplayer, players need to enter their hand. Options:
- Single text input (PBN format): `AKJ52.KQ3.84.A73`
- Four suit fields: one input per suit (S/H/D/C), tab between them, enter to submit
- Visual card picker (stretch goal): tap cards from a 52-card grid

Decision deferred to implementation time. Start with whichever feels best.

---

## Practice Mode Architecture

Practice sessions are server-side (the engine is Python-only) and support 1-4 human players. The computer bids for any seat without a human player.

```python
class PracticeSession:
    id: str
    host_user_id: int                          # Who created the session
    players: dict[Seat, int | None]            # Seat -> user_id or None (computer)
    hands: dict[Seat, Hand]                    # All 4 hands (dealt by server)
    auction: AuctionState
    advisor: BiddingAdvisor

    def join(self, seat: Seat, user_id: int) -> None:
        """A player joins a seat. Raises if seat is occupied by another human."""

    def leave(self, seat: Seat) -> None:
        """A player leaves. Seat reverts to computer control."""

    def computer_bids(self) -> list[tuple[Seat, Bid]]:
        """Auto-bid for computer seats until it's a human player's turn."""

    def player_bid(self, seat: Seat, bid: Bid) -> PracticeBidResult:
        """Record a human player's bid, return whether it matched the engine."""

    def get_advice(self, seat: Seat) -> BiddingAdvice:
        """Get engine recommendation for a human player's seat."""

    def redeal(self) -> None:
        """Deal new hands, reset auction. All seat assignments kept."""
```

Practice sessions are stored in-memory (dict keyed by session ID). With multiple human players, practice sessions use WebSocket for real-time updates (same infrastructure as multiplayer tables). Solo sessions (1 player) can use simple request/response.

---

## WebSocket Architecture

### Connection Manager

```python
class ConnectionManager:
    """Manages WebSocket connections per table."""

    def __init__(self) -> None:
        self._connections: dict[str, dict[str, WebSocket]] = {}
        # table_id -> {username -> websocket}

    async def connect(self, table_id: str, username: str, ws: WebSocket) -> None
    async def disconnect(self, table_id: str, username: str) -> None
    async def broadcast(self, table_id: str, event: WSEvent) -> None
    async def send_to(self, table_id: str, username: str, event: WSEvent) -> None
```

### Flow

1. Player opens Table page -> connects WebSocket
2. Player joins seat -> server broadcasts `player_joined` to all
3. Player sets hand -> server broadcasts `hand_set` (no hand data) to all
4. Player bids -> server broadcasts `bid_made` to all
5. Auction completes -> server broadcasts `auction_complete` to all
6. Player disconnects -> server broadcasts `player_left`

REST endpoints handle the actual mutations (join, bid, etc.). WebSocket is notification-only (server -> client). This keeps the architecture simple — REST for writes, WebSocket for push notifications.

---

## Implementation Steps

### Step 1: Backend Foundation

**Goal**: FastAPI app running with auth endpoints and database.

Files to create:
- `src/bridge/api/__init__.py`
- `src/bridge/api/main.py` — FastAPI app with CORS, lifespan (create tables on startup)
- `src/bridge/api/config.py` — Settings class
- `src/bridge/api/db.py` — SQLAlchemy engine, session, Base
- `src/bridge/api/deps.py` — `get_db`, `get_current_user`, `get_lobby`
- `src/bridge/api/auth/__init__.py`
- `src/bridge/api/auth/models.py` — User SQLAlchemy model
- `src/bridge/api/auth/schemas.py` — Pydantic request/response models
- `src/bridge/api/auth/service.py` — create_user, authenticate, password hashing
- `src/bridge/api/auth/jwt.py` — create_token, decode_token
- `src/bridge/api/auth/router.py` — register, login, logout, me endpoints

Tests:
- `tests/api/__init__.py`
- `tests/api/test_auth.py` — registration, login, logout, me, duplicate username, wrong password

Verification:
- `pdm run check` passes
- `curl POST /api/auth/register` creates a user
- `curl POST /api/auth/login` returns JWT cookie
- `curl GET /api/auth/me` returns user info with valid cookie

---

### Step 2: Frontend Foundation

**Goal**: React app with login/register, talking to the backend.

Setup:
- Initialize Vite + React + TypeScript in `frontend/`
- Install and configure Tailwind CSS
- Install and configure shadcn/ui (Button, Card, Input, Label, etc.)
- Set up React Router (Login, Register, Lobby, Table, Practice routes)
- Set up openapi-typescript for type generation
- Create API client with auth (cookie-based)

Files to create:
- `frontend/` — full Vite project scaffold
- `frontend/src/api/client.ts` — axios instance with cookie handling
- `frontend/src/api/endpoints.ts` — typed API call functions
- `frontend/src/hooks/useAuth.ts` — auth state management
- `frontend/src/store/authStore.ts` — zustand store for user session
- `frontend/src/pages/Login.tsx` — login form
- `frontend/src/pages/Register.tsx` — registration form
- `frontend/src/components/layout/AppLayout.tsx` — nav + auth status
- `frontend/src/App.tsx` — router setup with protected routes
- `frontend/src/lib/utils.ts` — cn() helper
- `frontend/src/lib/constants.ts` — suit symbols, colors

Verification:
- `pnpm run dev` starts frontend on port 5173
- Register a new user, login, see the lobby (empty for now)
- Auth state persists across page refreshes (cookie)

---

### Step 3: Practice Mode (Web)

**Goal**: Playable practice mode in the browser (1-4 players). This proves the entire UI stack.

Backend:
- `src/bridge/api/practice/__init__.py`
- `src/bridge/api/practice/session.py` — PracticeSession class (supports 1-4 human players)
- `src/bridge/api/practice/router.py` — create, join, leave, bid, advise, redeal endpoints
- `src/bridge/api/practice/schemas.py` — request/response models

Frontend:
- `frontend/src/pages/Practice.tsx` — practice mode page
- `frontend/src/hooks/usePractice.ts` — practice state management
- `frontend/src/components/hand/HandDisplay.tsx` — card layout by suit
- `frontend/src/components/hand/CardRow.tsx` — single suit row
- `frontend/src/components/auction/AuctionGrid.tsx` — 4-column bid table
- `frontend/src/components/auction/BidControls.tsx` — bid buttons/grid
- `frontend/src/components/advice/AdvicePanel.tsx` — recommendation display
- `frontend/src/components/advice/ThoughtProcess.tsx` — condition trace
- `frontend/src/components/advice/AlternativesPanel.tsx` — alternative bids

Tests:
- `tests/api/test_practice.py` — practice session lifecycle (solo and multi-player)

Verification:
- Start practice solo, see dealt hand, computer bids other seats
- Enter a bid, see if it matches the engine
- "Advise Me" shows recommendation with thought process
- "New Hand" redeals
- Second player joins a seat, both can bid and get advice

---

### Step 4: Multiplayer — Lobby

**Goal**: Create and browse tables.

Backend:
- `src/bridge/api/tables/__init__.py`
- `src/bridge/api/tables/router.py` — list, create, delete tables
- `src/bridge/api/tables/schemas.py` — TableResponse, TableSummaryResponse

Frontend:
- `frontend/src/pages/Lobby.tsx` — table list with create button
- `frontend/src/store/tableStore.ts` — zustand store for table state

Tests:
- `tests/api/test_tables.py` — table CRUD

Verification:
- Create a table from the lobby
- See it listed with "waiting" status
- Delete a table

---

### Step 5: Multiplayer — Table

**Goal**: Full table interaction via REST (no WebSocket yet — manual refresh).

Backend:
- Extend `src/bridge/api/tables/router.py` — join, leave, hand, bid, advise, reset, get state

Frontend:
- `frontend/src/pages/Table.tsx` — full table UI
- `frontend/src/hooks/useTable.ts` — table state + polling fallback
- `frontend/src/components/auction/ContractDisplay.tsx` — final contract

Tests:
- Extend `tests/api/test_tables.py` — join, bid, complete auction

Verification:
- Two browser windows, two users
- Both join the same table (different seats)
- Enter hands, bid in turn (refresh to see updates)
- Auction completes, contract shown
- Reset for next hand

---

### Step 6: WebSocket Real-time

**Goal**: Live updates without manual refresh.

Backend:
- `src/bridge/api/ws/__init__.py`
- `src/bridge/api/ws/handler.py` — ConnectionManager
- `src/bridge/api/ws/events.py` — event type definitions
- Wire WebSocket into table router

Frontend:
- `frontend/src/hooks/useWebSocket.ts` — WebSocket connection manager
- Update `useTable.ts` to use WebSocket for live state updates
- Update Table page to reflect incoming events in real-time

Tests:
- `tests/api/test_ws.py` — WebSocket connection, event broadcast

Verification:
- Two browser windows on the same table
- One player bids -> other player sees the bid instantly (no refresh)
- Player joins/leaves -> others notified
- Auction completes -> all players see the contract

---

### Step 7: Polish

**Goal**: Production-quality UX.

- Loading states (spinners, skeleton screens)
- Error handling (network errors, expired tokens, server errors)
- Toast notifications for events
- Desktop polish:
  - Clean side-by-side layout (hand + auction)
  - Keyboard shortcuts for common bids
  - Hover states, tooltips
- Responsive fallback for mobile browsers (stacked layout, usable but not the primary target)
- Accessibility (ARIA labels, focus management, screen reader support)

---

## Development Workflow

### Running locally

```bash
# Terminal 1: Backend
pdm run uvicorn bridge.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && pnpm run dev
```

Vite dev server proxies `/api` to `localhost:8000` (configured in `vite.config.ts`).

### Type generation

```bash
# After changing API schemas:
cd frontend && pnpm run generate-types
# Reads from http://localhost:8000/openapi.json
# Writes to src/api/types.ts
```

### Production build

```bash
cd frontend && pnpm run build
# Output: frontend/dist/

# FastAPI serves static files from frontend/dist/
# Single process serves both API and frontend
```

---

## Serving in Production

FastAPI serves the built frontend as static files:

```python
# In main.py, after all API routes:
app.mount("/", StaticFiles(directory="frontend/dist", html=True))
```

This means a single `uvicorn` process serves everything — no separate web server needed. Works for both local network and cloud deployment.

---

## Verification

After each step:
- `pdm run check` passes (backend)
- `pnpm run build` succeeds (frontend, after Step 2)
- Manual testing against the verification criteria listed per step

After full Phase 2:
- Register, login, see lobby
- Create a table, join a seat, enter a hand, bid
- Two players can bid in real-time on the same table
- Solo practice works end-to-end
- Desktop layout is clean and polished
- Mobile browsers can use the app (responsive fallback)
