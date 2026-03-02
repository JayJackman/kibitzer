/**
 * Session header bar shown during multiplayer and helper mode sessions.
 * Displays the join code (with a copy button), player names at each
 * seat, and a leave button.
 */
import { useState } from "react";
import { Form } from "react-router";

import type { PracticeState } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { ALL_SEATS } from "@/lib/bridge";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Check, Copy } from "lucide-react";

interface SessionHeaderProps {
  state: PracticeState;
  isSubmitting: boolean;
}

export default function SessionHeader({ state, isSubmitting }: SessionHeaderProps) {
  const [copied, setCopied] = useState(false);

  /** Copy the join code to the clipboard and show a brief "Copied!" label. */
  function handleCopy() {
    navigator.clipboard.writeText(state.join_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border bg-card text-card-foreground px-4 py-2 text-sm">
      {/* Join code with copy button */}
      <div className="flex items-center gap-1.5">
        <span className="text-card-muted-foreground">Code:</span>
        <span className="font-mono font-semibold">{state.join_code}</span>
        <Button variant="outline" size="xs" onClick={handleCopy} className="px-1.5">
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        </Button>
      </div>

      {/* Player names at each seat */}
      <div className="flex items-center gap-3">
        {ALL_SEATS.map((seat) => {
          const name = state.players[seat];
          const isYou = seat === state.your_seat;
          return (
            <span key={seat} className={cn(isYou && "font-semibold")}>
              {SEAT_LABELS[seat]}:{" "}
              <span className={cn(name === null && "text-card-muted-foreground")}>
                {isYou ? "You" : name ?? "CPU"}
              </span>
            </span>
          );
        })}
      </div>

      {/* Leave button */}
      <Form method="post" className="ml-auto">
        <input type="hidden" name="intent" value="leave" />
        <Button
          type="submit"
          variant="outline"
          size="xs"
          disabled={isSubmitting}
        >
          Leave
        </Button>
      </Form>
    </div>
  );
}
