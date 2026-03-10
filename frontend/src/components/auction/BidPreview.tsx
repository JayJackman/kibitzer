/**
 * Preview panel showing what a hovered bid communicates about the hand.
 *
 * Displayed below the bid grid on the practice page. When the player
 * hovers over a legal bid button, this panel shows:
 *   - The bid's combined promise (HCP range, suit lengths, balanced/unbalanced)
 *   - Which rules matched (rule name + explanation)
 *
 * If no rules match the bid (e.g. a bid the engine doesn't recognize),
 * it shows "No matching rules" instead of constraints.
 */
import type { BidAnalysis } from "@/api/types";
import { constraintColor, formatHandDescription } from "@/lib/handDescription";
import { Card, CardContent } from "@/components/ui/card";

interface BidPreviewProps {
  /** The analysis for the currently hovered bid. */
  analysis: BidAnalysis;
}

export default function BidPreview({ analysis }: BidPreviewProps) {
  const constraints = formatHandDescription(analysis.promise);

  return (
    <Card>
      <CardContent>
        {/* Promise summary: the combined constraints from all matching rules. */}
        {constraints.length > 0 ? (
          <ul className="text-sm space-y-0.5">
            {constraints.map((c, i) => (
              <li key={i} className={constraintColor(c)}>
                {c.text}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-card-muted-foreground text-sm">
            {analysis.matches.length > 0
              ? "No specific promises (unconstrained)"
              : "No matching rules"}
          </p>
        )}

        {/* Matching rule names, shown smaller below the constraints. */}
        {analysis.matches.length > 0 && (
          <div className="text-card-muted-foreground mt-2 text-xs">
            {analysis.matches.map((m) => m.explanation).join(" · ")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
