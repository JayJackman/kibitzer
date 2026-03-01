/**
 * Displays the engine's rule evaluation trace -- how it reached its bid.
 *
 * Each step is a rule that was evaluated, with a list of conditions that
 * either passed or failed. The winning rule (the one that produced the
 * recommended bid) is shown prominently; other rules are muted.
 *
 * Conditions are shown as a checklist with green checkmarks for passing
 * conditions and red X marks for failures, so the user can see exactly
 * which criteria were met and which weren't.
 */
import type { ThoughtStep } from "@/api/types";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

interface ThoughtProcessProps {
  /** The list of rule evaluation steps from the engine. */
  steps: ThoughtStep[];
}

export default function ThoughtProcess({ steps }: ThoughtProcessProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <h4 className="text-muted-foreground text-xs font-medium uppercase tracking-wide">
        Thought Process
      </h4>

      {steps.map((step, index) => (
        <div key={index}>
          {/* Separator between steps (not before the first one). */}
          {index > 0 && <Separator className="mb-2" />}

          <div
            className={cn(
              "flex flex-col gap-1",
              // The winning rule is fully opaque; other rules are dimmed.
              !step.passed && "opacity-50",
            )}
          >
            {/* Rule name + pass/fail indicator */}
            <div className="flex items-center gap-2 text-sm">
              <span>{step.passed ? "\u2705" : "\u274C"}</span>
              <span className="font-medium">{step.rule_name}</span>
              {/* Show the bid this rule would have produced (if any). */}
              {step.bid && (
                <span className="text-muted-foreground">
                  &rarr; {step.bid}
                </span>
              )}
            </div>

            {/* Condition checklist for this rule. */}
            <ul className="ml-6 flex flex-col gap-0.5">
              {step.conditions.map((cond, condIndex) => (
                <li key={condIndex} className="flex items-start gap-1.5 text-xs">
                  {/* Small colored dot: green for pass, red for fail. */}
                  <span
                    className={cn(
                      "mt-0.5 inline-block h-2 w-2 shrink-0 rounded-full",
                      cond.passed ? "bg-green-500" : "bg-red-500",
                    )}
                  />
                  <span>
                    {/* Condition label in medium weight, detail in muted. */}
                    <span className="font-medium">{cond.label}</span>
                    {cond.detail && (
                      <span className="text-muted-foreground">
                        {" "}
                        ({cond.detail})
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
}
