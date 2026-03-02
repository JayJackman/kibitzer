/**
 * Compact session controls: join code text, copy button, and leave button.
 *
 * Two visual variants:
 *   - "background": for use when placed directly on the page background
 *   - "card": for use when placed inside a Card or other elevated surface
 */
import { useState } from "react";
import { Form } from "react-router";

import type { PracticeState } from "@/api/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Check, Copy } from "lucide-react";

const variantStyles = {
  background: { /** For rendering on the background */
    container: "rounded-md border bg-background py-1.5",
    text: "text-foreground",
    copyButton: "",
    leaveButtonVariant: "ghost",
  },
  card: { /** For rendering on a card */
    container: "",
    text: "",
    copyButton: "",
    leaveButtonVariant: "action",
  },
} as const;

interface SessionControlsProps {
  state: PracticeState;
  isSubmitting: boolean;
  variant?: "background" | "card";
}

export default function SessionControls({
  state,
  isSubmitting,
  variant = "background",
}: SessionControlsProps) {
  const [copied, setCopied] = useState(false);

  /** Copy the join code to the clipboard and show a brief check mark. */
  function handleCopy() {
    navigator.clipboard.writeText(state.join_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const styles = variantStyles[variant];

  return (
    <div className={cn("flex items-center gap-1 px-1", styles.container)}>
      <span className={cn("whitespace-nowrap font-mono font-semibold tracking-wider px-1", styles.text)}>
        {state.join_code}
      </span>
      <Button variant="ghost" size="icon-xs" onClick={handleCopy} className={styles.copyButton}>
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      </Button>
      <Form method="post">
        <input type="hidden" name="intent" value="leave" />
        <Button type="submit" variant={styles.leaveButtonVariant} size="xs" disabled={isSubmitting}>
          Leave
        </Button>
      </Form>
    </div>
  );
}
