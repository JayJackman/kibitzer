/**
 * Practice page -- the main bidding practice interface.
 *
 * Composes all practice sub-components into a single page:
 *   - HandDisplay: shows the player's 13 cards + evaluation
 *   - AuctionGrid: 4-column bid history table
 *   - BidControls: 7x5 button grid for placing bids
 *   - AdvicePanel: engine recommendation + thought process
 *
 * Data flow uses React Router v7 patterns:
 *   - Loader: fetches session state before the page renders (no loading spinner)
 *   - Action: handles bid placement and redeal via form submissions
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
  useSubmit,
} from "react-router";

import type { Advice, AuctionBid, Hand, PracticeState, Seat } from "@/api/types";
import { useBidKeyboard } from "@/hooks/useBidKeyboard";
import { SEAT_LABELS, SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

/** The loader returns the full practice session state. */
interface LoaderData {
  state: PracticeState;
}

export default function PracticePage() {
  // --- Data from React Router ---

  /**
   * useLoaderData: the session state fetched by the loader BEFORE this
   * component rendered. No loading spinner needed -- the data is ready.
   */
  const { state } = useLoaderData() as LoaderData;


  /**
   * useNavigation: tells us if a form submission is in flight. Used to
   * show a subtle "submitting" state on the bid controls.
   */
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  /**
   * useFetcher: for the "Advise Me" button. Loads advice from the backend
   * without a full page navigation (no URL change, no loader re-run).
   * The fetcher manages its own loading state independently.
   */
  const adviceFetcher = useFetcher<Advice>();

  /**
   * useSubmit: programmatic form submission. Used by the keyboard shortcut
   * hook to submit a bid when the user confirms with Enter/Space.
   */
  const submit = useSubmit();

  // Destructure the session state for easier access in the template.
  const { auction, hand, hand_evaluation, legal_bids, is_my_turn } = state;

  /**
   * Keyboard shortcut hook for bid selection.
   * Lets the user press level/suit keys to filter the bid grid, then
   * Enter/Space to confirm. Only active when it's the player's turn
   * and the auction is still going.
   */
  const handleBidConfirm = useCallback(
    (bid: string) => {
      submit({ intent: "bid", bid }, { method: "post" });
    },
    [submit],
  );
  const { highlightedBids } = useBidKeyboard({
    legalBids: legal_bids,
    enabled: is_my_turn && !auction.is_complete && !isSubmitting,
    onConfirm: handleBidConfirm,
  });

  /**
   * Track whether advice is visible. Set to true when the user clicks
   * "Advise Me", reset to false when the legal bids change (i.e., after
   * a bid is placed and it's a new turn).
   */
  const [showAdvice, setShowAdvice] = useState(false);
  const legalBidsKey = legal_bids.join(",");
  useEffect(() => {
    setShowAdvice(false);
  }, [legalBidsKey]);

  /**
   * Handle the "Advise Me" button click.
   * Triggers a GET to the advice loader route, which fetches
   * engine advice without navigating away from the page.
   */
  function handleAdvise() {
    setShowAdvice(true);
    adviceFetcher.load(`/practice/${state.id}/advise`);
  }


  return (
    <div className="container mx-auto px-4 py-6">
      {/* --- Page header: title, hand number, and New Hand button --- */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Practice Mode</h1>
          <p className="text-muted-foreground text-sm">
            Hand #{state.hand_number} &middot; Seat:{" "}
            {SEAT_LABELS[state.your_seat]} &middot; Vuln:{" "}
            {auction.vulnerability}
          </p>
        </div>

        {/*
         * "New Hand" button: submits a form with intent=redeal.
         * Uses its own <Form> so it doesn't conflict with the bid form.
         */}
        <Form method="post">
          <input type="hidden" name="intent" value="redeal" />
          <Button type="submit" variant="outline" disabled={isSubmitting}>
            New Hand
          </Button>
        </Form>
      </div>

      {/*
       * --- Main content: two-column layout on desktop ---
       * Left column: hand + advise button + advice panel
       * Right column: auction grid + feedback + bid controls (or all hands)
       */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* === Left column: controls + advice === */}
        <div className="flex flex-col gap-4">

          {/*
           * During active bidding: show bid controls.
           * After auction completes: show contract + all hands + New Hand.
           */}
          {!auction.is_complete ? (
            <BidControls
              legalBids={legal_bids}
              disabled={!is_my_turn || isSubmitting}
              highlightedBids={highlightedBids}
              bottomRight={
                is_my_turn && !showAdvice ? (
                  <Button
                    variant="secondary"
                    onClick={handleAdvise}
                    disabled={adviceFetcher.state === "loading"}
                  >
                    {adviceFetcher.state === "loading" ? "Thinking..." : "Advise Me"}
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <AuctionComplete state={state} />
          )}

          {/* Advice panel -- visible after clicking "Advise Me", hidden after bidding */}
          {showAdvice && (
            <AdvicePanel
              advice={adviceFetcher.data ?? null}
              isLoading={adviceFetcher.state === "loading"}
            />
          )}
        </div>

        {/* === Right area: hand + auction grid side by side, history below === */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-row items-start gap-4">
            {/* Auction history grid */}
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
                />
              </CardContent>
            </Card>

            {/* Player's hand with evaluation metrics */}
            <HandDisplay
              hand={hand}
              evaluation={hand_evaluation}
              title="Your Hand"
            />
          </div>

          {/* Auction history: every bid with explanations + feedback */}
          {auction.bids.length > 0 && (
            <AuctionHistory
              bids={auction.bids}
              yourSeat={state.your_seat}
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
    .filter(({ entry }) => entry.bid !== "Pass");

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
              isPlayer && matched === true && "bg-green-100",
              isPlayer && matched === false && "bg-amber-100",
            )}>
              {/* Seat label */}
              <span className={cn("w-12 shrink-0 font-medium", isPlayer && "text-primary")}>
                {SEAT_LABELS[entry.seat]}
              </span>

              {/* Bid */}
              <span className="font-semibold">{entry.bid}</span>

              {/* Explanation */}
              {entry.explanation && (
                <span className="text-muted-foreground text-xs italic">
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
 */
function AuctionComplete({ state }: { state: PracticeState }) {
  const { auction, all_hands } = state;

  return (
    <div className="flex flex-col gap-4">
      {/*
       * All 4 hands in compass layout with contract in the center:
       *            North
       *   West   [Contract]   East
       *            South
       */}
      {all_hands && (
        <div className="grid grid-cols-3 gap-2">
          {/* Top row: North in the center */}
          <div />
          <HandDisplay hand={all_hands.N} title={`North (${countHcp(all_hands.N)})`} isPlayer={state.your_seat === "N"} />
          <div />

          {/* Middle row: West, Contract, East */}
          <HandDisplay hand={all_hands.W} title={`West (${countHcp(all_hands.W)})`} isPlayer={state.your_seat === "W"} />
          {auction.contract ? (
            <ContractDisplay contract={auction.contract} />
          ) : (
            <div />
          )}
          <HandDisplay hand={all_hands.E} title={`East (${countHcp(all_hands.E)})`} isPlayer={state.your_seat === "E"} />

          {/* Bottom row: South in the center */}
          <div />
          <HandDisplay hand={all_hands.S} title={`South (${countHcp(all_hands.S)})`} isPlayer={state.your_seat === "S"} />
          <div />
        </div>
      )}
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
