/**
 * Summary displayed when a rubber is complete.
 *
 * Shows the final totals, rubber bonus, margin of victory,
 * and a "New Rubber" button to start fresh.
 */
import type { RubberState } from "@/api/types";
import { Button } from "@/components/ui/button";

interface RubberSummaryProps {
  scoring: RubberState;
  onNewRubber: () => Promise<void>;
}

export default function RubberSummary({ scoring, onNewRubber }: RubberSummaryProps) {
  const nsWon = scoring.ns_games_won >= 2;
  const winner = nsWon ? "NS" : "EW";
  const margin = Math.abs(scoring.ns_total - scoring.ew_total);

  return (
    <div className="bg-muted mt-4 rounded-md p-4 text-center">
      <div className="mb-1 text-lg font-bold">
        Rubber Complete!
      </div>
      <div className="text-sm">
        <span className="font-semibold">{winner}</span> wins by{" "}
        <span className="font-semibold">{margin}</span> points
      </div>
      <div className="text-muted-foreground mt-1 text-xs">
        Games: NS {scoring.ns_games_won} - EW {scoring.ew_games_won}
        {" | "}
        Rubber bonus: {scoring.rubber_bonus}
      </div>
      <div className="text-muted-foreground mt-1 text-xs">
        NS total: {scoring.ns_total} | EW total: {scoring.ew_total}
      </div>
      <Button
        variant="outline"
        size="sm"
        className="mt-3"
        onClick={onNewRubber}
      >
        New Rubber
      </Button>
    </div>
  );
}
