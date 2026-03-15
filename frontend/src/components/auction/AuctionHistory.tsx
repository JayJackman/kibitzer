/**
 * Running auction history showing every bid with explanations.
 *
 * Each bid row shows the seat name, bid, explanation, and -- for player bids --
 * a green/amber indicator of whether the bid matched the engine's recommendation.
 * Pass bids are filtered out to keep the history compact.
 */
import type { AuctionBid, HandDescription, Seat } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { constraintColor, formatHandDescription } from "@/lib/handDescription";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import BidText from "@/components/ui/BidText";

interface AuctionHistoryProps {
  /** Bid history in chronological order. */
  bids: AuctionBid[];
  /** The player's seat (used to highlight their bids). */
  yourSeat: Seat;
  /**
   * Optional cumulative hand descriptions from analyzeAuction().
   * One entry per non-pass bid, in auction order -- indices match the
   * filtered nonPassBids array below. Each entry is the running
   * intersection of all bids by that seat so far (e.g. after 1H + 2H,
   * shows "12+ HCP, 6+ Hearts, 0-16 Total Points" not just the 2H promise).
   * Used in helper mode to show what we know about each bidder's hand.
   */
  bidDescriptions?: HandDescription[];
}

export default function AuctionHistory({ bids, yourSeat, bidDescriptions }: AuctionHistoryProps) {
  // Filter out Pass bids, but track original indices for stable React keys.
  // Also track a running count of non-pass bids so we can index into
  // bidDescriptions (which contains one entry per non-pass bid, in order).
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
        {nonPassBids.map(({ entry, origIndex }, displayIndex) => {
          const isPlayer = entry.seat === yourSeat;
          const matched = entry.matched_engine;
          // bidDescriptions has one entry per non-pass bid in auction order,
          // matching the order of nonPassBids (pass bids with
          // matched_engine === false are rare and only appear in
          // practice mode where bidDescriptions is not provided).
          const desc = bidDescriptions?.[displayIndex];
          const constraints = desc
            ? formatHandDescription(desc)
            : [];

          return (
            <div key={origIndex} className={cn(
              "rounded px-2 py-0.5",
              isPlayer && matched === true && "bg-correct",
              isPlayer && matched === false && "bg-incorrect",
            )}>
              {/* Top line: seat, bid, explanation, match indicator */}
              <div className="flex items-baseline gap-2">
                {/* Seat label */}
                <span className={cn("w-12 shrink-0 font-medium", isPlayer && "text-primary")}>
                  {SEAT_LABELS[entry.seat]}
                </span>

                {/* Bid */}
                <BidText bid={entry.bid} />

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

              {/* Hand description constraints (helper mode, from analyzeAuction) */}
              {constraints.length > 0 && (
                <div className="ml-14 flex flex-wrap gap-x-3 text-xs">
                  {constraints.map((c, j) => (
                    <span key={j} className={constraintColor(c, "text-card-muted-foreground")}>
                      {c.text}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        </div>
      </CardContent>
    </Card>
  );
}
