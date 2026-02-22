# Phase 1: Domain Model

The `model/` package defines the core vocabulary of the system. Every other layer imports from here. Getting these representations right is critical — changing them later means changing everything.

## Modules

| Module | Classes | Purpose |
|--------|---------|---------|
| `card.py` | `Suit`, `Rank`, `Card` | Individual card representation |
| `hand.py` | `Hand` | 13-card hand with suit queries and shape analysis |
| `bid.py` | `Bid`, `Strain`, `BidType` | A single bid (1H, Pass, Double, etc.) |
| `auction.py` | `AuctionState`, `Seat`, `Vulnerability` | Full auction history and derived state |

## Design Decisions to Resolve

### 1. Hand input format

Options for how users specify a hand:

- **PBN-style** (dots): `AKJ52.KQ3.84.A73` — suits in S.H.D.C order, separated by dots
- **Labeled**: `S:AKJ52 H:KQ3 D:84 C:A73` — explicit suit labels
- **Compact**: `SAKJ52HKQ3D84CA73` — suit letter then cards, no separators

Recommendation: Support all three for input parsing (in the CLI parser layer), but use PBN-style as the canonical internal string format since it's the most standard in bridge software.

### 2. Hand immutability

Hands should be **frozen/immutable** — a hand never changes once dealt. This means:
- `frozenset` of Cards internally
- `@dataclass(frozen=True)`
- All queries (suit_length, shape, etc.) are computed properties or methods, not stored state

### 3. Bid representation

A `Bid` needs to cover:
- Suit bids: level (1-7) + strain (C/D/H/S/NT)
- Pass
- Double
- Redouble

Key question: Should `Bid` be ordered/comparable? Yes — bids must be compared to check legality (each bid must be higher than the last suit bid). Natural ordering: 1C < 1D < 1H < 1S < 1NT < 2C < ... < 7NT.

### 4. Auction state — what to track

The `AuctionState` needs to answer these questions efficiently (used by every rule):

- Whose turn is it?
- What did partner bid? What did RHO bid?
- Is this an opening position (no bids yet)?
- What seat position am I in (1st/2nd/3rd/4th)?
- Has a trump suit been agreed?
- Is the auction competitive (opponents bid)?
- Is the auction complete (3 passes after a bid, or 4 initial passes)?
- What is the full bid history?

### 5. Seat and Vulnerability

`Seat` is an enum (N/E/S/W) with helper methods for partner, LHO, RHO.

`Vulnerability` tracks NS and EW vulnerability independently. Affects preemptive bidding decisions and competitive actions.

### 6. Strain vs Suit

The plan uses both `Suit` (C/D/H/S for cards) and `Strain` (C/D/H/S/NT for bids). These are related but distinct — notrump is a strain but not a suit. The `Strain` enum includes a `from_suit()` converter.

## Classes in Detail

### Suit
- `IntEnum` ordered: CLUBS=1, DIAMONDS=2, HEARTS=3, SPADES=4
- Properties: `is_major`, `is_minor`, `symbol` (unicode), `short` (single letter)

### Rank
- `IntEnum`: TWO=2 through ACE=14
- Property: `hcp` — 4-3-2-1 point value (J=1, Q=2, K=3, A=4, others=0)
- Property: `short` — display character (2-9, T, J, Q, K, A)

### Card
- Frozen dataclass: `suit: Suit`, `rank: Rank`
- Orderable (for sorting within a hand)

### Hand
- Frozen dataclass wrapping `FrozenSet[Card]`
- Validates exactly 13 cards
- Key methods:
  - `suit_cards(suit)` — cards in a suit, sorted high-to-low
  - `suit_length(suit)` — count of cards in a suit
  - `shape` — tuple (S, H, D, C) lengths
  - `sorted_shape` — shape sorted descending (e.g., 5-4-3-1)
  - `is_balanced` — 4333, 4432, or 5332
  - `is_semi_balanced` — balanced + 5422, 6322
  - `longest_suit` — longest suit (higher-ranking wins ties)
  - `has_card(suit, rank)` — boolean check
- Factory methods: `from_pbn()`, `from_text()`, `from_labeled()`

### Bid
- Frozen dataclass: `bid_type: BidType`, `level: Optional[int]`, `strain: Optional[Strain]`
- `BidType` enum: SUIT, PASS, DOUBLE, REDOUBLE
- `Strain` enum: CLUBS=1, DIAMONDS=2, HEARTS=3, SPADES=4, NOTRUMP=5
- Orderable for legality checks
- String parsing: `bid("1NT")`, `bid("Pass")`, `bid("X")`

### AuctionState
- Mutable (bids get added over time)
- Fields: `dealer: Seat`, `vulnerability: Vulnerability`, `bids: List[Tuple[Seat, Bid]]`
- Key properties/methods:
  - `current_seat` — whose turn it is
  - `is_complete` — auction over?
  - `opening_bid` — first non-pass bid and who made it
  - `partner_last_bid(seat)` — partner's most recent non-pass bid
  - `rho_last_bid(seat)` — RHO's most recent non-pass bid
  - `is_opener_position` — all passes so far?
  - `opening_seat_position` — 1st/2nd/3rd/4th seat
  - `bids_by(seat)` — all bids by a seat
  - `is_competitive()` — opponents have entered?
  - `add_bid(bid)` — append a bid

### Seat
- Enum: NORTH=0, EAST=1, SOUTH=2, WEST=3
- Methods: `partner`, `lho`, `rho`

### Vulnerability
- Frozen dataclass: `ns_vulnerable: bool`, `ew_vulnerable: bool`
- Method: `is_vulnerable(seat)`

## Testing for Phase 1

- Card/Suit/Rank creation and properties
- Hand creation from all three input formats
- Hand validation (reject != 13 cards, duplicates)
- Hand shape/balance queries against known hands
- Bid parsing, ordering, and legality
- AuctionState: add bids, check current seat, detect completion
- Seat partner/LHO/RHO relationships
- Vulnerability queries

## Resolved Decisions

1. **HCP in Hand?** No. Hand is pure structure — all point-counting lives in the evaluation layer. Computed on the fly (it's cheap).

2. **`short` property vs `__str__`?** Use `__str__` for human-readable display (e.g., `str(Rank.ACE)` -> `"A"`, `str(Suit.SPADES)` -> `"♠"`). Let `__repr__` keep the default enum behavior (`Rank.ACE`, `Suit.SPADES`). Drop the `short` property entirely. For `Suit`, keep a `letter` property (`"S"`, `"H"`, etc.) for input parsing since the symbol isn't typeable.

3. **Bid legality on `add_bid()`?** Yes. `add_bid()` raises an exception on illegal bids (e.g., 1H after 2C). Callers are responsible for catching the exception gracefully.

4. **`Board` container?** Yes, keep it in the model layer. A board is a real bridge concept — it bundles hand + seat + auction (which already contains vulnerability). Lives in `model/board.py`. Every layer passes a single `Board` instead of loose args.

5. **`Suit.__str__`?** Symbol for display (`♠`), `letter` property for parsing (`S`).

## Open Questions

None — Phase 1 design is resolved.
