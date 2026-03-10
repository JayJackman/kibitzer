/**
 * Displays what we know about a single player's hand based on
 * auction analysis -- HCP range, suit lengths, balanced/unbalanced.
 *
 * Shows "Unknown" when no constraints have been inferred yet
 * (e.g. the player hasn't bid, or only passed). Otherwise lists
 * each constraint as a short text line (from formatHandDescription).
 *
 * Used in the Auction Analyzer page's per-player grid. Could also
 * be reused on the practice page if we add hand descriptions there.
 */
import type { HandDescription, Seat } from "@/api/types";
import { constraintColor, formatHandDescription, isUnconstrained } from "@/lib/handDescription";
import { SEAT_LABELS } from "@/lib/constants";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface SeatAnalysisCardProps {
  seat: Seat;
  description: HandDescription;
}

export default function SeatAnalysisCard({ seat, description }: SeatAnalysisCardProps) {
  const constraints = formatHandDescription(description);
  const unconstrained = isUnconstrained(description);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-med">{SEAT_LABELS[seat]}</CardTitle>
      </CardHeader>
      <CardContent>
        {unconstrained ? (
          <p className="text-card-muted-foreground text-s">Unknown</p>
        ) : (
          <ul className="space-y-0.5">
            {constraints.map((c, i) => (
              <li key={i} className="text-s">
                - <span className={constraintColor(c, "")}>{c.text}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
