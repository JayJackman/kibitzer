/**
 * Displays the per-bid analysis breakdown for an auction.
 *
 * For each bid, shows:
 *   - The bid itself (colored by suit via BidText)
 *   - What the bid promises (HCP range, suit lengths, etc.)
 *   - Which rules matched (italic explanations below)
 *
 * When rules matched but the combined promise is unconstrained
 * (e.g. Garbage Stayman unions with Regular Stayman), shows
 * "No specific promises" instead of the misleading "No matching rules".
 *
 * Used by the Analyzer page. Could also be added to the practice page
 * to show a post-auction breakdown.
 */
import type { BidAnalysis } from "@/api/types";
import { constraintColor, formatHandDescription } from "@/lib/handDescription";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import BidText from "@/components/ui/BidText";

interface BidAnalysisCardProps {
  /** The list of per-bid analyses to display. */
  bidAnalyses: BidAnalysis[];
}

export default function BidAnalysisCard({ bidAnalyses }: BidAnalysisCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Bid Analysis</CardTitle>
        <CardDescription>
          What each bid communicated.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {bidAnalyses.map((ba, i) => {
            const constraints = formatHandDescription(ba.promise);
            return (
              <div key={i} className="border-b pb-2 last:border-b-0">
                <p className="text-sm font-medium"><BidText bid={ba.bid} /></p>
                {constraints.length > 0 ? (
                  <ul className="text-xs space-y-0.5">
                    {constraints.map((c, j) => (
                      <li key={j} className={constraintColor(c)}>{c.text}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-card-muted-foreground text-xs">
                    {ba.matches.length > 0
                      ? "No specific promises (unconstrained)"
                      : "No matching rules"}
                  </p>
                )}
                {ba.matches.length > 0 && (
                  <p className="text-card-muted-foreground mt-0.5 text-xs italic">
                    {ba.matches.map((m) => m.explanation).join(" · ")}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
