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

import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface BidControlsProps {
  /** Which bids are currently legal. Illegal bids are disabled. */
  legalBids: string[];
  /** If true, all buttons are disabled (not the player's turn). */
  disabled: boolean;
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

export default function BidControls({ legalBids, disabled }: BidControlsProps) {
  /**
   * useNavigation() tells us if a form submission is in flight.
   * While submitting, we disable all buttons to prevent double-clicks.
   */
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  /** True if a specific bid string is legal and the controls are active. */
  const isLegal = (bid: string) => !disabled && legalBids.includes(bid);

  return (
    <Form method="post">
      {/*
       * Hidden field tells the action handler this is a bid submission
       * (as opposed to a "redeal" intent, which uses a different form).
       */}
      <input type="hidden" name="intent" value="bid" />

      <div className="flex flex-col gap-3">
        {/* --- Top row: Pass, Double, Redouble --- */}
        <div className="flex gap-2">
          <BidButton
            bid="Pass"
            label="Pass"
            legal={isLegal("Pass")}
            submitting={isSubmitting}
          />
          <BidButton
            bid="X"
            label="Dbl"
            className="text-red-600"
            legal={isLegal("X")}
            submitting={isSubmitting}
          />
          <BidButton
            bid="XX"
            label="Rdbl"
            className="text-blue-600"
            legal={isLegal("XX")}
            submitting={isSubmitting}
          />
        </div>

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
                />
              );
            }),
          )}
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
 */
function BidButton({
  bid,
  label,
  className,
  legal,
  submitting,
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
        // Legal bids get their suit color; illegal bids are muted.
        legal ? className : "opacity-30",
      )}
    >
      {label}
    </Button>
  );
}
