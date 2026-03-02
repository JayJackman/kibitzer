/**
 * Practice page -- the main bidding practice interface.
 *
 * Composes all practice sub-components into a single page:
 *   - HandDisplay: shows the player's 13 cards + evaluation
 *   - AuctionGrid: 4-column bid history table
 *   - BidControls: 7x5 button grid for placing bids
 *   - AdvicePanel: engine recommendation + thought process
 *
 * Multiplayer support:
 *   - If the user isn't seated, the loader returns { needsJoin, info }
 *     and the page shows a JoinPanel with available seats.
 *   - Once seated, a SessionHeader shows the join code, player names,
 *     and a leave button.
 *   - When waiting for another human's bid, polls every 2s via
 *     useRevalidator() to pick up state changes.
 *
 * Helper mode support:
 *   - Shows a HandEntryForm instead of HandDisplay when hand is null.
 *   - Proxy bidding: BidControls enabled for unoccupied seats with
 *     a "Bidding for [Seat]" banner and for_seat hidden field.
 *   - Always shows SessionHeader (for join code sharing).
 *
 * Data flow uses React Router v7 patterns:
 *   - Loader: fetches session state before the page renders (no loading spinner)
 *   - Action: handles bid placement, redeal, set_hand, join, and leave via form submissions
 *   - Fetcher: loads advice on demand without a full page navigation
 *
 * When the auction completes, the bid controls are replaced with a display
 * of all 4 hands and the final contract, plus a "New Hand" button.
 */
import { useCallback, useEffect, useState } from "react";
import {
  Form,
  useFetcher,
  useLoaderData,
  useNavigation,
  useRevalidator,
  useSubmit,
} from "react-router";

import type {
  Advice,
  AuctionBid,
  Hand,
  PracticeState,
  Seat,
  SessionInfo,
} from "@/api/types";
import { useBidKeyboard } from "@/hooks/useBidKeyboard";
import { SEAT_LABELS, SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, Copy } from "lucide-react";
import HandDisplay from "@/components/hand/HandDisplay";
import AuctionGrid from "@/components/auction/AuctionGrid";
import BidControls from "@/components/auction/BidControls";
import AdvicePanel from "@/components/advice/AdvicePanel";

/** Arrow pointing from the center of the compass toward the declarer's seat. */
const DECLARER_ARROW: Record<Seat, string> = {
  N: "\u2191",  // ↑
  S: "\u2193",  // ↓
  W: "\u2190",  // ←
  E: "\u2192",  // →
};

/** HCP values for each rank (A=4, K=3, Q=2, J=1, others=0). */
const HCP_VALUES: Record<string, number> = { A: 4, K: 3, Q: 2, J: 1 };

/** Count high-card points from a Hand's four suit arrays. */
function countHcp(hand: Hand): number {
  return [hand.spades, hand.hearts, hand.diamonds, hand.clubs]
    .flat()
    .reduce((sum, rank) => sum + (HCP_VALUES[rank] ?? 0), 0);
}

/**
 * The loader returns either full session state (user is seated) or
 * lightweight session info (user needs to join).
 */
type LoaderData =
  | { state: PracticeState; needsJoin?: undefined }
  | { needsJoin: true; info: SessionInfo };

export default function PracticePage() {
  const data = useLoaderData() as LoaderData;

  // If the user isn't seated at this session, show the join panel
  // where they can pick an available seat.
  if (data.needsJoin) {
    return <JoinPanel info={data.info} />;
  }

  return <PracticeView state={data.state} />;
}

/**
 * The full practice UI, shown when the user is seated at the session.
 * Extracted into its own component so hooks aren't called conditionally
 * (hooks must run in the same order on every render).
 */
