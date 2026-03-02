/**
 * Form for entering a hand by suit (helper mode).
 *
 * Four labeled inputs (one per suit) with suit symbols and colors.
 * Tab moves between them. On submit, the four values are joined
 * into PBN format (Spades.Hearts.Diamonds.Clubs) for the API.
 * Each input accepts rank characters like "AKJ52" (case-insensitive).
 */
import { useState } from "react";
import { Form, useNavigation } from "react-router";

import type { Seat } from "@/api/types";
import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/** Suit field config for the four input rows. */
const SUIT_FIELDS = [
  { key: "S", symbol: SUIT_SYMBOLS.S, color: SUIT_COLORS.S, placeholder: "--" },
  { key: "H", symbol: SUIT_SYMBOLS.H, color: SUIT_COLORS.H, placeholder: "--" },
  { key: "D", symbol: SUIT_SYMBOLS.D, color: SUIT_COLORS.D, placeholder: "--" },
  { key: "C", symbol: SUIT_SYMBOLS.C, color: SUIT_COLORS.C, placeholder: "--" },
] as const;

/** Valid rank characters (case-insensitive). */
const VALID_RANKS = new Set("AKQJT98765432");

/** Rank sort order: A highest (0), 2 lowest (12). */
const RANK_ORDER: Record<string, number> = Object.fromEntries(
  "AKQJT98765432".split("").map((r, i) => [r, i]),
);

/**
 * Parse rank characters from a suit input string.
 * Normalises "10" to "T" and uppercases everything.
 * Returns the list of rank chars (e.g. ["A", "K", "J", "5", "2"]).
 */
function parseRanks(raw: string): string[] {
  const s = raw.toUpperCase().replace(/10/g, "T");
  return [...s].filter((char) => VALID_RANKS.has(char));
}

/**
 * Filter raw rank input: uppercase, strip invalid or duplicate characters,
 * clamp to `maxCards` so the total hand never exceeds 13, and sort
 * high-to-low (A K Q J T 9 ... 2).
 */
function filterRankInput(raw: string, maxCards: number): string {
  const seen = new Set<string>();
  return raw
    .toUpperCase()
    .split("")
    .filter((char) => {
      if (!VALID_RANKS.has(char) || seen.has(char)) return false;
      seen.add(char);
      return true;
    })
    .slice(0, maxCards)
    .sort((a, b) => RANK_ORDER[a] - RANK_ORDER[b])
    .join("");
}

/**
 * Validate the four suit inputs. Returns an error message string
 * or null if the hand is valid (exactly 13 unique cards).
 */
function validateHand(suits: Record<string, string>): string | null {
  const allCards: string[] = [];
  for (const [suitKey, raw] of Object.entries(suits)) {
    for (const rank of parseRanks(raw)) {
      allCards.push(`${rank}${suitKey}`);
    }
  }
  if (allCards.length === 0) return "Enter your cards";
  if (allCards.length !== 13) return `${allCards.length} cards entered (need 13)`;

  // Check for duplicates within the hand.
  const seen = new Set<string>();
  for (const card of allCards) {
    if (seen.has(card)) return `Duplicate card: ${card}`;
    seen.add(card);
  }
  return null;
}

export default function HandEntryForm({ sessionSeat }: { sessionSeat: Seat }) {
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  // Controlled state for each suit so we can assemble PBN on submit.
  const [suits, setSuits] = useState({ S: "", H: "", D: "", C: "" });
  const [error, setError] = useState<string | null>(null);

  // Assemble PBN: "AKJ52.KQ3.84.A73" (empty suits become "" which is valid).
  // Normalise "10" to "T" for the backend PBN parser.
  const pbn = SUIT_FIELDS.map(({ key }) =>
    parseRanks(suits[key]).join(""),
  ).join(".");

  // Total card count for the live counter.
  const cardCount = SUIT_FIELDS.reduce(
    (n, { key }) => n + parseRanks(suits[key]).length,
    0,
  );

  /** Validate before allowing the form to submit. */
  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    const err = validateHand(suits);
    if (err) {
      e.preventDefault();
      setError(err);
    }
  }

  return (
    <Card>
      <CardHeader className="px-3">
        <CardTitle>Enter Your Hand</CardTitle>
      </CardHeader>
      <CardContent className="px-3">
        <Form method="post" className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <input type="hidden" name="intent" value="set_hand" />
          <input type="hidden" name="seat" value={sessionSeat} />
          <input type="hidden" name="hand_pbn" value={pbn} />

          {/* One input per suit, each prefixed with the colored suit symbol. */}
          <div className="flex flex-col gap-2">
            {SUIT_FIELDS.map(({ key, symbol, color, placeholder }, i) => (
              <div key={key} className="flex items-center gap-2">
                <span className={cn("text-lg font-bold w-5 text-center", color)}>
                  {symbol}
                </span>
                <Input
                  value={suits[key]}
                  onChange={(e) => {
                    // How many cards the other three suits already use.
                    const otherCount = SUIT_FIELDS.reduce(
                      (n, f) => n + (f.key === key ? 0 : parseRanks(suits[f.key]).length),
                      0,
                    );
                    const value = filterRankInput(e.target.value, 13 - otherCount);
                    setSuits((prev) => ({ ...prev, [key]: value }));
                    setError(null);
                  }}
                  placeholder={placeholder}
                  className="font-mono flex-1"
                  autoFocus={i === 0}
                />
              </div>
            ))}
          </div>

          {/* Live card count + validation error */}
          <div className="flex items-center gap-3">
            <span className={cn(
              "text-xs",
              cardCount === 13 ? "text-green-600" : "text-card-muted-foreground",
            )}>
              {cardCount}/13 cards
            </span>
            {error && <span className="text-xs text-destructive">{error}</span>}
          </div>

          <Button type="submit" size="sm" className="w-fit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Submit Hand"}
          </Button>
        </Form>
      </CardContent>
    </Card>
  );
}
