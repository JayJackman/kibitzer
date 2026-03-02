/**
 * 4-column bid history table for a bridge auction.
 *
 * Columns are always in compass order: N, E, S, W. Bids are placed
 * left-to-right, top-to-bottom, starting with the dealer. Empty cells
 * pad the first row before the dealer's column (e.g., if dealer is East,
 * North gets an empty cell in row 1).
 *
 * Each bid cell is colored by suit using the shared BidText component.
 * When the auction is still active, the current seat's next cell shows
 * a "?" marker. Completed auctions show no marker.
 *
 * The grid uses a simple HTML table for clean alignment of the 4 columns.
 */
import type { AuctionBid, Seat } from "@/api/types";
import { ALL_SEATS } from "@/lib/bridge";
import { cn } from "@/lib/utils";
import BidText from "@/components/ui/BidText";

/**
 * Rotate ALL_SEATS so that `yourSeat` is the rightmost (last) column.
 * The seat to the left of the player (i.e. the next seat clockwise)
 * becomes the leftmost column.
 *
 * Example: yourSeat = "S" -> columns = ["W", "N", "E", "S"]
 */
function columnsForSeat(yourSeat: Seat): Seat[] {
  const idx = ALL_SEATS.indexOf(yourSeat);
  // Start from the seat after ours (wrapping around).
  return [
    ALL_SEATS[(idx + 1) % 4],
    ALL_SEATS[(idx + 2) % 4],
    ALL_SEATS[(idx + 3) % 4],
    ALL_SEATS[idx],
  ];
}

interface AuctionGridProps {
  /** Bid history in chronological order. */
  bids: AuctionBid[];
  /** Who dealt (determines where the first bid appears). */
  dealer: Seat;
  /** Whose turn it is, or null if the auction is complete. */
  currentSeat: Seat | null;
  /** Whether the auction has finished (3 consecutive passes after a bid, or 4 initial passes). */
  isComplete: boolean;
  /** The player's seat -- displayed as the rightmost column. */
  yourSeat: Seat;
}

/**
 * A single cell in the auction grid. Tagged union so the renderer can
 * switch cleanly without comparing against magic strings.
 */
type GridCell =
  | { kind: "empty" }
  | { kind: "bid"; data: AuctionBid }
  | { kind: "pending" };

/**
 * Build the flat list of grid cells from the bid history.
 *
 * 1. Pad with empty cells before the dealer's column (e.g., if dealer is
 *    East, North gets one empty cell in the first row).
 * 2. Add all actual bids.
 * 3. If the auction is still active, add a "pending" marker for the
 *    current seat.
 */
function buildCells(
  bids: AuctionBid[],
  dealer: Seat,
  currentSeat: Seat | null,
  isComplete: boolean,
  columns: Seat[],
): GridCell[] {
  const dealerIndex = columns.indexOf(dealer);
  const cells: GridCell[] = [];

  // Pad with empty cells up to the dealer's column.
  for (let i = 0; i < dealerIndex; i++) {
    cells.push({ kind: "empty" });
  }

  // Add all actual bids.
  for (const bid of bids) {
    cells.push({ kind: "bid", data: bid });
  }

  // If the auction isn't complete, add a "pending" marker.
  if (!isComplete && currentSeat) {
    cells.push({ kind: "pending" });
  }

  return cells;
}

/**
 * Split a flat cell list into rows of exactly 4, padding any short
 * final row with empty cells. This guarantees every row has 4 cells,
 * so the renderer doesn't need a separate trailing-pad step.
 */
function buildRows(cells: GridCell[]): GridCell[][] {
  const rows: GridCell[][] = [];
  for (let i = 0; i < cells.length; i += 4) {
    rows.push(cells.slice(i, i + 4));
  }

  // Pad the last row to 4 cells.
  const last = rows[rows.length - 1];
  if (last) {
    while (last.length < 4) {
      last.push({ kind: "empty" });
    }
  }

  return rows;
}

export default function AuctionGrid({
  bids,
  dealer,
  currentSeat,
  isComplete,
  yourSeat,
}: AuctionGridProps) {
  const columns = columnsForSeat(yourSeat);
  const cells = buildCells(bids, dealer, currentSeat, isComplete, columns);
  const rows = buildRows(cells);

  return (
    <table className="w-full text-center text-sm">
      {/* Column headers rotated so yourSeat is rightmost. */}
      <thead>
        <tr>
          {columns.map((seat) => (
            <th
              key={seat}
              className={cn(
                "px-3 py-1 font-medium",
                // Highlight the current bidder's column header.
                !isComplete && currentSeat === seat && "text-primary",
              )}
            >
              {seat}
            </th>
          ))}
        </tr>
      </thead>

      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowIndex} className="border-t border-border/50">
            {row.map((cell, colIndex) => (
              <td key={colIndex} className="px-3 py-1">
                {cell.kind === "empty" && <span />}
                {cell.kind === "pending" && (
                  <span className="text-card-muted-foreground animate-pulse">?</span>
                )}
                {cell.kind === "bid" && <BidText bid={cell.data.bid} />}
              </td>
            ))}
          </tr>
        ))}

        {/* If no bids yet, show an empty state row. */}
        {rows.length === 0 && (
          <tr>
            <td
              colSpan={4}
              className="text-card-muted-foreground px-3 py-4 text-center"
            >
              No bids yet
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