function PracticeView({ state }: { state: PracticeState }) {
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";
  const adviceFetcher = useFetcher<Advice>();
  const submit = useSubmit();
  const revalidator = useRevalidator();

  const { auction, hand, hand_evaluation, legal_bids, is_my_turn } = state;
  const isHelper = state.mode === "helper";

  // Whether the user can place a bid right now -- either it's their turn
  // or they can proxy-bid for an unoccupied seat in helper mode.
  const canBid = is_my_turn || state.can_proxy_bid;

  // --- Session polling ---
  // Poll every 2 seconds to pick up state changes from other browsers
  // (bids, hand entries, redeals, new players joining, etc.) without
  // requiring WebSockets. Every session has a join code so anyone could
  // join at any time -- always poll to stay in sync.
  // NOTE: revalidator is intentionally omitted from deps -- useRevalidator()
  // returns a new object reference each render, which would tear down and
  // recreate the interval continuously. We access it inside the callback
  // via closure, which always reads the latest value.
  useEffect(() => {
    const interval = setInterval(() => {
      if (revalidator.state === "idle") revalidator.revalidate();
    }, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Keyboard shortcuts ---
  // Include for_seat when proxy-bidding so the action handler knows
  // which unoccupied seat this bid is for.
  const handleBidConfirm = useCallback(
    (bid: string) => {
      const data: Record<string, string> = { intent: "bid", bid };
      if (state.can_proxy_bid && state.proxy_seat) {
        data.for_seat = state.proxy_seat;
      }
      submit(data, { method: "post" });
    },
    [submit, state.can_proxy_bid, state.proxy_seat],
  );
  const { highlightedBids } = useBidKeyboard({
    legalBids: legal_bids,
    enabled: canBid && !auction.is_complete && !isSubmitting,
    onConfirm: handleBidConfirm,
  });

  // --- Advice visibility ---
  const [showAdvice, setShowAdvice] = useState(false);
  const legalBidsKey = legal_bids.join(",");
  useEffect(() => {
    setShowAdvice(false);
  }, [legalBidsKey]);

  function handleAdvise() {
    setShowAdvice(true);
    adviceFetcher.load(`/practice/${state.id}/advise`);
  }

  // Always show the session header -- it displays the join code so
  // the player can invite friends at any time.
  const showSessionHeader = true;

  // Whether to show the "Show Advice" button. Available when it's
  // the player's turn (or proxy turn) and the hand has been entered.
  const canShowAdvice = is_my_turn && hand !== null;

  return (
    <div className="container mx-auto px-4 py-6">
      {/* --- Page header --- */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">
            {isHelper ? "Helper Mode" : "Practice Mode"}
          </h1>
          <Form method="post">
            <input type="hidden" name="intent" value="redeal" />
            <Button type="submit" variant="outline" size="sm" disabled={isSubmitting}>
              New Hand
            </Button>
          </Form>
        </div>
        <p className="text-muted-foreground text-sm">
          Hand #{state.hand_number} &middot; Seat:{" "}
          {SEAT_LABELS[state.your_seat]} &middot; Vuln:{" "}
          {auction.vulnerability}
        </p>
      </div>

      {/* Session header: join code, player names, leave button. */}
      {showSessionHeader && (
        <SessionHeader state={state} isSubmitting={isSubmitting} />
      )}

      {/* Waiting indicator when another human is bidding */}
      {!is_my_turn && !auction.is_complete && state.waiting_for && (
        <div className="text-muted-foreground mb-4 text-sm">
          Waiting for {SEAT_LABELS[state.waiting_for]} to bid...
        </div>
      )}

      {/*
       * --- Main content: two-column layout on desktop ---
       * Left column: bid controls (or all hands) + advice panel
       * Right column: auction grid + hand + bid history
       */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* === Left column: hand + auction grid, history below === */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-row items-start gap-4">
            <Card className="flex-1">
              <CardHeader>
                <CardTitle>Auction</CardTitle>
              </CardHeader>
              <CardContent>
                <AuctionGrid
                  bids={auction.bids}
                  dealer={auction.dealer}
                  currentSeat={auction.current_seat}
                  isComplete={auction.is_complete}
                  yourSeat={state.your_seat}
                />
              </CardContent>
            </Card>

            {/*
             * Show HandDisplay when the player's hand is available,
             * or HandEntryForm in helper mode when hand hasn't been entered yet.
             */}
            {hand ? (
              <HandDisplay
                hand={hand}
                evaluation={hand_evaluation ?? undefined}
                title="Your Hand"
              />
            ) : isHelper ? (
              <HandEntryForm sessionSeat={state.your_seat} />
            ) : null}
          </div>

          {auction.bids.length > 0 && (
            <AuctionHistory
              bids={auction.bids}
              yourSeat={state.your_seat}
            />
          )}
        </div>

        {/* === Right column: controls + advice === */}
        <div className="flex flex-col gap-4">
          {!auction.is_complete ? (
            <BidControls
              legalBids={legal_bids}
              disabled={!canBid || isSubmitting}
              highlightedBids={highlightedBids}
              forSeat={state.can_proxy_bid ? state.proxy_seat ?? undefined : undefined}
              bottomRight={
                canShowAdvice ? (
                  <Button
                    type="button"
                    variant="card"
                    onClick={showAdvice ? () => setShowAdvice(false) : handleAdvise}
                    disabled={adviceFetcher.state === "loading"}
                  >
                    {showAdvice ? "Hide Advice" : "Show Advice"}
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <AuctionComplete state={state} />
          )}

          {showAdvice && (
            <AdvicePanel
              advice={adviceFetcher.data ?? null}
              isLoading={adviceFetcher.state === "loading"}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components used only by PracticePage
// ---------------------------------------------------------------------------

/**
 * Form for entering a hand by suit (helper mode).
 *
 * Four labeled inputs (one per suit) with suit symbols and colors.
 * Tab moves between them. On submit, the four values are joined
 * into PBN format (Spades.Hearts.Diamonds.Clubs) for the API.
 * Each input accepts rank characters like "AKJ52" (case-insensitive).
 */
const SUIT_FIELDS = [
  { key: "S", symbol: SUIT_SYMBOLS.S, color: SUIT_COLORS.S, placeholder: "--" },
  { key: "H", symbol: SUIT_SYMBOLS.H, color: SUIT_COLORS.H, placeholder: "--" },
  { key: "D", symbol: SUIT_SYMBOLS.D, color: SUIT_COLORS.D, placeholder: "--" },
  { key: "C", symbol: SUIT_SYMBOLS.C, color: SUIT_COLORS.C, placeholder: "--" },
] as const;

/** Valid rank characters (case-insensitive). */
const VALID_RANKS = new Set("AKQJT98765432");

/** Rank sort order: A highest (0), 2 lowest (12). */
const RANK_ORDER: Record<string, number> = Object.fromEntries(
  "AKQJT98765432".split("").map((r, i) => [r, i]),
);

/**
 * Parse rank characters from a suit input string.
 * Normalises "10" to "T" and uppercases everything.
 * Returns the list of rank chars (e.g. ["A", "K", "J", "5", "2"]).
 */
function parseRanks(raw: string): string[] {
  const s = raw.toUpperCase().replace(/10/g, "T");
  return [...s].filter((char) => VALID_RANKS.has(char));
}

/**
 * Filter raw rank input: uppercase, strip invalid or duplicate characters,
 * clamp to `maxCards` so the total hand never exceeds 13, and sort
 * high-to-low (A K Q J T 9 ... 2).
 */
function filterRankInput(raw: string, maxCards: number): string {
  const seen = new Set<string>();
  return raw
    .toUpperCase()
    .split("")
    .filter((char) => {
      if (!VALID_RANKS.has(char) || seen.has(char)) return false;
      seen.add(char);
      return true;
    })
    .slice(0, maxCards)
    .sort((a, b) => RANK_ORDER[a] - RANK_ORDER[b])
    .join("");
}

/**
 * Validate the four suit inputs. Returns an error message string
 * or null if the hand is valid (exactly 13 unique cards).
 */
function validateHand(suits: Record<string, string>): string | null {
  const allCards: string[] = [];
  for (const [suitKey, raw] of Object.entries(suits)) {
    for (const rank of parseRanks(raw)) {
      allCards.push(`${rank}${suitKey}`);
    }
  }
  if (allCards.length === 0) return "Enter your cards";
  if (allCards.length !== 13) return `${allCards.length} cards entered (need 13)`;

  // Check for duplicates within the hand.
  const seen = new Set<string>();
  for (const card of allCards) {
    if (seen.has(card)) return `Duplicate card: ${card}`;
    seen.add(card);
  }
  return null;
}

function HandEntryForm({ sessionSeat }: { sessionSeat: Seat }) {
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  // Controlled state for each suit so we can assemble PBN on submit.
  const [suits, setSuits] = useState({ S: "", H: "", D: "", C: "" });
  const [error, setError] = useState<string | null>(null);

  // Assemble PBN: "AKJ52.KQ3.84.A73" (empty suits become "" which is valid).
  // Normalise "10" to "T" for the backend PBN parser.
  const pbn = SUIT_FIELDS.map(({ key }) =>
    parseRanks(suits[key]).join(""),
  ).join(".");

  // Total card count for the live counter.
  const cardCount = SUIT_FIELDS.reduce(
    (n, { key }) => n + parseRanks(suits[key]).length,
    0,
  );

  /** Validate before allowing the form to submit. */
  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    const err = validateHand(suits);
    if (err) {
      e.preventDefault();
      setError(err);
    }
  }

  return (
    <Card className="w-full py-2">
      <CardHeader className="px-3">
        <CardTitle>Enter Your Hand</CardTitle>
      </CardHeader>
      <CardContent className="px-3">
        <Form method="post" className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <input type="hidden" name="intent" value="set_hand" />
          <input type="hidden" name="seat" value={sessionSeat} />
          <input type="hidden" name="hand_pbn" value={pbn} />

          {/* One input per suit, each prefixed with the colored suit symbol. */}
          <div className="flex flex-col gap-2">
            {SUIT_FIELDS.map(({ key, symbol, color, placeholder }, i) => (
              <div key={key} className="flex items-center gap-2">
                <span className={cn("text-lg font-bold w-5 text-center", color)}>
                  {symbol}
                </span>
                <Input
                  value={suits[key]}
                  onChange={(e) => {
                    // How many cards the other three suits already use.
                    const otherCount = SUIT_FIELDS.reduce(
                      (n, f) => n + (f.key === key ? 0 : parseRanks(suits[f.key]).length),
                      0,
                    );
                    const value = filterRankInput(e.target.value, 13 - otherCount);
                    setSuits((prev) => ({ ...prev, [key]: value }));
                    setError(null);
                  }}
                  placeholder={placeholder}
                  className="font-mono flex-1"
                  autoFocus={i === 0}
                />
              </div>
            ))}
          </div>

          {/* Live card count + validation error */}
          <div className="flex items-center gap-3">
            <span className={cn(
              "text-xs",
              cardCount === 13 ? "text-green-600" : "text-card-muted-foreground",
            )}>
              {cardCount}/13 cards
            </span>
            {error && <span className="text-xs text-destructive">{error}</span>}
          </div>

          <Button type="submit" size="sm" className="w-fit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Submit Hand"}
          </Button>
        </Form>
      </CardContent>
    </Card>
  );
}

/**
 * Running auction history showing every bid with explanations.
 *
 * Each bid row shows the seat name, bid, explanation, and -- for player bids --
 * a green/amber indicator of whether the bid matched the engine's recommendation.
 * Pass bids are filtered out to keep the history compact.
 */
function AuctionHistory({
  bids,
  yourSeat,
}: {
  bids: AuctionBid[];
  yourSeat: Seat;
}) {
  // Filter out Pass bids, but track original indices for stable React keys.
  const nonPassBids = bids
    .map((entry, i) => ({ entry, origIndex: i }))
    .filter(({ entry }) => entry.bid !== "Pass" || entry.matched_engine === false);

  if (nonPassBids.length === 0) return null;

  return (
    <Card>
      <CardHeader className="px-4">
        <CardTitle>Bid History</CardTitle>
      </CardHeader>
      <CardContent className="px-4 text-sm">
        <div className="flex flex-col gap-1">
        {nonPassBids.map(({ entry, origIndex }) => {
          const isPlayer = entry.seat === yourSeat;
          const matched = entry.matched_engine;

          return (
            <div key={origIndex} className={cn(
              "flex items-baseline gap-2 rounded px-2 py-0.5",
              isPlayer && matched === true && "bg-correct",
              isPlayer && matched === false && "bg-incorrect",
            )}>
              {/* Seat label */}
              <span className={cn("w-12 shrink-0 font-medium", isPlayer && "text-primary")}>
                {SEAT_LABELS[entry.seat]}
              </span>

              {/* Bid */}
              <span className="font-semibold">{entry.bid}</span>

              {/* Explanation */}
              {entry.explanation && (
                <span className="text-card-muted-foreground text-xs italic">
                  {entry.explanation}
                </span>
              )}

              {/* Match indicator for player bids */}
              {matched === true && (
                <span className="text-xs italic text-green-600">Matched engine</span>
              )}
              {matched === false && (
                <span className="text-xs italic text-amber-600">Missed</span>
              )}
            </div>
          );
        })}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Shown when the auction is complete: displays the final contract
 * and all 4 hands arranged in a compass layout.
 *
 * In helper mode, some seats may not have hands entered -- those
 * positions are left empty in the compass layout.
 */
/** Placeholder hand with empty suits, used when a seat's hand isn't set. */
const EMPTY_HAND: Hand = { spades: [], hearts: [], diamonds: [], clubs: [] };

function AuctionComplete({ state }: { state: PracticeState }) {
  const { auction, all_hands } = state;

  /** Get the hand for a seat, falling back to an empty placeholder. */
  function handFor(seat: Seat) {
    return all_hands?.[seat] ?? EMPTY_HAND;
  }

  /** Title with HCP if the hand has cards, just the seat name otherwise. */
  function titleFor(seat: Seat, label: string) {
    const h = all_hands?.[seat];
    return h ? `${label} (${countHcp(h)})` : label;
  }

  return (
    <div className="flex flex-col gap-4">
      {/*
       * All 4 hands in compass layout with contract in the center:
       *            North
       *   West   [Contract]   East
       *            South
       * Seats without hands render with empty suit rows.
       */}
      <div className="grid grid-cols-3 gap-2">
        {/* Top row: North in the center */}
        <div />
        <HandDisplay hand={handFor("N")} title={titleFor("N", "North")} isPlayer={state.your_seat === "N"} />
        <div />

        {/* Middle row: West, Contract, East */}
        <HandDisplay hand={handFor("W")} title={titleFor("W", "West")} isPlayer={state.your_seat === "W"} />
        {auction.contract ? (
          <ContractDisplay contract={auction.contract} />
        ) : (
          <div />
        )}
        <HandDisplay hand={handFor("E")} title={titleFor("E", "East")} isPlayer={state.your_seat === "E"} />

        {/* Bottom row: South in the center */}
        <div />
        <HandDisplay hand={handFor("S")} title={titleFor("S", "South")} isPlayer={state.your_seat === "S"} />
        <div />
      </div>
    </div>
  );
}

/**
 * Displays the contract in the center of the compass layout with an arrow
 * pointing toward the declarer. For N/S the arrow is above/below the bid
 * (vertical stack). For W/E the arrow is to the left/right (horizontal).
 */
function ContractDisplay({ contract }: { contract: PracticeState["auction"]["contract"] }) {
  if (!contract) return null;

  if (contract.passed_out) {
    return (
      <div className="flex items-center justify-center">
        <p className="text-center text-2xl font-bold">Passed Out</p>
      </div>
    );
  }

  /*
   * Grid trick: both the bid and arrow occupy the same single cell
   * (row 1 / col 1). The bid is centered, the arrow is self-aligned
   * to the edge nearest the declarer's hand. This keeps the bid
   * perfectly centered regardless of arrow size or direction.
   */
  const d = contract.declarer;
  const arrowAlign: Record<Seat, string> = {
    N: "self-start justify-self-center",   // top center
    S: "self-end justify-self-center",     // bottom center
    W: "self-center justify-self-start",   // middle left
    E: "self-center justify-self-end",     // middle right
  };

  return (
    <div className="grid">
      {/* Bid — centered in the cell */}
      <span className="col-start-1 row-start-1 place-self-center text-3xl font-bold">
        {contract.level}
        <ContractSuit suit={contract.suit} />
        {contract.doubled && " X"}
        {contract.redoubled && " XX"}
      </span>
      {/* Arrow — same cell, pushed to the edge toward the declarer */}
      <span className={`col-start-1 row-start-1 text-4xl leading-none ${arrowAlign[d]}`}>
        {DECLARER_ARROW[d]}
      </span>
    </div>
  );
}

/**
 * Renders the contract's suit as a colored Unicode symbol.
 * For suit contracts (C/D/H/S), shows the symbol in the suit's color.
 * For notrump, shows "NT" unstyled.
 */
function ContractSuit({ suit }: { suit: string }) {
  if (suit in SUIT_SYMBOLS) {
    const key = suit as keyof typeof SUIT_SYMBOLS;
    return (
      <span className={SUIT_COLORS[key]}>
        {SUIT_SYMBOLS[key]}
      </span>
    );
  }
  return <>{suit}</>;
}

// ---------------------------------------------------------------------------
// Multiplayer sub-components
// ---------------------------------------------------------------------------

/** All four seats in display order. */
const ALL_SEATS: Seat[] = ["N", "E", "S", "W"];

/**
 * Shown when the user isn't seated at the session (loader returned 403).
 * Displays the session info and a seat picker so the user can join.
 *
 * Each available seat is a form button that submits intent=join with
 * the chosen seat. The practiceAction calls joinSession(), then
 * redirects to trigger a fresh loader run (now returning full state).
 */
function JoinPanel({ info }: { info: SessionInfo }) {
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  return (
    <div className="container mx-auto flex flex-col items-center gap-6 px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Join Session</CardTitle>
          <p className="text-card-muted-foreground text-sm">
            Code: <span className="font-mono font-semibold">{info.join_code}</span>
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Show who's already seated */}
          <div className="text-sm">
            {ALL_SEATS.map((seat) => (
              <div key={seat} className="flex items-center gap-2 py-0.5">
                <span className="w-14 font-medium">{SEAT_LABELS[seat]}</span>
                <span className="text-card-muted-foreground">
                  {info.players[seat] ?? "Computer"}
                </span>
              </div>
            ))}
          </div>

          {/* Seat picker: one button per available seat */}
          <p className="text-sm font-medium">Pick a seat:</p>
          <div className="flex gap-2">
            {info.available_seats.map((seat) => (
              <Form method="post" key={seat}>
                <input type="hidden" name="intent" value="join" />
                <input type="hidden" name="seat" value={seat} />
                <Button type="submit" variant="outline" disabled={isSubmitting}>
                  {SEAT_LABELS[seat]}
                </Button>
              </Form>
            ))}
          </div>

          {info.available_seats.length === 0 && (
            <p className="text-card-muted-foreground text-sm">
              No seats available -- the session is full.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Session header bar shown during multiplayer and helper mode sessions.
 * Displays the join code (with a copy button), player names at each
 * seat, and a leave button.
 */
function SessionHeader({
  state,
  isSubmitting,
}: {
  state: PracticeState;
  isSubmitting: boolean;
}) {
  const [copied, setCopied] = useState(false);

  /** Copy the join code to the clipboard and show a brief "Copied!" label. */
  function handleCopy() {
    navigator.clipboard.writeText(state.join_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border bg-card text-card-foreground px-4 py-2 text-sm">
      {/* Join code with copy button */}
      <div className="flex items-center gap-1.5">
        <span className="text-card-muted-foreground">Code:</span>
        <span className="font-mono font-semibold">{state.join_code}</span>
        <Button variant="outline" size="xs" onClick={handleCopy} className="px-1.5">
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        </Button>
      </div>

      {/* Player names at each seat */}
      <div className="flex items-center gap-3">
        {ALL_SEATS.map((seat) => {
          const name = state.players[seat];
          const isYou = seat === state.your_seat;
          return (
            <span key={seat} className={cn(isYou && "font-semibold")}>
              {SEAT_LABELS[seat]}:{" "}
              <span className={cn(name === null && "text-card-muted-foreground")}>
                {isYou ? "You" : name ?? "CPU"}
              </span>
            </span>
          );
        })}
      </div>

      {/* Leave button */}
      <Form method="post" className="ml-auto">
        <input type="hidden" name="intent" value="leave" />
        <Button
          type="submit"
          variant="outline"
          size="xs"
          disabled={isSubmitting}
        >
          Leave
        </Button>
      </Form>
    </div>
  );
}
