/**
 * 4-column bid history table for a bridge auction.
 *
 * Columns are always in compass order: N, E, S, W. Bids are placed
 * left-to-right, top-to-bottom, starting with the dealer. Empty cells
 * pad the first row before the dealer's column (e.g., if dealer is East,
 * North gets an empty cell in row 1).
 *
 * Each bid cell is colored by suit using SUIT_COLORS. When the auction
 * is still active, the current seat's next cell shows a "?" marker.
 * Completed auctions show no marker.
 *
 * The grid uses a simple HTML table for clean alignment of the 4 columns.
 */
import type { AuctionBid, Seat } from "@/api/types";
import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** Column order for the auction grid (standard bridge display). */
const COLUMNS = ["N", "E", "S", "W"] as const;

interface AuctionGridProps {
  /** Bid history in chronological order. */
  bids: AuctionBid[];
  /** Who dealt (determines where the first bid appears). */
  dealer: Seat;
  /** Whose turn it is, or null if the auction is complete. */
  currentSeat: Seat | null;
  /** Whether the auction has finished (3 consecutive passes after a bid, or 4 initial passes). */
  isComplete: boolean;
}

/**
 * Extract the suit letter from a bid string for coloring.
 * Returns the suit key ("S", "H", "D", "C") or null for Pass/X/XX.
 */
function bidSuit(bid: string): "S" | "H" | "D" | "C" | null {
  // Suit bids look like "1S", "3NT", "2H", etc.
  // The suit letter is the last character for single-suit bids.
  const last = bid[bid.length - 1];
  if (last === "S" || last === "H" || last === "D" || last === "C") {
    return last;
  }
  // NT bids and special bids (Pass, X, XX) have no single suit color.
  return null;
}

/**
 * Render a single bid cell with suit coloring and symbol substitution.
 * "1S" becomes "1♠", "Pass" stays "Pass", etc.
 */
function BidCell({ bid }: { bid: string }) {
  const suit = bidSuit(bid);

  if (suit) {
    // Replace the trailing suit letter with the Unicode symbol.
    // e.g., "1S" -> "1" + "♠", "3NT" won't match (suit is null).
    const level = bid.slice(0, -1);
    const symbol = SUIT_SYMBOLS[suit];
    const color = SUIT_COLORS[suit];

    return (
      <span className={cn("font-semibold", color)}>
        {level}
        {symbol}
      </span>
    );
  }

  // Non-suit bids: Pass, X (double), XX (redouble), NT bids
  if (bid === "Pass") {
    return <span className="text-muted-foreground">Pass</span>;
  }
  if (bid === "X") {
    return <span className="font-semibold text-red-600">X</span>;
  }
  if (bid === "XX") {
    return <span className="font-semibold text-blue-600">XX</span>;
  }
  // NT bids (e.g., "1NT", "3NT")
  return <span className="font-semibold">{bid}</span>;
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
): GridCell[] {
  const dealerIndex = COLUMNS.indexOf(dealer);
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
}: AuctionGridProps) {
  const cells = buildCells(bids, dealer, currentSeat, isComplete);
  const rows = buildRows(cells);

  return (
    <table className="w-full text-center text-sm">
      {/* Column headers: N, E, S, W */}
      <thead>
        <tr>
          {COLUMNS.map((seat) => (
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
                  <span className="text-muted-foreground animate-pulse">?</span>
                )}
                {cell.kind === "bid" && <BidCell bid={cell.data.bid} />}
              </td>
            ))}
          </tr>
        ))}

        {/* If no bids yet, show an empty state row. */}
        {rows.length === 0 && (
          <tr>
            <td
              colSpan={4}
              className="text-muted-foreground px-3 py-4 text-center"
            >
              No bids yet
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
