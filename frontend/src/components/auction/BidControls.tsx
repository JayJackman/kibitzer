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
  /**
   * Called when the user hovers over (or leaves) a bid button.
   * Receives the bid string on enter, null on leave. Used by the
   * practice page to show a trial-bid preview panel.
   */
  onBidHover?: (bid: string | null) => void;
  /**
   * Called when a bid button is clicked (analyzer mode).
   * When provided, the component renders plain buttons instead of a
   * form -- clicks call this handler rather than submitting to the
   * action. This lets the bid grid be reused outside of React Router
   * form flows (e.g. the standalone auction analyzer page).
   */
  onBidClick?: (bid: string) => void;
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
  onBidHover,
  onBidClick,
}: BidControlsProps) {
  /**
   * useNavigation() tells us if a form submission is in flight.
   * While submitting, we disable all buttons to prevent double-clicks.
   * In click mode (onBidClick), navigation state isn't relevant, but
   * we still call the hook unconditionally to satisfy React's rules.
   */
  const navigation = useNavigation();
  const isSubmitting = !onBidClick && navigation.state === "submitting";

  /** True if a specific bid string is legal and the controls are active. */
  const isLegal = (bid: string) => !disabled && legalBids.includes(bid);

  /** Whether any keyboard highlight is active (used to dim non-highlighted). */
  const anyHighlighted = highlightedBids != null && highlightedBids.size > 0;

  /**
   * Build the bid grid + bottom row content. This is shared between
   * form mode (practice page) and click mode (analyzer page).
   */
  const gridContent = (
    <div className="flex flex-col gap-3">
      {/* --- 7x5 bid grid --- */}
      <div className="grid grid-cols-5 gap-1">
        {LEVELS.map((level) =>
          SUIT_COLUMNS.map((col) => {
            const bid = `${level}${col.suffix}`;
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
                onHover={onBidHover}
                onClick={onBidClick}
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
          onHover={onBidHover}
          onClick={onBidClick}
        />
        <BidButton
          bid="X"
          label="Dbl"
          className="text-red-600"
          legal={isLegal("X")}
          submitting={isSubmitting}
          highlighted={highlightedBids?.has("X") ?? false}
          anyHighlighted={anyHighlighted}
          onHover={onBidHover}
          onClick={onBidClick}
        />
        <BidButton
          bid="XX"
          label="Rdbl"
          className="text-blue-600"
          legal={isLegal("XX")}
          submitting={isSubmitting}
          highlighted={highlightedBids?.has("XX") ?? false}
          anyHighlighted={anyHighlighted}
          onHover={onBidHover}
          onClick={onBidClick}
        />
        {/* Proxy-bid banner + any extra content pushed to the right */}
        {(forSeat || bottomRight) && (
          <div className="ml-auto flex items-center gap-2">
            {forSeat && (
              <span className="rounded-md border-2 bg-card px-3 py-1.5 text-sm font-medium text-card-foreground">
                Bidding for {SEAT_LABELS[forSeat]}
              </span>
            )}
            {bottomRight}
          </div>
        )}
      </div>
    </div>
  );

  /*
   * In click mode (onBidClick is set), render a plain <div> instead of
   * a <Form>. Buttons use type="button" + onClick instead of form submit.
   * In form mode (default), wrap in a React Router <Form> for the action.
   */
  if (onBidClick) {
    return <div>{gridContent}</div>;
  }

  return (
    <Form method="post">
      <input type="hidden" name="intent" value="bid" />
      {forSeat && <input type="hidden" name="for_seat" value={forSeat} />}
      {gridContent}
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
  onHover,
  onClick,
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
  /** Called on mouse enter (bid string) / leave (null) for hover preview. */
  onHover?: (bid: string | null) => void;
  /** Called on click in analyzer mode (replaces form submit). */
  onClick?: (bid: string) => void;
}) {
  return (
    <Button
      // In click mode (onClick), use type="button" so the button doesn't
      // try to submit a form. In form mode, use type="submit".
      type={onClick ? "button" : "submit"}
      name={onClick ? undefined : "bid"}
      value={onClick ? undefined : bid}
      variant="card"
      size="sm"
      disabled={!legal || submitting}
      className={cn(
        "font-semibold",
        legal
          ? [
              className,
              anyHighlighted && !highlighted && "opacity-50",
              highlighted && "ring-2 ring-primary",
            ]
          : "opacity-30",
      )}
      // Hover handlers for trial-bid preview (only fire for legal bids).
      onMouseEnter={onHover && legal ? () => onHover(bid) : undefined}
      onMouseLeave={onHover && legal ? () => onHover(null) : undefined}
      // Click handler for analyzer mode.
      onClick={onClick && legal ? () => onClick(bid) : undefined}
    >
      {label}
    </Button>
  );
}
