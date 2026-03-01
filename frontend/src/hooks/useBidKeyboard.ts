/**
 * Keyboard shortcut hook for bid selection in the practice page.
 *
 * Lets the user filter the bid grid by level and/or suit using keyboard
 * keys, then confirm a selection with Enter or Space. This avoids needing
 * the mouse for every bid.
 *
 * Key bindings:
 *   1-7     Filter by bid level (toggle: press again to clear)
 *   C/D/H/S Filter by suit (toggle: press again to clear)
 *   N       Filter by notrump (maps to "NT" internally)
 *   P       Highlight Pass (toggle)
 *   X       Highlight Double or Redouble (whichever is legal), toggle off
 *   Enter   Confirm the highlighted bid (only if exactly one)
 *   Space   Same as Enter
 *   Escape  Clear all filters
 *
 * Combining keys narrows the filter. For example:
 *   2 then H → highlights only 2H (if legal)
 *   H then 2 → same result (order doesn't matter)
 *   2 then 3 → level replaces: highlights all 3-level bids
 *
 * Filters automatically reset when:
 *   - The hook is disabled (not the player's turn)
 *   - The legal bids list changes (new turn after bidding)
 */
import { useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface UseBidKeyboardOptions {
  /** The list of currently legal bid strings (e.g. ["1C", "1D", ..., "Pass"]). */
  legalBids: string[];
  /** Whether keyboard shortcuts are active (only when it's the player's turn). */
  enabled: boolean;
  /** Called when the user confirms a highlighted bid via Enter/Space. */
  onConfirm: (bid: string) => void;
}

/** Internal filter state. Two independent axes plus a special-bid override. */
interface KeyboardFilterState {
  /** Active level filter (1-7), or null if no level is selected. */
  activeLevel: number | null;
  /** Active suit filter ("C", "D", "H", "S", "NT"), or null if none. */
  activeSuit: string | null;
  /** Special bid override ("Pass", "X", "XX"), or null. Clears level/suit. */
  special: "Pass" | "X" | "XX" | null;
}

const INITIAL_STATE: KeyboardFilterState = {
  activeLevel: null,
  activeSuit: null,
  special: null,
};

// ---------------------------------------------------------------------------
// Highlighted bids computation
// ---------------------------------------------------------------------------

/**
 * Compute which bids should be highlighted given the current filter state
 * and the list of legal bids.
 *
 * - If a special key is active (Pass/X/XX), highlight just that bid.
 * - Otherwise, filter the legal suit bids by the active level and/or suit.
 * - If no filters are active, return an empty set (nothing highlighted).
 */
function computeHighlightedBids(
  state: KeyboardFilterState,
  legalBids: string[],
): Set<string> {
  const { activeLevel, activeSuit, special } = state;

  // No filters active → nothing highlighted.
  if (activeLevel === null && activeSuit === null && special === null) {
    return new Set();
  }

  // Special key overrides level/suit — highlight just that one bid.
  if (special !== null) {
    return legalBids.includes(special) ? new Set([special]) : new Set();
  }

  // Filter suit bids (like "1C", "3NT") by level and/or suit.
  return new Set(
    legalBids.filter((bid) => {
      // Skip non-suit bids (Pass, X, XX) — they're handled by special keys.
      if (bid === "Pass" || bid === "X" || bid === "XX") return false;

      // Parse the bid: first char is the level digit, rest is the suit.
      const level = parseInt(bid[0], 10);
      const suit = bid.slice(1); // "C", "D", "H", "S", or "NT"

      if (activeLevel !== null && level !== activeLevel) return false;
      if (activeSuit !== null && suit !== activeSuit) return false;

      return true;
    }),
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useBidKeyboard({
  legalBids,
  enabled,
  onConfirm,
}: UseBidKeyboardOptions): { highlightedBids: Set<string> } {
  const [state, setState] = useState<KeyboardFilterState>(INITIAL_STATE);

  // Reset filters when the hook is disabled (not the player's turn).
  useEffect(() => {
    if (!enabled) {
      setState(INITIAL_STATE);
    }
  }, [enabled]);

  // Reset filters when the legal bids change (new turn after a bid).
  // We join the array into a string so useEffect can compare by value.
  const legalBidsKey = legalBids.join(",");
  useEffect(() => {
    setState(INITIAL_STATE);
  }, [legalBidsKey]);

  // Compute highlighted bids from the current filter state.
  const highlightedBids = computeHighlightedBids(state, legalBids);

  // Refs to avoid stale closures in the keydown handler.
  // The handler is attached once (per enabled change) but needs access
  // to the latest values of these variables.
  const highlightedRef = useRef(highlightedBids);
  highlightedRef.current = highlightedBids;
  const onConfirmRef = useRef(onConfirm);
  onConfirmRef.current = onConfirm;
  const legalBidsRef = useRef(legalBids);
  legalBidsRef.current = legalBids;

  useEffect(() => {
    if (!enabled) return;

    function handleKeyDown(e: KeyboardEvent) {
      // Don't intercept keystrokes aimed at text inputs.
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      const key = e.key.toUpperCase();

      // --- Level keys: 1-7 ---
      // Toggle the level filter. Pressing the same level again clears it.
      // Pressing a different level replaces the previous one.
      // Clears any active special key (level/suit and special are exclusive).
      if (key >= "1" && key <= "7") {
        const level = parseInt(key, 10);
        e.preventDefault();
        setState((prev) => {
          // Can always toggle off
          if (prev.activeLevel === level) {
            return {activeLevel: null, activeSuit: prev.activeSuit, special: null };
          }
          const candidate = {activeLevel:  level, activeSuit: prev.activeSuit, special: null };
          if (computeHighlightedBids(candidate, legalBidsRef.current).size === 0) {
            return prev;
          }
          return candidate;
        })
        return;
      }

      // --- Suit keys: C, D, H, S, N (N maps to "NT") ---
      // Same toggle/replace behavior as level keys.
      if ("CDHSN".includes(key) && key.length === 1) {
        const suit = key === "N" ? "NT" : key;
        e.preventDefault();
        setState((prev) => {
          // Can always toggle off
          if (prev.activeSuit === suit) {
            return {activeLevel: prev.activeLevel, activeSuit: null, special: null };
          }
          const candidate = {activeLevel:  prev.activeLevel, activeSuit: suit, special: null };
          if (computeHighlightedBids(candidate, legalBidsRef.current).size === 0) {
            return prev;
          }
          return candidate;
        })
      }

      // --- Pass: toggle on/off ---
      if (key === "P") {
        e.preventDefault();
        setState((prev) => ({
          activeLevel: null,
          activeSuit: null,
          special: prev.special === "Pass" ? null : "Pass",
        }));
        return;
      }

      // --- Double / Redouble: highlight whichever is legal, toggle off ---
      // In bridge, X and XX are mutually exclusive -- you can never have
      // both available. So X just highlights whichever one is in legalBids.
      if (key === "X") {
        e.preventDefault();
        const bids = legalBidsRef.current;
        const target = bids.includes("X") ? "X" : bids.includes("XX") ? "XX" : null;
        setState((prev) => {
          // Toggle off if already highlighting the target.
          if (prev.special === target) {
            return INITIAL_STATE;
          }
          if (target === null) {
            return INITIAL_STATE;
          }
          return { activeLevel: null, activeSuit: null, special: target };
        });
        return;
      }

      // --- Enter / Space: confirm if exactly one bid is highlighted ---
      if (key === "ENTER" || key === " ") {
        const current = highlightedRef.current;
        if (current.size === 1) {
          const bid = [...current][0];
          e.preventDefault();
          onConfirmRef.current(bid);
          setState(INITIAL_STATE);
        }
        return;
      }

      // --- Escape: clear all filters ---
      if (key === "ESCAPE") {
        e.preventDefault();
        setState(INITIAL_STATE);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled]);

  return { highlightedBids };
}
