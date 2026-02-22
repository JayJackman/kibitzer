# Phase 0: Foundation Layer

## Goal

Build the shared service layer that all UIs (CLI, web, iOS, desktop) will consume. This includes the bidding advisor, table/session management, lobby, input parsing, and random deal generation.

After Phase 0, the engine's capabilities are fully exposed through a clean service API. No UI yet — that's Phase 1+.

---

## Existing Interfaces (What We're Building On)

### Engine Pipeline (current)

The engine works through this call chain:

```python
# 1. Build a Board (hand + seat + auction)
board = Board(hand=Hand.from_pbn("AKJ52.KQ3.84.A73"), seat=Seat.NORTH, auction=auction)

# 2. Create a BiddingContext (pre-computes all hand metrics)
ctx = BiddingContext(board)

# 3. Run the selector (detects phase, picks highest-priority matching rule)
registry = create_sayc_registry()
selector = BidSelector(registry)
result = selector.select(ctx)       # -> RuleResult (single best bid)
candidates = selector.candidates(ctx)  # -> list[RuleResult] (all matching rules)
```

Key types:
- `Board` — frozen dataclass: `hand: Hand`, `seat: Seat`, `auction: AuctionState`
- `BiddingContext` — pre-computes: `hcp`, `length_pts`, `total_pts`, `distribution_pts`, `controls`, `quick_tricks`, `losers`, `shape`, `sorted_shape`, `is_balanced`, `is_semi_balanced`, `longest_suit`, plus auction convenience fields
- `BidSelector.select(ctx)` -> `RuleResult` (bid, rule_name, explanation, alerts, forcing)
- `BidSelector.candidates(ctx)` -> `list[RuleResult]` (all matching, not just winner)
- `BidSelector.detect_phase(ctx)` -> `Category` (OPENING, RESPONSE, REBID_OPENER, etc.)

### Hand Parsing (current)

Three formats already supported:
- `Hand.from_pbn("AKJ52.KQ3.84.A73")` — S.H.D.C dot-separated
- `Hand.from_labeled("S:AKJ52 H:KQ3 D:84 C:A73")` — suit-labeled
- `Hand.from_compact("SAKJ52HKQ3D84CA73")` — no separators

### Bid Parsing (current)

`parse_bid(text)` handles: `"Pass"`, `"P"`, `"X"`, `"XX"`, `"1C"`, `"1NT"`, `"3H"`, `"7NT"`, etc. Case-insensitive.

### AuctionState (current)

Mutable state tracker:
- `dealer: Seat`, `vulnerability: Vulnerability`
- `add_bid(bid)` — validates legality, raises `IllegalBidError`
- `current_seat` — whose turn it is (derived from dealer + bid count)
- `is_complete` — 3 passes after a non-pass, or 4 initial passes
- `bids` — list of `(Seat, Bid)` pairs
- `opening_bid`, `has_opened`, `partner_last_bid(seat)`, `rho_last_bid(seat)`, `bids_by(seat)`, `is_competitive()`
- `last_contract_bid` — most recent SuitBid (the current contract if auction ends)

### Evaluate Functions (current)

All in `bridge.evaluate`:
- `hcp(hand)`, `length_points(hand)`, `total_points(hand)`
- `distribution_points(hand, trump_suit=None)`, `support_points(hand, trump_suit)`
- `bergen_points(hand, trump_suit)`
- `controls(hand)`, `quick_tricks(hand)`, `losing_trick_count(hand)`
- `quality_suit(hand, suit)`, `has_stopper(hand, suit)`
- `best_major(hand)`, `best_minor(hand)`
- `rule_of_20(hand, hcp)`, `rule_of_15(hand, hcp)`
- `has_outside_four_card_major(hand, exclude)`

---

## 0A: Service/Advisor Layer

**File:** `src/bridge/service/advisor.py`

### BiddingAdvisor

Wraps the engine pipeline into a single call. This is the entry point that all UIs use for bid advice.

