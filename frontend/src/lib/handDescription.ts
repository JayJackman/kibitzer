/**
 * Formatting utilities for HandDescription objects from the analyze API.
 *
 * Converts the structured Bound/HandDescription types into human-readable
 * strings like "12+ HCP", "5-8 Hearts", "Balanced". Used by the bid
 * preview panel and the auction analyzer page to display what a bid
 * communicates about a player's hand.
 */
import type { Bound, HandDescription } from "../api/types";

/** Suit key -> display name with proper capitalization. */
const SUIT_LABELS: Record<string, string> = {
  spades: "Spades",
  hearts: "Hearts",
  diamonds: "Diamonds",
  clubs: "Clubs",
  notrump: "NT",
};

/**
 * Format a Bound as a human-readable range string.
 *
 * Examples:
 *   { min: 12, max: null } + "HCP"   -> "12+ HCP"
 *   { min: 15, max: 17 }   + "HCP"   -> "15-17 HCP"
 *   { min: 5, max: null }  + "Spades" -> "5+ Spades"
 *   { min: null, max: 3 }  + "Hearts" -> "0-3 Hearts"
 *   { min: null, max: null }          -> null (unconstrained)
 */
export function formatBound(bound: Bound, label: string): string | null {
  const { min, max } = bound;

  // Fully unconstrained -- nothing to say.
  if (min === null && max === null) return null;

  // Exact value (min == max).
  if (min !== null && max !== null && min === max) return `${min} ${label}`;

  // Open-ended: "12+ HCP"
  if (min !== null && max === null) return `${min}+ ${label}`;

  // Upper-bounded only: "0-3 Hearts"
  if (min === null && max !== null) return `0-${max} ${label}`;

  // Full range: "15-17 HCP"
  return `${min}-${max} ${label}`;
}

/**
 * Format a HandDescription into a list of human-readable constraint strings.
 *
 * Returns an array like:
 *   ["12+ HCP", "5+ Spades", "Balanced"]
 *
 * Empty array means fully unconstrained (we know nothing).
 */
export function formatHandDescription(desc: HandDescription): string[] {
  const parts: string[] = [];

  // HCP range.
  const hcp = formatBound(desc.hcp, "HCP");
  if (hcp) parts.push(hcp);

  // Total points range (only show if different from HCP).
  const pts = formatBound(desc.total_pts, "points");
  if (pts && pts !== hcp?.replace("HCP", "points")) parts.push(pts);

  // Suit lengths.
  for (const [suit, bound] of Object.entries(desc.lengths)) {
    const label = SUIT_LABELS[suit] ?? suit;
    const text = formatBound(bound, label);
    if (text) parts.push(text);
  }

  // Balanced / unbalanced.
  if (desc.balanced === true) parts.push("Balanced");
  if (desc.balanced === false) parts.push("Unbalanced");

  return parts;
}

/**
 * Check whether a HandDescription has any constraints at all.
 * Returns true if everything is unconstrained (we know nothing).
 */
export function isUnconstrained(desc: HandDescription): boolean {
  return formatHandDescription(desc).length === 0;
}
