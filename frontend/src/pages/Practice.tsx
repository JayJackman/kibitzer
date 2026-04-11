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
 *   - Once seated, SessionControls shows the join code, copy button,
 *     and leave button in the page header row.
 *   - When waiting for another human's bid, polls every 2s via
 *     useRevalidator() to pick up state changes.
 *
 * Helper mode support:
 *   - Shows a HandEntryForm instead of HandDisplay when hand is null.
 *   - Proxy bidding: BidControls enabled for unoccupied seats with
 *     a "Bidding for [Seat]" banner and for_seat hidden field.
 *   - Always shows SessionControls (for join code sharing).
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

import type { AllBidsAnalysis, Advice, AuctionAnalysis, PracticeState, SessionInfo } from "@/api/types";
import { analyzeAllBids, analyzeAuction } from "@/api/endpoints";
import { useBidKeyboard } from "@/hooks/useBidKeyboard";
import { SEAT_LABELS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import HandDisplay from "@/components/hand/HandDisplay";
import HandEntryForm from "@/components/hand/HandEntryForm";
import AuctionGrid from "@/components/auction/AuctionGrid";
import AuctionHistory from "@/components/auction/AuctionHistory";
import AuctionComplete from "@/components/auction/AuctionComplete";
import BidControls from "@/components/auction/BidControls";
import BidPreview from "@/components/auction/BidPreview";
import AdvicePanel from "@/components/advice/AdvicePanel";
import ScoringSheet from "@/components/scoring/ScoringSheet";
import JoinPanel from "@/components/session/JoinPanel";
import SessionControls from "@/components/session/SessionControls";

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

  // --- Trial bids (hover preview) ---
  // Batch-fetch analyses for all legal bids when the player's turn starts.
  // The result is cached in state so hovering over buttons is instant.
  const [hoveredBid, setHoveredBid] = useState<string | null>(null);
  const [bidAnalyses, setBidAnalyses] = useState<AllBidsAnalysis | null>(null);
  const legalBidsKey = legal_bids.join(",");
  // Stable string key for the auction bids so the effect below doesn't
  // re-run on every 2-second poll (which returns a new array reference
  // even when the content hasn't changed, clearing the hovered bid).
  const auctionBidsKey = auction.bids.map((b) => b.bid).join(",");

  useEffect(() => {
    // Reset analyses when legal bids change (new turn or new hand).
    setBidAnalyses(null);
    setHoveredBid(null);

    // Only fetch when the player can bid (own turn or proxy-bidding
    // in helper mode) and bids are available.
    if (!canBid || legal_bids.length === 0) return;

    // The effect callback itself can't be async (React ignores the
    // returned promise), so we define an inner async function and
    // call it immediately. The `cancelled` flag prevents setting
    // state after the effect has been cleaned up (e.g. the component
    // unmounted or the deps changed before the fetch completed).
    let cancelled = false;
    const bidStrings = auctionBidsKey ? auctionBidsKey.split(",") : [];

    async function fetchAnalyses() {
      try {
        const result = await analyzeAllBids(
          auction.dealer, auction.vulnerability, bidStrings,
        );
        if (!cancelled) setBidAnalyses(result);
      } catch {
        // Silently ignore errors -- trial bids are a nice-to-have, not critical.
      }
    }

    fetchAnalyses();

    return () => {
      cancelled = true;
    };
  }, [legalBidsKey, is_my_turn, auction.dealer, auction.vulnerability, auctionBidsKey]);

  // Look up the hovered bid's analysis from the cached batch response.
  const hoveredAnalysis =
    hoveredBid && bidAnalyses ? bidAnalyses.analyses[hoveredBid] ?? null : null;

  // --- Auction analysis (helper mode) ---
  // In helper mode, fetch per-bid hand descriptions so users can see
  // what each bid communicated (HCP range, suit lengths, etc.) in the
  // bid history. Not needed in practice mode where the engine already
  // provides explanations from the matched rule.
  const [auctionAnalysis, setAuctionAnalysis] = useState<AuctionAnalysis | null>(null);

  useEffect(() => {
    if (!isHelper) return;

    setAuctionAnalysis(null);
    const bidStrings = auction.bids.map((b) => b.bid);
    if (bidStrings.length === 0) return;

    let cancelled = false;
    async function fetchAnalysis() {
      try {
        const result = await analyzeAuction(
          auction.dealer, auction.vulnerability, bidStrings,
        );
        if (!cancelled) setAuctionAnalysis(result);
      } catch {
        // Non-critical -- degrade gracefully if the analysis fails.
      }
    }
    fetchAnalysis();
    return () => { cancelled = true; };
  }, [isHelper, auction.dealer, auction.vulnerability, auctionBidsKey]);

  // --- Advice visibility ---
  const [showAdvice, setShowAdvice] = useState(false);
  useEffect(() => {
    setShowAdvice(false);
  }, [legalBidsKey]);

  function handleAdvise() {
    setShowAdvice(true);
    adviceFetcher.load(`/practice/${state.id}/advise`);
  }

  // Whether to show the "Show Advice" button. Available when it's
  // the player's turn (or proxy turn) and the hand has been entered.
  const canShowAdvice = is_my_turn && hand !== null;

  return (
    <div className="container mx-auto px-4 py-6 pb-[50vh]">
      {/* --- Page header --- */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          {/* Left: title + new hand */}
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
            {/* Undo removes the last human bid (+ computer follow-ups in practice mode).
                Reset clears all bids back to the initial state (same hand/dealer/vuln). */}
            {state.can_undo && (
              <>
                <Form method="post">
                  <input type="hidden" name="intent" value="undo" />
                  <Button type="submit" variant="outline" size="sm" disabled={isSubmitting}>
                    Undo
                  </Button>
                </Form>
                <Form method="post">
                  <input type="hidden" name="intent" value="reset_auction" />
                  <Button type="submit" variant="outline" size="sm" disabled={isSubmitting}>
                    Reset
                  </Button>
                </Form>
              </>
            )}
          </div>
          {/* Right: scoring (helper mode) + join code + copy + leave */}
          <div className="flex items-center gap-2">
            {isHelper && <ScoringSheet state={state} />}
            <SessionControls variant="background" state={state} isSubmitting={isSubmitting} />
          </div>
        </div>
        <p className="text-muted-foreground text-sm">
          Hand #{state.hand_number} &middot; Seat:{" "}
          {SEAT_LABELS[state.your_seat]} &middot; Vuln:{" "}
          {auction.vulnerability}
        </p>
      </div>

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
          <div className="flex items-start gap-4">
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
                  yourSeat={state.your_seat}
                />
              </CardContent>
            </Card>
          </div>

          {auction.bids.length > 0 && (
            <AuctionHistory
              bids={auction.bids}
              yourSeat={state.your_seat}
              bidDescriptions={auctionAnalysis?.bid_cumulative}
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
              onBidHover={setHoveredBid}
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

          {/* Trial bid preview: shows what the hovered bid communicates. */}
          {hoveredAnalysis && <BidPreview analysis={hoveredAnalysis} />}

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
