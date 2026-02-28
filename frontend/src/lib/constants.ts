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

/** Tailwind CSS color classes for each suit. */
export const SUIT_COLORS = {
  S: "text-blue-600", // Spades: blue
  H: "text-red-600", // Hearts: red
  D: "text-orange-500", // Diamonds: orange
  C: "text-green-600", // Clubs: green
} as const;

/** Seat labels for display. */
export const SEAT_LABELS = {
  N: "North",
  E: "East",
  S: "South",
  W: "West",
} as const;
