/**
 * Running auction history showing every bid with explanations.
 *
 * Each bid row shows the seat name, bid, explanation, and -- for player bids --
 * a green/amber indicator of whether the bid matched the engine's recommendation.
 * Pass bids are filtered out to keep the history compact.
 */
import type { AuctionBid, Seat } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AuctionHistoryProps {
  /** Bid history in chronological order. */
  bids: AuctionBid[];
  /** The player's seat (used to highlight their bids). */
  yourSeat: Seat;
}

export default function AuctionHistory({ bids, yourSeat }: AuctionHistoryProps) {
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