```python
class BiddingAdvisor:
    """Provides bid recommendations using the SAYC rule engine."""

    def __init__(self) -> None:
        registry = create_sayc_registry()
        self._selector = BidSelector(registry)

    def advise(self, hand: Hand, auction: AuctionState) -> BiddingAdvice:
        """Get a bid recommendation for the given hand and auction state.

        The seat is inferred from auction.current_seat.
        """
```

Implementation:
1. Build a `Board` from `hand`, `auction.current_seat`, and `auction`
2. Create a `BiddingContext` from the board
3. Call `self._selector.select(ctx)` for the recommended bid
4. Call `self._selector.candidates(ctx)` for alternatives (exclude the winner)
5. Call `self._selector.detect_phase(ctx)` for the phase (cheap call — just auction state checks; duplicates what `select()` does internally, but needed to populate the `BiddingAdvice.phase` field for the UI)
6. Build a `HandEvaluation` from the context's pre-computed metrics
7. Return a `BiddingAdvice` bundling all of the above

### BiddingAdvice

**File:** `src/bridge/service/models.py`

```python
@dataclass(frozen=True)
class BiddingAdvice:
    recommended: RuleResult
    alternatives: list[RuleResult]
    hand_evaluation: HandEvaluation
    phase: Category
```

### HandEvaluation

Bundles all computed metrics in a UI-friendly structure. Built from `BiddingContext` fields.

```python
@dataclass(frozen=True)
class HandEvaluation:
    hcp: int
    length_points: int
    total_points: int
    distribution_points: int
    controls: int
    quick_tricks: float
    losers: int
    shape: tuple[int, int, int, int]         # S-H-D-C order
    sorted_shape: tuple[int, ...]            # descending
    is_balanced: bool
    is_semi_balanced: bool
    longest_suit: Suit
```

