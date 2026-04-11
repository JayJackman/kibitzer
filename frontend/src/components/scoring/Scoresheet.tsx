/**
 * Visual rubber bridge scoresheet display.
 *
 * Two-column layout (NS vs EW) with:
 *   - Above-the-line points at the top (overtricks, penalties, slams, insults)
 *   - A thick divider (the "line")
 *   - Below-the-line points (contract points toward game) with game dividers
 *   - Running totals at the bottom
 *
 * Each scored entry row is clickable to expand inline editing (contract
 * and tricks_taken). Pending entries (tricks_taken = null) are highlighted.
 */
import { useState } from "react";

import type { RubberState, ScoringEntry, Seat } from "@/api/types";
import { SUIT_SYMBOLS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ScoresheetProps {
  scoring: RubberState;
  players: Record<Seat, string | null>;
  onEditEntry: (entry: {
    entry_id: number;
    level: number;
    suit: string;
    declarer: Seat;
    doubled: boolean;
    redoubled: boolean;
    tricks_taken?: number | null;
  }) => Promise<void>;
  onDeleteEntry: (entryId: number) => Promise<void>;
}

/** Format a suit letter (C/D/H/S/NT) to its symbol for display. */
function formatSuit(suit: string): string {
  if (suit === "NT") return "NT";
  return (SUIT_SYMBOLS as Record<string, string>)[suit] ?? suit;
}

/** Format a contract for display: "4♠", "3NT", "2♥X", etc. */
function formatContract(e: ScoringEntry): string {
  const suit = formatSuit(e.contract_suit);
  const dbl = e.redoubled ? "XX" : e.doubled ? "X" : "";
  return `${e.contract_level}${suit}${dbl}`;
}

/** Format the result: "=" for exactly, "+N" for overtricks, "-N" for down. */
function formatResult(e: ScoringEntry): string {
  if (e.tricks_taken === null) return "?";
  const needed = 6 + e.contract_level;
  const diff = e.tricks_taken - needed;
  if (diff === 0) return "=";
  return diff > 0 ? `+${diff}` : `${diff}`;
}

/** Build the NS/EW header string, e.g. "N(Alice)/S(Bob)". */
function sideHeader(
  seats: [Seat, Seat],
  players: Record<Seat, string | null>,
): string {
  return seats
    .map((s) => {
      const name = players[s];
      return name ? `${s}(${name})` : s;
    })
    .join("/");
}

export default function Scoresheet({
  scoring,
  players,
  onEditEntry,
  onDeleteEntry,
}: ScoresheetProps) {
  // Which entry is currently being edited (inline).
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTricks, setEditTricks] = useState<string>("");

  const nsHeader = sideHeader(["N", "S"], players);
  const ewHeader = sideHeader(["E", "W"], players);

  /** Handle clicking an entry row to edit tricks_taken. */
  function startEdit(entry: ScoringEntry) {
    setEditingId(entry.id);
    setEditTricks(entry.tricks_taken?.toString() ?? "");
  }

  /** Save the edited tricks value. */
  async function saveEdit(entry: ScoringEntry) {
    const tricks = editTricks === "" ? null : parseInt(editTricks, 10);
    if (tricks !== null && (isNaN(tricks) || tricks < 0 || tricks > 13)) return;
    await onEditEntry({
      entry_id: entry.id,
      level: entry.contract_level,
      suit: entry.contract_suit,
      declarer: entry.declarer,
      doubled: entry.doubled,
      redoubled: entry.redoubled,
      tricks_taken: tricks,
    });
    setEditingId(null);
  }

  // Separate entries into above-the-line and below-the-line items.
  // Each scored entry contributes to one or both sections.
  const rows = scoring.entries;

  return (
    <div className="flex flex-col gap-2">
      {/* Column headers */}
      <div className="grid grid-cols-2 gap-2 text-center text-xs font-bold">
        <div className="truncate" title={nsHeader}>{nsHeader}</div>
        <div className="truncate" title={ewHeader}>{ewHeader}</div>
      </div>

      {/* ---- Above the line ---- */}
      <div className="text-muted-foreground text-center text-[10px] uppercase tracking-wider">
        Above the Line
      </div>
      <div className="grid grid-cols-2 gap-2 text-center text-sm">
        <div>{scoring.ns_above > 0 ? scoring.ns_above : "-"}</div>
        <div>{scoring.ew_above > 0 ? scoring.ew_above : "-"}</div>
      </div>

      {/* ---- The line ---- */}
      <div className="border-foreground border-t-2" />

      {/* ---- Below the line ---- */}
      <div className="text-muted-foreground text-center text-[10px] uppercase tracking-wider">
        Below the Line
      </div>

      {/* Completed games with dividers */}
      {scoring.games.map((game, gi) => (
        <div key={gi}>
          <div className="grid grid-cols-2 gap-2 text-center text-sm">
            <div>{game.ns_below > 0 ? game.ns_below : "-"}</div>
            <div>{game.ew_below > 0 ? game.ew_below : "-"}</div>
          </div>
          {/* Game divider line */}
          <div className="border-muted-foreground my-1 border-t" />
        </div>
      ))}

      {/* Current (incomplete) game */}
      <div className="grid grid-cols-2 gap-2 text-center text-sm font-semibold">
        <div>{scoring.ns_below_current > 0 ? scoring.ns_below_current : "-"}</div>
        <div>{scoring.ew_below_current > 0 ? scoring.ew_below_current : "-"}</div>
      </div>

      {/* ---- Vulnerability indicator ---- */}
      <div className="text-muted-foreground grid grid-cols-2 gap-2 text-center text-xs">
        <div>{scoring.ns_vulnerable ? "Vulnerable" : "Not Vul"}</div>
        <div>{scoring.ew_vulnerable ? "Vulnerable" : "Not Vul"}</div>
      </div>

      {/* ---- Totals ---- */}
      <div className="border-foreground border-t-2" />
      <div className="grid grid-cols-2 gap-2 text-center text-sm font-bold">
        <div>NS: {scoring.ns_total}</div>
        <div>EW: {scoring.ew_total}</div>
      </div>

      {/* Game score */}
      <div className="text-muted-foreground grid grid-cols-2 gap-2 text-center text-xs">
        <div>Games: {scoring.ns_games_won}</div>
        <div>Games: {scoring.ew_games_won}</div>
      </div>

      {/* ---- Deal history ---- */}
      {rows.length > 0 && (
        <>
          <div className="border-muted mt-2 border-t pt-2">
            <div className="text-muted-foreground mb-1 text-xs font-semibold uppercase">
              Deal History
            </div>
          </div>

          {rows.map((se) => {
            const e = se;
            const isPending = e.tricks_taken === null;
            const isEditing = editingId === e.id;

            return (
              <div
                key={e.id}
                className={cn(
                  "flex items-center gap-2 rounded px-2 py-1 text-sm",
                  isPending && "bg-yellow-50 dark:bg-yellow-950",
                  !isPending && !isEditing && "hover:bg-muted cursor-pointer",
                )}
                onClick={() => !isEditing && startEdit(e)}
              >
                {/* Contract + declarer */}
                <span className="min-w-[4rem] font-mono">
                  {formatContract(e)} {e.declarer}
                </span>

                {/* Result or edit input */}
                {isEditing ? (
                  <span className="flex items-center gap-1">
                    <span className="text-muted-foreground text-xs">Tricks:</span>
                    <input
                      type="number"
                      min={0}
                      max={13}
                      value={editTricks}
                      onChange={(ev) => setEditTricks(ev.target.value)}
                      onKeyDown={(ev) => {
                        if (ev.key === "Enter") saveEdit(e);
                        if (ev.key === "Escape") setEditingId(null);
                      }}
                      className="border-input bg-background w-12 rounded border px-1 py-0.5 text-center text-sm"
                      autoFocus
                      onClick={(ev) => ev.stopPropagation()}
                    />
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        saveEdit(e);
                      }}
                    >
                      Save
                    </Button>
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        onDeleteEntry(e.id);
                        setEditingId(null);
                      }}
                      className="text-destructive"
                    >
                      Del
                    </Button>
                  </span>
                ) : (
                  <>
                    <span
                      className={cn(
                        "font-mono",
                        isPending && "text-yellow-600",
                        e.made === true && "text-green-600",
                        e.made === false && "text-red-600",
                      )}
                    >
                      {formatResult(e)}
                    </span>
                    {/* Points summary */}
                    {e.made !== null && (
                      <span className="text-muted-foreground text-xs">
                        {e.made
                          ? `${(e.contract_points ?? 0) + (e.overtrick_points ?? 0) + (e.slam_bonus ?? 0) + (e.insult_bonus ?? 0)} pts`
                          : `${e.undertrick_points ?? 0} pen`}
                      </span>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
