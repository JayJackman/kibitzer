/**
 * Renders a bid string with the suit symbol in its color.
 *
 * "1S" -> "1♠" (blue), "3NT" -> "3NT" (unstyled), "Pass" -> "Pass" (muted),
 * "X" -> "X" (red), "XX" -> "XX" (blue).
 *
 * Used by AuctionGrid, AdvicePanel, and AuctionHistory to display bids
 * consistently without each component re-implementing the same formatting.
 */
import { formatBid } from "@/lib/bridge";
import { cn } from "@/lib/utils";

interface BidTextProps {
  /** The bid string in backend format (e.g. "1S", "Pass", "X"). */
  bid: string;
  /** Optional extra Tailwind classes on the outer span. */
  className?: string;
}

export default function BidText({ bid, className }: BidTextProps) {
  const { text, color } = formatBid(bid);

  // Special styling for Pass, Double, and Redouble.
  if (bid === "Pass") {
    return <span className={cn("text-card-muted-foreground", className)}>{text}</span>;
  }
  if (bid === "X") {
    return <span className={cn("font-semibold text-red-600", className)}>{text}</span>;
  }
  if (bid === "XX") {
    return <span className={cn("font-semibold text-blue-600", className)}>{text}</span>;
  }

  // Suit bids get their suit color; NT bids are unstyled.
  return <span className={cn("font-semibold", color, className)}>{text}</span>;
}
