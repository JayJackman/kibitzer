/**
 * Form for entering a new deal result into the rubber scoresheet.
 *
 * Two modes:
 *   1. **Pending entry**: The auction completed in the app, so the contract
 *      is pre-filled. The user only needs to enter tricks taken (0-13).
 *   2. **Manual entry**: The user enters the full contract (level, suit,
 *      declarer, doubled/redoubled) plus tricks taken.
 *
 * Submits via the parent's onSubmit callback, which calls the scoring
 * API endpoint.
 */
import { useState } from "react";

import type { RubberState, Seat } from "@/api/types";
import { ALL_SEATS } from "@/lib/bridge";
import { SUIT_SYMBOLS } from "@/lib/constants";
import { Button } from "@/components/ui/button";

interface ScoreEntryProps {
  scoring: RubberState;
  players: Record<Seat, string | null>;
  onSubmit: (entry: {
    entry_id?: number;
    level: number;
    suit: string;
    declarer: Seat;
    doubled: boolean;
    redoubled: boolean;
    tricks_taken?: number | null;
  }) => Promise<void>;
}

const SUITS = [
  { value: "C", label: `${SUIT_SYMBOLS.C} Clubs` },
  { value: "D", label: `${SUIT_SYMBOLS.D} Diamonds` },
  { value: "H", label: `${SUIT_SYMBOLS.H} Hearts` },
  { value: "S", label: `${SUIT_SYMBOLS.S} Spades` },
  { value: "NT", label: "NT" },
];

export default function ScoreEntry({ scoring, players, onSubmit }: ScoreEntryProps) {
  // Check if there's a pending entry from a completed auction.
  const pendingEntry = scoring.entries.find(
    (e) => e.id === scoring.pending_entry_id,
  );

  // Manual entry form state.
  const [level, setLevel] = useState(1);
  const [suit, setSuit] = useState("NT");
  const [declarer, setDeclarer] = useState<Seat>("N");
  const [doubled, setDoubled] = useState(false);
  const [redoubled, setRedoubled] = useState(false);
  const [tricks, setTricks] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Pending entry: just need tricks input.
  const [pendingTricks, setPendingTricks] = useState("");

  /** Submit the pending entry (fill in tricks_taken). */
  async function submitPending() {
    if (!pendingEntry) return;
    const t = parseInt(pendingTricks, 10);
    if (isNaN(t) || t < 0 || t > 13) return;
    setSubmitting(true);
    try {
      await onSubmit({
        entry_id: pendingEntry.id,
        level: pendingEntry.contract_level,
        suit: pendingEntry.contract_suit,
        declarer: pendingEntry.declarer,
        doubled: pendingEntry.doubled,
        redoubled: pendingEntry.redoubled,
        tricks_taken: t,
      });
      setPendingTricks("");
    } finally {
      setSubmitting(false);
    }
  }

  /** Submit a fully manual entry. */
  async function submitManual() {
    const t = tricks === "" ? null : parseInt(tricks, 10);
    if (t !== null && (isNaN(t) || t < 0 || t > 13)) return;
    setSubmitting(true);
    try {
      await onSubmit({
        level,
        suit,
        declarer,
        doubled,
        redoubled,
        tricks_taken: t,
      });
      // Reset form.
      setTricks("");
      setDoubled(false);
      setRedoubled(false);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-4 flex flex-col gap-3">
      {/* Pending entry from completed auction */}
      {pendingEntry && (
        <div className="bg-yellow-50 dark:bg-yellow-950 rounded-md p-3">
          <div className="mb-2 text-sm font-semibold">
            Completed auction: {pendingEntry.contract_level}
            {pendingEntry.contract_suit === "NT"
              ? "NT"
              : (SUIT_SYMBOLS as Record<string, string>)[pendingEntry.contract_suit]}
            {pendingEntry.redoubled ? "XX" : pendingEntry.doubled ? "X" : ""}
            {" by "}
            {pendingEntry.declarer}
            {players[pendingEntry.declarer]
              ? ` (${players[pendingEntry.declarer]})`
              : ""}
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Tricks taken:</label>
            <input
              type="number"
              min={0}
              max={13}
              value={pendingTricks}
              onChange={(e) => setPendingTricks(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submitPending()}
              className="border-input bg-background w-14 rounded border px-2 py-1 text-center text-sm"
            />
            <Button
              size="sm"
              disabled={submitting}
              onClick={submitPending}
            >
              Record
            </Button>
          </div>
        </div>
      )}

      {/* Manual entry form */}
      <div className="border-border rounded-md border p-3">
        <div className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
          Add a Deal Manually
        </div>
        <div className="grid grid-cols-2 gap-2">
          {/* Level */}
          <div>
            <label className="text-xs">Level</label>
            <select
              value={level}
              onChange={(e) => setLevel(Number(e.target.value))}
              className="border-input bg-background w-full rounded border px-2 py-1 text-sm"
            >
              {[1, 2, 3, 4, 5, 6, 7].map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>

          {/* Suit */}
          <div>
            <label className="text-xs">Suit</label>
            <select
              value={suit}
              onChange={(e) => setSuit(e.target.value)}
              className="border-input bg-background w-full rounded border px-2 py-1 text-sm"
            >
              {SUITS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          {/* Declarer */}
          <div>
            <label className="text-xs">Declarer</label>
            <select
              value={declarer}
              onChange={(e) => setDeclarer(e.target.value as Seat)}
              className="border-input bg-background w-full rounded border px-2 py-1 text-sm"
            >
              {ALL_SEATS.map((s) => (
                <option key={s} value={s}>
                  {s}{players[s] ? ` (${players[s]})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Tricks taken */}
          <div>
            <label className="text-xs">Tricks (0-13)</label>
            <input
              type="number"
              min={0}
              max={13}
              value={tricks}
              onChange={(e) => setTricks(e.target.value)}
              placeholder="opt."
              className="border-input bg-background w-full rounded border px-2 py-1 text-sm"
            />
          </div>
        </div>

        {/* Doubled / Redoubled toggles */}
        <div className="mt-2 flex items-center gap-3">
          <label className="flex items-center gap-1 text-sm">
            <input
              type="checkbox"
              checked={doubled}
              onChange={(e) => {
                setDoubled(e.target.checked);
                if (e.target.checked) setRedoubled(false);
              }}
            />
            Doubled
          </label>
          <label className="flex items-center gap-1 text-sm">
            <input
              type="checkbox"
              checked={redoubled}
              onChange={(e) => {
                setRedoubled(e.target.checked);
                if (e.target.checked) setDoubled(false);
              }}
            />
            Redoubled
          </label>
        </div>

        <Button
          className="mt-2 w-full"
          size="sm"
          disabled={submitting}
          onClick={submitManual}
        >
          Add Deal
        </Button>
      </div>
    </div>
  );
}
