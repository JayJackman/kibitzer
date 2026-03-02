/**
 * Bridge-specific display constants.
 *
 * Suit symbols and colors for rendering cards, bids, and auctions
 * in the browser. These match the symbols used in the CLI (display.py)
 * so the experience is consistent across interfaces.
 */

/** Unicode suit symbols for display. */
export const SUIT_SYMBOLS = {
  S: "\u2660", // ♠ spades
  H: "\u2665", // ♥ hearts
  D: "\u2666", // ♦ diamonds
  C: "\u2663", // ♣ clubs
} as const;

/**
 * Tailwind CSS color classes for each suit.
 * Uses theme variables (--suit-*) defined in index.css so colors
 * can be tuned from the theme without touching component code.
 */
export const SUIT_COLORS = {
  S: "text-suit-spades", // Spades: blue
  H: "text-suit-hearts", // Hearts: red
  D: "text-suit-diamonds", // Diamonds: orange
  C: "text-suit-clubs", // Clubs: green
} as const;

/** Seat labels for display. */
export const SEAT_LABELS = {
  N: "North",
  E: "East",
  S: "South",
  W: "West",
} as const;
