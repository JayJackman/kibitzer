/**
 * Panel showing the engine's bid recommendation and reasoning.
 *
 * Displayed when the user clicks "Advise Me" on the practice page.
 * Uses a fetcher (non-navigation request), so the panel appears inline
 * without a full page reload.
 *
 * Layout:
 *   - Recommended bid (large, colored by suit) with explanation
 *   - Forcing badge (if the bid is forcing)
 *   - Phase label (e.g. "opening", "response")
 *   - Alternative bids (if any) with their explanations
 *   - Thought process trace (expandable rule evaluation)
 */
import type { Advice } from "@/api/types";
import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

import ThoughtProcess from "./ThoughtProcess";

interface AdvicePanelProps {
  /** The engine's advice data, or null if not yet requested. */
  advice: Advice | null;
  /** True while the fetcher is loading advice from the backend. */
  isLoading: boolean;
}

/**
 * Format a bid string for display: replace trailing suit letter with
 * the Unicode symbol. "1S" becomes "1♠", "Pass" stays "Pass", etc.
 */
function formatBid(bid: string): { text: string; color: string | null } {
  const last = bid[bid.length - 1];
  if (last === "S" || last === "H" || last === "D" || last === "C") {
    return {
      text: bid.slice(0, -1) + SUIT_SYMBOLS[last],
      color: SUIT_COLORS[last],
    };
  }
  return { text: bid, color: null };
}

export default function AdvicePanel({ advice, isLoading }: AdvicePanelProps) {
  // Don't render anything if advice hasn't been requested yet.
  if (!advice && !isLoading) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Engine Advice</CardTitle>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        {/* Loading state while the fetcher is in flight. */}
        {isLoading && (
          <p className="text-card-muted-foreground animate-pulse text-sm">
            Thinking...
          </p>
        )}

        {advice && (
          <>
            {/* --- Recommended bid --- */}
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                {/* The recommended bid, displayed large with suit coloring. */}
                <RecommendedBid bid={advice.recommended.bid} />

                {/* Forcing indicator badge. */}
                {advice.recommended.forcing && (
                  <Badge variant="outline">Forcing</Badge>
                )}

                {/* Phase label (e.g. "opening", "response"). */}
                <Badge variant="secondary">{advice.phase}</Badge>
              </div>

              {/* Rule name and explanation text. */}
              <p className="text-sm">{advice.recommended.explanation}</p>
              <p className="text-card-muted-foreground text-xs">
                Rule: {advice.recommended.rule_name}
              </p>

              {/* Alert messages from the rule (e.g. "alertable bid"). */}
              {advice.recommended.alerts.length > 0 && (
                <div className="flex gap-1">
                  {advice.recommended.alerts.map((alert, i) => (
                    <Badge key={i} variant="destructive">
                      {alert}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* --- Alternative bids --- */}
            {advice.alternatives.length > 0 && (
              <>
                <Separator />
                <div className="flex flex-col gap-2">
                  <h4 className="text-card-muted-foreground text-xs font-medium uppercase tracking-wide">
                    Alternatives
                  </h4>
                  {advice.alternatives.map((alt, i) => {
                    const { text, color } = formatBid(alt.bid);
                    return (
                      <div key={i} className="flex flex-col gap-0.5">
                        <div className="flex items-center gap-2 text-sm">
                          <span className={cn("font-semibold", color)}>
                            {text}
                          </span>
                          {alt.forcing && (
                            <Badge variant="outline" className="text-[10px]">
                              Forcing
                            </Badge>
                          )}
                        </div>
                        <p className="text-card-muted-foreground text-xs">
                          {alt.explanation}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </>
            )}

            {/* --- Thought process trace --- */}
            {advice.thought_process.steps.length > 0 && (
              <>
                <Separator />
                <ThoughtProcess steps={advice.thought_process.steps} />
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * The recommended bid displayed in a large, prominent style.
 * Suit bids get their suit color; other bids (Pass, X, XX, NT) are unstyled.
 */
function RecommendedBid({ bid }: { bid: string }) {
  const { text, color } = formatBid(bid);
  return (
    <span className={cn("text-2xl font-bold", color)}>
      {text}
    </span>
  );
}