Note: `support_points` and `bergen_points` are context-dependent (need a trump suit), so they are NOT in the base `HandEvaluation`. The advisor could add them when relevant (e.g., when raising partner's suit), but that's a future enhancement.

### Design Decisions

- **Seat is not a parameter.** The advisor infers it from `auction.current_seat`. This avoids mismatches where someone passes the wrong seat.
- **The advisor is stateless.** It takes a hand + auction and returns advice. The `Table` class (0B) manages state.
- **One advisor instance per app.** The registry is created once. `advise()` can be called many times.
- **Alternatives exclude the winner.** If `candidates()` returns `[1S, 2H, Pass]` and the winner is `1S`, alternatives = `[2H, Pass]`.

---

## 0B: Table/Session Management

**File:** `src/bridge/service/table.py`

### Table

Manages the stateful game session for a live auction.

```python
@dataclass
class Player:
    name: str

class TableStatus(StrEnum):
    WAITING = "waiting"           # waiting for players/hands
    IN_PROGRESS = "in_progress"   # auction underway
    COMPLETED = "completed"       # auction finished

class Table:
    id: str
    seats: dict[Seat, Player | None]
    hands: dict[Seat, Hand | None]
    auction: AuctionState
    status: TableStatus
    _advisor: BiddingAdvisor
```

### Methods

```python
def join(self, seat: Seat, player: Player) -> None:
    """Claim a seat. Raises if seat is occupied."""

def leave(self, seat: Seat) -> None:
    """Vacate a seat. Raises if seat is empty."""

def set_hand(self, seat: Seat, hand: Hand) -> None:
    """Set the hand for a seat.

    Raises if:
    - Seat is unoccupied
    - Auction is in progress
    - Any card in the hand duplicates a card in another seat's hand
      (error message names which seats conflict, but NOT which cards,
      to avoid leaking hand information — players must re-check and
      re-enter their hands)
    """

def make_bid(self, seat: Seat, bid: Bid, player: Player) -> None:
    """Place a bid for a seat.

    Authorization:
    - If seat has a player assigned and player == that player -> allowed (own bid)
    - If seat has no player assigned -> allowed (proxy bid for empty seat)
    - If seat has a player assigned and player != that player -> rejected

    Validates:
    - It's this seat's turn (auction.current_seat == seat)
    - The bid is legal (delegated to AuctionState.add_bid)
    - The player is seated somewhere at the table

    After the bid:
    - If auction.is_complete, set status to COMPLETED
    """

def get_state(self, seat: Seat) -> TableView:
    """Return a filtered view for a specific seat.

    Shows: your hand (only), all seat assignments, full auction,
    whose turn it is, contract result if complete.
    """

def get_advice(self, seat: Seat) -> BiddingAdvice:
    """Get bid advice for a seat.

    Raises if:
    - No hand set for this seat
    - It's not this seat's turn
    - Auction is complete
    """

def reset(self) -> None:
    """Clear hands and auction for a new deal. Keep seat assignments."""
```

### TableView

What a client sees — no other players' hands.

```python
@dataclass(frozen=True)
class TableView:
    seat: Seat
    hand: Hand | None
    seats: dict[Seat, str | None]     # seat -> player name or None
    bids: list[tuple[Seat, Bid]]      # full auction history
    current_seat: Seat                 # whose turn
    is_complete: bool
    contract: Contract | None          # set when auction completes
    status: TableStatus
```

### Contract

Derived when the auction completes.

```python
@dataclass(frozen=True)
class Contract:
    level: int              # 1-7
    suit: Suit              # including NOTRUMP
    declarer: Seat          # who plays
    doubled: bool
    redoubled: bool
    passed_out: bool        # True if all 4 passed (no contract)
```

The `declarer` is the first player on the declaring side who bid the contract suit. This requires scanning the auction history. If `passed_out` is True, the other fields are meaningless.

#### Deriving the Contract

When `auction.is_complete`:
1. If all 4 bids were passes -> `Contract(passed_out=True, ...)`
2. Otherwise, find `auction.last_contract_bid` (the final SuitBid)
3. Find who bid that suit first on the declaring side
4. Check `auction.is_doubled` and `auction.is_redoubled` (already public properties)

To find the declarer, scan the auction history for the first player on the declaring side who bid the contract suit. `AuctionState` already has `bids` (list of seat-bid pairs) and `opening_bid`, so this is straightforward.

**Decision:** Add a `contract` property to `AuctionState` that returns a `Contract` when the auction is complete (None otherwise). The `Contract` dataclass lives in `model/` (not service/) since it's pure auction-derived data. This also means `AuctionState` tests cover contract derivation.

---

## 0C: Lobby Management

**File:** `src/bridge/service/lobby.py`

### Lobby

Manages tables. For now, a single in-memory instance with one table. Infrastructure supports N tables.

```python
class Lobby:
    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    def create_table(self) -> Table:
        """Create a new table with a unique ID."""

    def get_table(self, table_id: str) -> Table:
        """Get a table by ID. Raises if not found."""

    def list_tables(self) -> list[TableSummary]:
        """List all tables with summary info."""

    def delete_table(self, table_id: str) -> None:
        """Remove a table. Raises if not found."""
```

### TableSummary

Lightweight view for the lobby list.

```python
@dataclass(frozen=True)
class TableSummary:
    id: str
    status: TableStatus
    seats: dict[Seat, str | None]    # seat -> player name or None
    num_players: int
```

### Design Decisions

- **In-memory only.** No database, no persistence. If the server restarts, state is lost. This is fine for the initial use case (friends at a table). Persistence can be added later.
- **Table IDs:** Use short random strings (e.g., 6-char alphanumeric). Could use `secrets.token_urlsafe(4)` or similar.
- **One lobby instance per app.** Created at startup, shared across all requests.

---

## 0D: Auction Input Parsing

**File:** `src/bridge/model/auction.py` (add to existing file)

### parse_auction

Builds an `AuctionState` from a space-separated string of bids.

```python
def parse_auction(text: str, dealer: Seat = Seat.NORTH,
                  vulnerability: Vulnerability | None = None) -> AuctionState:
    """Parse an auction string into an AuctionState.

    Args:
        text: Space-separated bid strings, e.g. "1H P 2H P"
        dealer: Who dealt (default North)
        vulnerability: Optional vulnerability state

    Returns:
        AuctionState with all bids added.

    Raises:
        ValueError: If any bid string is invalid
        IllegalBidError: If any bid is illegal in sequence

    Examples:
        parse_auction("1H P 2H P")
        parse_auction("1H P 1S P 2H", dealer=Seat.EAST)
        parse_auction("")  # empty auction, dealer's turn
    """
```

Implementation:
1. Create `AuctionState(dealer=dealer, vulnerability=vulnerability or Vulnerability())`
2. Split text on whitespace, skip empty
3. For each token, call `parse_bid(token)` then `auction.add_bid(bid)`
4. Return the auction

This uses the existing `parse_bid()` function which already handles all bid formats (`P`, `Pass`, `X`, `XX`, `1C`, `1NT`, etc.).

### Where to put it

Add `parse_auction` to `auction.py` alongside `AuctionState`. Export it from `model/__init__.py`.

---

## 0E: Random Deal Generator

**File:** `src/bridge/service/deal.py`

### deal

Shuffles a standard 52-card deck and deals 4 hands of 13 cards.

```python
import random
from bridge.model.card import Card, Rank, Suit, SUITS_SHDC
from bridge.model.hand import Hand
from bridge.model.auction import Seat

def deal(rng: random.Random | None = None) -> dict[Seat, Hand]:
    """Deal 52 cards into 4 hands of 13.

    Args:
        rng: Optional random.Random instance for reproducible deals.
             If None, uses the default random module.

    Returns:
        Dict mapping each Seat to a Hand.
    """
```

Implementation:
1. Build the full 52-card deck: `[Card(suit, rank) for suit in SUITS_SHDC for rank in Rank]`
   - Note: `SUITS_SHDC` has 4 suits (no NOTRUMP). `Rank` has 13 values (2-A). Total: 52.
2. Shuffle with `rng.shuffle(deck)` or `random.shuffle(deck)`
3. Split into 4 groups of 13
4. Map to `{Seat.NORTH: Hand(frozenset(deck[0:13])), ...}`

### Design Decisions

- **Accepts an RNG** for testability and reproducibility. Tests can pass `random.Random(42)` for deterministic deals.
- **No NOTRUMP in deck.** `SUITS_SHDC` is `(SPADES, HEARTS, DIAMONDS, CLUBS)` — the 4 physical suits. This is correct.
- **Returns `dict[Seat, Hand]`.** The table's `set_hand()` can be called for each seat.

---

## Files to Create

| File | Contents |
|------|----------|
| `src/bridge/service/models.py` | `HandEvaluation`, `BiddingAdvice`, `Player`, `TableStatus`, `TableView`, `TableSummary` |
| `src/bridge/service/advisor.py` | `BiddingAdvisor` |
| `src/bridge/service/table.py` | `Table` |
| `src/bridge/service/lobby.py` | `Lobby` |
| `src/bridge/service/deal.py` | `deal()` |
| `tests/service/__init__.py` | (empty) |
| `tests/service/test_advisor.py` | Tests for `BiddingAdvisor.advise()` |
| `tests/service/test_table.py` | Tests for `Table` (join, leave, bid, state, advice, reset) |
| `tests/service/test_lobby.py` | Tests for `Lobby` (create, get, list, delete) |
| `tests/service/test_deal.py` | Tests for `deal()` |
| `tests/model/test_parse_auction.py` | Tests for `parse_auction()` |

## Files to Modify

| File | Change |
|------|--------|
| `src/bridge/model/auction.py` | Add `Contract` dataclass, `contract` property on `AuctionState`, `parse_auction()` function (`is_doubled`/`is_redoubled` already made public) |
| `src/bridge/model/__init__.py` | Export `Contract`, `parse_auction` |
| `src/bridge/service/__init__.py` | Export public API: `BiddingAdvisor`, `BiddingAdvice`, `HandEvaluation`, `Table`, `Lobby`, etc. |

---

## Implementation Order

### Step 1: Models (`service/models.py`)

All the dataclasses/enums that the rest of Phase 0 depends on. No logic, just types:
- `Player`
- `TableStatus`
- `HandEvaluation`
- `BiddingAdvice`
- `Contract`
- `TableView`
- `TableSummary`

### Step 2: Contract derivation + AuctionState changes

- Make `_is_doubled` / `_is_redoubled` public on `AuctionState`
- Add contract derivation logic (either on AuctionState or as a standalone function)
- Tests for contract derivation

### Step 3: parse_auction (`model/auction.py`)

- Add `parse_auction()` to `auction.py`
- Export from `model/__init__.py`
- Tests in `tests/model/test_parse_auction.py`

### Step 4: deal (`service/deal.py`)

- Implement `deal()` with RNG parameter
- Tests: 4 hands of 13, no duplicates, all 52 cards present, deterministic with seed

### Step 5: BiddingAdvisor (`service/advisor.py`)

- Implement `BiddingAdvisor.advise()`
- Tests: known hands produce expected advice (reuse some from `test_sayc.py` integration tests)
- Verify: recommended bid matches `selector.select()`, alternatives match `selector.candidates()` minus winner

### Step 6: Table (`service/table.py`)

- Implement `Table` with all methods
- Tests:
  - Join/leave seats
  - Set hands
  - Make bids (valid turn, invalid turn, proxy for unoccupied seat)
  - get_state returns only your hand
  - get_advice works when it's your turn
  - reset clears hands/auction, keeps seats
  - Status transitions: WAITING -> IN_PROGRESS -> COMPLETED
  - Contract shown when auction completes

### Step 7: Lobby (`service/lobby.py`)

- Implement `Lobby`
- Tests: create, get, list, delete tables

### Step 8: Exports + Integration

- Wire up `service/__init__.py`
- `pdm run check` — lint + typecheck + test

---

## Test Plan

### test_advisor.py

```python
class TestBiddingAdvisor:
    def test_advise_opening_hand(self):
        """15 HCP balanced -> recommended 1NT, phase OPENING."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AK32.KQ3.J84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        advice = advisor.advise(hand, auction)
        assert advice.recommended.bid == SuitBid(1, Suit.NOTRUMP)
        assert advice.phase == Category.OPENING
        assert advice.hand_evaluation.hcp == 15
        assert advice.hand_evaluation.is_balanced

    def test_advise_response_hand(self):
        """Response to 1H with 15 HCP and 5 spades -> 1S."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AKJ52.Q73.84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(PASS)
        advice = advisor.advise(hand, auction)
        assert advice.recommended.bid == SuitBid(1, Suit.SPADES)
        assert advice.phase == Category.RESPONSE

    def test_advise_includes_alternatives(self):
        """Alternatives list is populated and excludes the winner."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AKJ52.Q73.84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(PASS)
        advice = advisor.advise(hand, auction)
        assert len(advice.alternatives) > 0
        winner_name = advice.recommended.rule_name
        assert all(alt.rule_name != winner_name for alt in advice.alternatives)

    def test_advise_hand_evaluation_populated(self):
        """HandEvaluation has all expected fields."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AK32.KQ3.J84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        advice = advisor.advise(hand, auction)
        ev = advice.hand_evaluation
        assert ev.hcp == 15
        assert ev.shape == (4, 3, 3, 3)
        assert ev.is_balanced
        assert ev.quick_tricks > 0
```

### test_table.py

```python
class TestTable:
    def test_join_and_leave(self):
        """Players can join and leave seats."""

    def test_join_occupied_seat_raises(self):
        """Joining an occupied seat raises an error."""

    def test_set_hand(self):
        """Set hand for a seated player."""

    def test_set_hand_unseated_raises(self):
        """Setting hand for an empty seat raises."""

    def test_set_hand_duplicate_card_raises(self):
        """Setting a hand that shares a card with another seat raises with clear message."""

    def test_make_bid_valid_turn(self):
        """Bid accepted when it's the correct seat's turn."""

    def test_make_bid_wrong_turn_raises(self):
        """Bid rejected when it's not this seat's turn."""

    def test_make_bid_illegal_bid_raises(self):
        """Illegal bid (e.g., 1C after 2C) raises."""

    def test_proxy_bid_for_unoccupied_seat(self):
        """Any seated player can bid for unoccupied seats."""

    def test_bid_for_another_players_seat_raises(self):
        """Cannot bid for a seat occupied by a different player."""

    def test_bid_by_unseated_player_raises(self):
        """Player must be seated somewhere at the table to bid."""

    def test_get_state_shows_only_your_hand(self):
        """TableView for seat X shows X's hand but not others."""

    def test_get_state_shows_all_bids(self):
        """TableView includes the full auction history."""

    def test_get_advice(self):
        """Advice returned when it's your turn and hand is set."""

    def test_get_advice_not_your_turn_raises(self):
        """Advice rejected when it's not your turn."""

    def test_status_transitions(self):
        """WAITING -> IN_PROGRESS (first bid) -> COMPLETED (auction done)."""

    def test_completed_shows_contract(self):
        """After auction completes, TableView includes the contract."""

    def test_reset_keeps_seats(self):
        """Reset clears hands/auction but keeps seat assignments."""

    def test_reset_back_to_waiting(self):
        """After reset, status is WAITING."""
```

### test_deal.py

```python
class TestDeal:
    def test_four_hands_of_thirteen(self):
        """Deal produces 4 hands of exactly 13 cards each."""

    def test_all_52_cards_present(self):
        """All 52 cards appear exactly once across the 4 hands."""

    def test_no_duplicates_across_hands(self):
        """No card appears in more than one hand."""

    def test_deterministic_with_seed(self):
        """Same seed produces same deal."""

    def test_different_seeds_different_deals(self):
        """Different seeds produce different deals."""

    def test_all_seats_present(self):
        """Dict has keys for all 4 seats."""
```

### test_parse_auction.py

```python
class TestParseAuction:
    def test_empty_string(self):
        """Empty string -> empty auction at dealer's turn."""

    def test_single_bid(self):
        """'1H' -> auction with one bid."""

    def test_full_auction(self):
        """'1H P 2H P P P' -> complete auction."""

    def test_custom_dealer(self):
        """Dealer parameter changes seat assignments."""

    def test_with_vulnerability(self):
        """Vulnerability parameter is passed through."""

    def test_invalid_bid_raises(self):
        """Invalid bid string raises ValueError."""

    def test_illegal_sequence_raises(self):
        """Illegal bid sequence raises IllegalBidError."""

    def test_double_and_redouble(self):
        """'1H X XX' -> double and redouble."""

    def test_passed_out(self):
        """'P P P P' -> passed out."""
```

### test_lobby.py

```python
class TestLobby:
    def test_create_table(self):
        """Create returns a new table with unique ID."""

    def test_get_table(self):
        """Get by ID returns the correct table."""

    def test_get_nonexistent_raises(self):
        """Getting unknown ID raises."""

    def test_list_tables(self):
        """List returns summaries of all tables."""

    def test_delete_table(self):
        """Delete removes table; get raises after delete."""
```

---

## Error Handling

### Custom Exceptions

Define in `service/models.py` or a separate `service/errors.py`:

```python
class SeatOccupiedError(Exception):
    """Raised when trying to join an occupied seat."""

class SeatEmptyError(Exception):
    """Raised when operating on an empty seat."""

class NotYourTurnError(Exception):
    """Raised when bidding out of turn."""

class TableNotFoundError(Exception):
    """Raised when a table ID doesn't exist."""

class AuctionNotStartedError(Exception):
    """Raised when requesting advice before auction starts."""

class AuctionCompleteError(Exception):
    """Raised when trying to bid after auction ends."""

class HandNotSetError(Exception):
    """Raised when requesting advice without a hand."""

class DuplicateCardError(Exception):
    """Raised when a hand shares cards with another seat's hand.
    Message names conflicting seats only, not the cards (to avoid leaking hand info)."""
```

Note: `IllegalBidError` already exists in `model/auction.py` for bid legality. The above are service-layer errors for game-state violations.

---

## Resolved Decisions

- **Contract derivation location:** `contract` property on `AuctionState`, `Contract` dataclass in `model/auction.py`.
- **Table.make_bid authorization:** Table enforces it. `make_bid(seat, bid, player)` — player can bid for their own seat or for unoccupied seats. Cannot bid for another player's seat. Player must be seated somewhere at the table.
- **Status transition: WAITING -> IN_PROGRESS:** First bid triggers the transition. Hands can be set at any time before your turn.

---

## Verification

```bash
pdm run check   # lint + typecheck + all tests must pass
```

All existing 739 tests must continue to pass. New tests should cover all the cases listed above.
