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
import { useCallback } from "react";
import {
  Form,
  useActionData,
  useFetcher,
  useLoaderData,
  useNavigation,
  useSubmit,
} from "react-router";

import type { Advice, BidFeedback, PracticeState, Seat } from "@/api/types";
import { useBidKeyboard } from "@/hooks/useBidKeyboard";
import { SEAT_LABELS, SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import HandDisplay from "@/components/hand/HandDisplay";
import AuctionGrid from "@/components/auction/AuctionGrid";
import BidControls from "@/components/auction/BidControls";
import AdvicePanel from "@/components/advice/AdvicePanel";

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
   * useActionData: the result of the most recent form submission (bid or
   * redeal). For bids, this contains the BidFeedback (matched_engine, etc.).
   * Null if no action has run yet or after a redeal (which redirects).
   */
  const actionData = useActionData() as BidFeedback | null | undefined;

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
   * Handle the "Advise Me" button click.
   * Triggers a GET to the advice loader route, which fetches
   * engine advice without navigating away from the page.
   */
  function handleAdvise() {
    adviceFetcher.load(`/practice/${state.id}/advise`);
  }

  // Feedback from the last bid (if any). Shows whether the player's bid
  // matched the engine's recommendation.
  const feedback = actionData ?? state.last_feedback;

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
        {/* === Left column === */}
        <div className="flex flex-col gap-4">
          {/* Player's hand with evaluation metrics */}
          <HandDisplay
            hand={hand}
            evaluation={hand_evaluation}
            title="Your Hand"
          />

          {/* "Advise Me" button -- only shown during active bidding */}
          {!auction.is_complete && is_my_turn && (
            <Button
              variant="secondary"
              onClick={handleAdvise}
              disabled={adviceFetcher.state === "loading"}
            >
              {adviceFetcher.state === "loading" ? "Thinking..." : "Advise Me"}
            </Button>
          )}

          {/* Advice panel -- appears after clicking "Advise Me" */}
          <AdvicePanel
            advice={adviceFetcher.data ?? null}
            isLoading={adviceFetcher.state === "loading"}
          />
        </div>

        {/* === Right column === */}
        <div className="flex flex-col gap-4">
          {/* Auction history grid */}
          <Card>
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

          {/* Bid feedback from the last action */}
          {feedback && <FeedbackBanner feedback={feedback} />}

          {/* Computer bids notification */}
          {state.computer_bids.length > 0 && (
            <ComputerBidsNotice bids={state.computer_bids} />
          )}

          {/*
           * During active bidding: show bid controls.
           * After auction completes: show contract + all hands + New Hand.
           */}
          {!auction.is_complete ? (
            <BidControls
              legalBids={legal_bids}
              disabled={!is_my_turn || isSubmitting}
              highlightedBids={highlightedBids}
            />
          ) : (
            <AuctionComplete state={state} />
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
 * Banner showing whether the player's last bid matched the engine.
 * Green for match, amber for mismatch (with the engine's recommendation).
 */
function FeedbackBanner({ feedback }: { feedback: BidFeedback }) {
  return (
    <div
      className={cn(
        "rounded-md border px-4 py-2 text-sm",
        feedback.matched_engine
          ? "border-green-200 bg-green-50 text-green-800"
          : "border-amber-200 bg-amber-50 text-amber-800",
      )}
    >
      {feedback.matched_engine ? (
        "Matched the engine's recommendation."
      ) : (
        <>
          Engine recommends <strong>{feedback.engine_bid}</strong>:{" "}
          {feedback.engine_explanation}
        </>
      )}
    </div>
  );
}

/**
 * Small notice listing what the computer seats bid since the player's
 * last action. Helps the player track what happened while it wasn't
 * their turn.
 */
function ComputerBidsNotice({
  bids,
}: {
  bids: { seat: Seat; bid: string; explanation: string }[];
}) {
  return (
    <div className="text-muted-foreground rounded-md border px-4 py-2 text-xs">
      {bids.map((cb, i) => (
        <div key={i}>
          <strong>{SEAT_LABELS[cb.seat]}</strong> bid {cb.bid}
          {cb.explanation && (
            <span className="ml-1 italic">({cb.explanation})</span>
          )}
        </div>
      ))}
    </div>
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
      {/* Final contract summary */}
      {auction.contract && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-lg font-semibold">
              {auction.contract.passed_out ? (
                "Passed Out"
              ) : (
                <>
                  Contract: {auction.contract.level}
                  <ContractSuit suit={auction.contract.suit} />
                  {auction.contract.doubled && " X"}
                  {auction.contract.redoubled && " XX"} by{" "}
                  {SEAT_LABELS[auction.contract.declarer]}
                </>
              )}
            </p>
          </CardContent>
        </Card>
      )}

      {/*
       * All 4 hands in compass layout:
       *         North
       *   West        East
       *         South
       */}
      {all_hands && (
        <div className="grid grid-cols-3 gap-2">
          {/* Top row: North in the center */}
          <div />
          <HandDisplay hand={all_hands.N} title="North" />
          <div />

          {/* Middle row: West and East on the sides */}
          <HandDisplay hand={all_hands.W} title="West" />
          <div />
          <HandDisplay hand={all_hands.E} title="East" />

          {/* Bottom row: South in the center */}
          <div />
          <HandDisplay hand={all_hands.S} title="South" />
          <div />
        </div>
      )}
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
