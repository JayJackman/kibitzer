/**
 * Shared bridge domain utilities used across frontend components.
 *
 * Centralises bid formatting, seat lists, and HCP calculation so
 * they aren't duplicated in Practice.tsx, AuctionGrid, AdvicePanel, etc.
 */
import type { Hand, Seat } from "@/api/types";
import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";

/** All four seats in compass order. */
export const ALL_SEATS: Seat[] = ["N", "E", "S", "W"];

/**
 * Format a bid string for display: replace the trailing suit letter
 * with its Unicode symbol and return the matching Tailwind color class.
 *
 * Examples:
 *   "1S"   -> { text: "1♠",   color: "text-suit-spades" }
 *   "3NT"  -> { text: "3NT",  color: null }
 *   "Pass" -> { text: "Pass", color: null }
 */
export function formatBid(bid: string): { text: string; color: string | null } {
  const last = bid[bid.length - 1];
  if (last === "S" || last === "H" || last === "D" || last === "C") {
    return {
      text: bid.slice(0, -1) + SUIT_SYMBOLS[last],
      color: SUIT_COLORS[last],
    };
  }
  return { text: bid, color: null };
}

/** HCP values for each rank (A=4, K=3, Q=2, J=1, others=0).
 *  Mirrors backend evaluate.py -- safe to duplicate since HCP values are universal. */
const HCP_VALUES: Record<string, number> = { A: 4, K: 3, Q: 2, J: 1 };

/** Count high-card points from a Hand's four suit arrays. */
export function countHcp(hand: Hand): number {
  return [hand.spades, hand.hearts, hand.diamonds, hand.clubs]
    .flat()
    .reduce((sum, rank) => sum + (HCP_VALUES[rank] ?? 0), 0);
}

/** Placeholder hand with empty suits, used when a seat's hand isn't set. */
export const EMPTY_HAND: Hand = { spades: [], hearts: [], diamonds: [], clubs: [] };

/** Arrow pointing from the center of the compass toward the declarer's seat. */
export const DECLARER_ARROW: Record<Seat, string> = {
  N: "\u2191",  // up
  S: "\u2193",  // down
  W: "\u2190",  // left
  E: "\u2192",  // right
};
