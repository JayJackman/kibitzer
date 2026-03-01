/**
 * A single suit row: colored suit symbol followed by space-separated ranks.
 *
 * Renders something like: ♠ A K J 5 2
 * Both the symbol and ranks are colored using the suit's Tailwind class
 * from SUIT_COLORS (e.g. blue for spades, red for hearts).
 *
 * If the suit has no cards, renders just the symbol with a dash: ♠ —
 */
import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** The four suit keys used in Hand and in constants. */
type Suit = "S" | "H" | "D" | "C";

interface CardRowProps {
  /** Which suit this row displays. */
  suit: Suit;
  /** Rank strings for this suit, e.g. ["A", "K", "J", "5", "2"]. */
  ranks: string[];
  /** Optional extra Tailwind classes on the wrapper. */
  className?: string;
}

export default function CardRow({ suit, ranks, className }: CardRowProps) {
  const color = SUIT_COLORS[suit];
  const symbol = SUIT_SYMBOLS[suit];

  return (
    <div className={cn("flex items-center gap-1.5 font-mono text-sm", className)}>
      {/* Suit symbol (always shown, slightly larger for visual weight) */}
      <span className={cn(color, "text-base leading-none")}>{symbol}</span>

      {/* Rank characters, or a dash if the suit is void */}
      <span className={color}>
        {ranks.length > 0 ? ranks.join(" ") : "\u2014"}
      </span>
    </div>
  );
}
