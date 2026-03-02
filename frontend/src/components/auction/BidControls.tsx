/**
 * Button grid for placing bids in a bridge auction.
 *
 * Layout:
 *   Top row:    [Pass]  [X]  [XX]
 *   Grid:       7 rows (levels 1-7) x 5 columns (C, D, H, S, NT)
 *
 * Each button submits a React Router <Form> with two fields:
 *   - intent: "bid" (so the action handler knows this is a bid, not a redeal)
 *   - bid: the bid string (e.g. "1S", "Pass", "X")
 *
 * Buttons for illegal bids are disabled with muted styling. The entire
 * grid is disabled when it's not the player's turn.
 *
 * Bid strings match the backend format: "1C", "2H", "3NT", "Pass", "X", "XX".
 */
import { Form, useNavigation } from "react-router";

import type { Seat } from "@/api/types";
import { SEAT_LABELS, SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface BidControlsProps {
  /** Which bids are currently legal. Illegal bids are disabled. */
  legalBids: string[];
  /** If true, all buttons are disabled (not the player's turn). */
  disabled: boolean;
  /**
   * Set of bid strings currently highlighted by keyboard shortcuts.
   * When non-empty, highlighted buttons get a ring and non-highlighted
   * legal buttons are dimmed, so the highlighted ones stand out.
   */
  highlightedBids?: Set<string>;
  /** Optional extra content rendered to the right of Pass/Dbl/Rdbl row. */
  bottomRight?: React.ReactNode;
  /**
   * When set, a hidden "for_seat" field is included in the form so the
   * action handler knows this is a proxy bid for an unoccupied seat
   * (helper mode). A banner is shown above the grid.
   */
  forSeat?: Seat;
}

/**
 * The 5 suit columns in standard bidding order (low to high).
 * Each entry has the bid suffix (appended to the level number)
 * and an optional display label/color for the button text.
 */
const SUIT_COLUMNS = [
  { suffix: "C", label: SUIT_SYMBOLS.C, color: SUIT_COLORS.C },
  { suffix: "D", label: SUIT_SYMBOLS.D, color: SUIT_COLORS.D },
  { suffix: "H", label: SUIT_SYMBOLS.H, color: SUIT_COLORS.H },
  { suffix: "S", label: SUIT_SYMBOLS.S, color: SUIT_COLORS.S },
  { suffix: "NT", label: "NT", color: null },
] as const;

/** The 7 bid levels (1 through 7). */
const LEVELS = [1, 2, 3, 4, 5, 6, 7] as const;

export default function BidControls({
  legalBids,
  disabled,
  highlightedBids,
  bottomRight,
  forSeat,
}: BidControlsProps) {
  /**
   * useNavigation() tells us if a form submission is in flight.
   * While submitting, we disable all buttons to prevent double-clicks.
   */
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  /** True if a specific bid string is legal and the controls are active. */
  const isLegal = (bid: string) => !disabled && legalBids.includes(bid);

  /** Whether any keyboard highlight is active (used to dim non-highlighted). */
  const anyHighlighted = highlightedBids != null && highlightedBids.size > 0;

  return (
    <Form method="post">
      {/*
       * Hidden field tells the action handler this is a bid submission
       * (as opposed to a "redeal" intent, which uses a different form).
       */}
      <input type="hidden" name="intent" value="bid" />
      {/* In helper mode, for_seat tells the backend which unoccupied seat
       * this proxy bid is for. Omitted for normal (own-seat) bids. */}
      {forSeat && <input type="hidden" name="for_seat" value={forSeat} />}

      <div className="flex flex-col gap-3">
        {/* Banner shown when proxy-bidding for an unoccupied seat */}
        {forSeat && (
          <div className="rounded-md bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700">
            Bidding for {SEAT_LABELS[forSeat]}
          </div>
        )}

        {/*
         * --- 7x5 bid grid ---
         * Rows = levels (1-7), Columns = suits (C, D, H, S, NT).
         * CSS grid with 5 equal columns for clean alignment.
         */}
        <div className="grid grid-cols-5 gap-1">
          {LEVELS.map((level) =>
            SUIT_COLUMNS.map((col) => {
              // Build the bid string the backend expects (e.g. "1C", "3NT").
              const bid = `${level}${col.suffix}`;
              // Display: level number + suit symbol (e.g. "1♠", "3NT").
              const label = `${level}${col.label}`;

              return (
                <BidButton
                  key={bid}
                  bid={bid}
                  label={label}
                  className={col.color ?? undefined}
                  legal={isLegal(bid)}
                  submitting={isSubmitting}
                  highlighted={highlightedBids?.has(bid) ?? false}
                  anyHighlighted={anyHighlighted}
                />
              );
            }),
          )}
        </div>

        {/* --- Bottom row: Pass, Double, Redouble + optional extra content --- */}
        <div className="flex items-center gap-2">
          <BidButton
            bid="Pass"
            label="Pass"
            legal={isLegal("Pass")}
            submitting={isSubmitting}
            highlighted={highlightedBids?.has("Pass") ?? false}
            anyHighlighted={anyHighlighted}
          />
          <BidButton
            bid="X"
            label="Dbl"
            className="text-red-600"
            legal={isLegal("X")}
            submitting={isSubmitting}
            highlighted={highlightedBids?.has("X") ?? false}
            anyHighlighted={anyHighlighted}
          />
          <BidButton
            bid="XX"
            label="Rdbl"
            className="text-blue-600"
            legal={isLegal("XX")}
            submitting={isSubmitting}
            highlighted={highlightedBids?.has("XX") ?? false}
            anyHighlighted={anyHighlighted}
          />
          {/* Push extra content to the right */}
          {bottomRight && <div className="ml-auto">{bottomRight}</div>}
        </div>
      </div>
    </Form>
  );
}

/**
 * A single bid button. When clicked, it submits the enclosing <Form>
 * with name="bid" and value={bid}. The action handler reads this value
 * from FormData to know which bid the player chose.
 *
 * Disabled buttons (illegal bids or submitting) get low opacity and
 * are not clickable (pointer-events-none via the Button component).
 *
 * When keyboard highlights are active, highlighted buttons get a
 * prominent ring and non-highlighted legal buttons are dimmed, making
 * the highlighted ones visually obvious.
 */
function BidButton({
  bid,
  label,
  className,
  legal,
  submitting,
  highlighted,
  anyHighlighted,
}: {
  /** The bid string sent to the backend (e.g. "1S", "Pass"). */
  bid: string;
  /** The display text on the button (e.g. "1♠", "Pass"). */
  label: string;
  /** Optional Tailwind color class for the button text. */
  className?: string;
  /** Whether this bid is currently legal. */
  legal: boolean;
  /** Whether a form submission is in flight (disables all buttons). */
  submitting: boolean;
  /** Whether this specific button is highlighted by a keyboard shortcut. */
  highlighted: boolean;
  /** Whether any button in the grid is highlighted (used to dim others). */
  anyHighlighted: boolean;
}) {
  return (
    <Button
      type="submit"
      name="bid"
      value={bid}
      variant="outline"
      size="sm"
      disabled={!legal || submitting}
      className={cn(
        "font-semibold",
        legal
          ? [
              className,
              // When highlights are active, dim non-highlighted legal buttons.
              anyHighlighted && !highlighted && "opacity-50",
              // Highlighted buttons get a ring to stand out.
              highlighted && "ring-2 ring-primary",
            ]
          : "opacity-30",
      )}
    >
      {label}
    </Button>
  );
}
