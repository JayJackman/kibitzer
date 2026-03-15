/**
 * Standalone Auction Analyzer page.
 *
 * Enter bids one at a time using the bid grid (click mode) and see:
 *   - An auction grid showing all bids so far
 *   - Per-player hand description cards (what we know about N/E/S/W)
 *   - What each bid communicated (in the bid history below the grid)
 *
 * All state is local -- no backend session needed. The page calls
 * POST /api/analyze/auction after each bid to get updated analysis.
 *
 * Controls:
 *   - Dealer picker + Vulnerability picker to set up the auction
 *   - Undo: removes the last bid
 *   - Reset: clears all bids and returns to setup
 */
import { useCallback, useEffect, useState } from "react";

import type {
  AllBidsAnalysis,
  AuctionAnalysis,
  AuctionBid,
  Seat,
} from "@/api/types";
import { analyzeAllBids, analyzeAuction } from "@/api/endpoints";
import { SEAT_LABELS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import SeatPicker from "@/components/ui/SeatPicker";
import VulnPicker from "@/components/ui/VulnPicker";
import AuctionGrid from "@/components/auction/AuctionGrid";
import BidAnalysisCard from "@/components/auction/BidAnalysisCard";
import BidControls from "@/components/auction/BidControls";
import BidPreview from "@/components/auction/BidPreview";
import SeatAnalysisCard from "@/components/auction/SeatAnalysisCard";

/** All four seats in standard order. */
const ALL_SEATS: Seat[] = ["N", "E", "S", "W"];

/** All 36 legal bids in a fresh auction (Pass + every level/suit combo). */
const ALL_BIDS: string[] = [
  "Pass",
  ...Array.from({ length: 7 }, (_, i) => i + 1).flatMap((level) =>
    ["C", "D", "H", "S", "NT"].map((suit) => `${level}${suit}`),
  ),
];

/** Map seat index offsets from dealer to get seat for each bid. */
function seatForBid(dealer: Seat, index: number): Seat {
  const dealerIdx = ALL_SEATS.indexOf(dealer);
  return ALL_SEATS[(dealerIdx + index) % 4];
}

export default function AnalyzerPage() {
  // --- Setup state ---
  const [dealer, setDealer] = useState<Seat>("N");
  const [vuln, setVuln] = useState("None");

  // --- Auction state (local, no backend session) ---
  const [bids, setBids] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<AuctionAnalysis | null>(null);
  const [hoveredBid, setHoveredBid] = useState<string | null>(null);
  const [bidAnalyses, setBidAnalyses] = useState<AllBidsAnalysis | null>(null);

  // Derive the legal bids and current seat from analysis (if available),
  // otherwise every bid is legal in a fresh auction.
  const legalBids = analysis?.legal_bids ?? ALL_BIDS;
  const currentSeat = analysis?.current_seat ?? dealer;
  const isComplete = analysis !== null && analysis.current_seat === null && bids.length > 0;

  // --- Fetch analysis whenever bids change ---
  useEffect(() => {
    // No bids yet -- clear analysis.
    if (bids.length === 0) {
      setAnalysis(null);
      return;
    }

    let cancelled = false;
    analyzeAuction(dealer, vuln, bids).then(
      (result) => {
        if (!cancelled) setAnalysis(result);
      },
      // On error, keep the previous analysis rather than clearing it.
      () => {},
    );
    return () => {
      cancelled = true;
    };
  }, [dealer, vuln, bids]);

  // --- Trial bids (hover preview) ---
  // Batch-fetch analyses for all legal bids so hovering is instant.
  // Re-fetches whenever the auction changes (new bids alter which
  // bids are legal and what each would mean in the current position).
  const legalBidsKey = legalBids.join(",");

  useEffect(() => {
    setBidAnalyses(null);
    setHoveredBid(null);

    if (isComplete || legalBids.length === 0) return;

    let cancelled = false;
    async function fetchAnalyses() {
      try {
        const result = await analyzeAllBids(dealer, vuln, bids);
        if (!cancelled) setBidAnalyses(result);
      } catch {
        // Trial bids are a nice-to-have, not critical.
      }
    }
    fetchAnalyses();
    return () => { cancelled = true; };
  }, [dealer, vuln, legalBidsKey, isComplete]);

  // Look up the hovered bid's analysis from the cached batch response.
  const hoveredAnalysis =
    hoveredBid && bidAnalyses ? bidAnalyses.analyses[hoveredBid] ?? null : null;

  // --- Bid handlers ---
  const handleBidClick = useCallback(
    (bid: string) => {
      setBids((prev) => [...prev, bid]);
      setHoveredBid(null);
    },
    [],
  );

  const handleUndo = useCallback(() => {
    setBids((prev) => prev.slice(0, -1));
    setHoveredBid(null);
  }, []);

  const handleReset = useCallback(() => {
    setBids([]);
    setAnalysis(null);
    setHoveredBid(null);
  }, []);

  // Build AuctionBid[] for AuctionGrid (it expects the same shape as
  // the practice page's auction.bids).
  const auctionBids: AuctionBid[] = bids.map((bid, i) => ({
    seat: seatForBid(dealer, i),
    bid,
    explanation: null,
    matched_engine: null,
  }));

  return (
    <div className="container mx-auto px-4 py-6 pb-[50vh]">
      {/* --- Page header --- */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Auction Analyzer</h1>
        <p className="text-muted-foreground text-sm">
          Enter bids to see what each communicates about the hand.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* === Left column: setup + auction grid + player cards === */}
        <div className="flex flex-col gap-4">
          {/* Setup pickers and auction grid side by side */}
          <div className="flex items-start gap-4">
            {/* Dealer + vulnerability pickers */}
            <Card>
              <CardContent className="pt-4">
                <div className="flex flex-col gap-3">
                  <div>
                    <p className="mb-1.5 text-sm font-medium">Dealer</p>
                    <SeatPicker
                      selected={dealer}
                      onSelect={(s) => {
                        setDealer(s);
                        // Changing dealer mid-auction invalidates everything.
                        if (bids.length > 0) handleReset();
                      }}
                    />
                  </div>
                  <div>
                    <p className="mb-1.5 text-sm font-medium">Vulnerability</p>
                    <VulnPicker selected={vuln} onSelect={setVuln} />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Auction grid (same component as practice page) */}
            {bids.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Auction</CardTitle>
                </CardHeader>
                <CardContent>
                  <AuctionGrid
                    bids={auctionBids}
                    dealer={dealer}
                    currentSeat={currentSeat}
                    isComplete={isComplete}
                    yourSeat="S"
                  />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Per-player hand descriptions (what we know about each player) */}
          {analysis && (
            <div className="grid grid-cols-2 gap-3">
              {ALL_SEATS.map((seat) => {
                const desc = analysis.players[seat];
                if (!desc) return null;
                return <SeatAnalysisCard key={seat} seat={seat} description={desc} />;
              })}
            </div>
          )}
        </div>

        {/* === Right column: bid controls + undo/reset === */}
        <div className="flex flex-col gap-4">
          {!isComplete ? (
            <>
              {/* Show whose turn it is */}
              <p className="text-sm font-medium">
                {currentSeat ? `${SEAT_LABELS[currentSeat]}'s turn` : "Ready"}
              </p>
              <BidControls
                legalBids={legalBids}
                disabled={isComplete}
                onBidClick={handleBidClick}
                onBidHover={setHoveredBid}
              />
            </>
          ) : (
            <Card>
              <CardContent className="pt-4">
                <p className="text-muted-foreground text-sm">
                  Auction complete.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Hover preview: shows what the hovered bid would communicate. */}
          {hoveredAnalysis && <BidPreview analysis={hoveredAnalysis} />}

          {/* Undo / Reset buttons */}
          {bids.length > 0 && (
            <div className="flex gap-2">
              <Button variant="card" size="sm" onClick={handleUndo}>
                Undo
              </Button>
              <Button variant="card" size="sm" onClick={handleReset}>
                Reset
              </Button>
            </div>
          )}

          {/* Per-bid analysis breakdown */}
          {analysis && analysis.bid_analyses.length > 0 && (
            <BidAnalysisCard bidAnalyses={analysis.bid_analyses} />
          )}
        </div>
      </div>
    </div>
  );
}
