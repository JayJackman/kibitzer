/**
 * Displays a 13-card bridge hand grouped by suit, inside a shadcn Card.
 *
 * Four CardRow components are stacked vertically (spades, hearts, diamonds,
 * clubs -- the standard display order). If an `evaluation` prop is provided,
 * hand metrics (HCP, total points, shape, balanced/unbalanced) are shown
 * below the cards in a compact summary line.
 *
 * Used on the practice page to show the player's dealt hand.
 */
import type { Hand, HandEvaluation } from "@/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import CardRow from "./CardRow";

interface HandDisplayProps {
  /** The hand to display (cards grouped by suit). */
  hand: Hand;
  /** Optional hand metrics shown below the cards. */
  evaluation?: HandEvaluation;
  /** Optional title shown above the cards (e.g. "Your Hand", "North"). */
  title?: string;
  /** Optional extra Tailwind classes on the outer Card. */
  className?: string;
}

export default function HandDisplay({
  hand,
  evaluation,
  title,
  className,
}: HandDisplayProps) {
  return (
    <Card className={cn("w-full", className)}>
      {/* Only render the header if a title is provided */}
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}

      <CardContent className="flex flex-col gap-1">
        {/* Four suit rows in standard display order: S, H, D, C */}
        <CardRow suit="S" ranks={hand.spades} />
        <CardRow suit="H" ranks={hand.hearts} />
        <CardRow suit="D" ranks={hand.diamonds} />
        <CardRow suit="C" ranks={hand.clubs} />

        {/* Optional evaluation summary below the cards */}
        {evaluation && (
          <div className="text-muted-foreground mt-2 border-t pt-2 text-xs">
            <span>{evaluation.hcp} HCP</span>
            <span className="mx-1">/</span>
            <span>{evaluation.total_points} pts</span>
            <span className="mx-1">/</span>
            <span>{evaluation.shape.join("-")}</span>
            <span className="mx-1">/</span>
            <span>{evaluation.is_balanced ? "bal" : "unbal"}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
