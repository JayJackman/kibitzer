/**
 * Scoring sheet slide-out panel for rubber bridge scoring.
 *
 * Opens from the right side of the screen when the user clicks the
 * "Scoring" button in the practice page header (helper mode only).
 *
 * The sheet contains:
 *   - Column headers with player names (NS vs EW)
 *   - The visual scoresheet (above/below the line, game dividers)
 *   - Entry forms for recording deal results (auto or manual)
 *   - Rubber summary when complete (with "New Rubber" button)
 *
 * Scoring state lives on the backend session and arrives via the
 * PracticeState.scoring field (updated every 2s by polling). Mutations
 * (add/update/delete entries, new rubber) use direct API calls that
 * return the updated RubberState, so the sheet can optimistically
 * update without waiting for the next poll cycle.
 */
import { useCallback, useState } from "react";
import { Calculator } from "lucide-react";

import type { PracticeState, RubberState, Seat } from "@/api/types";
import {
  submitScoringEntry,
  deleteScoringEntry,
  startNewRubber,
} from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import Scoresheet from "./Scoresheet";
import ScoreEntry from "./ScoreEntry";
import RubberSummary from "./RubberSummary";

interface ScoringSheetProps {
  state: PracticeState;
}

export default function ScoringSheet({ state }: ScoringSheetProps) {
  // Local copy of scoring state for optimistic updates. Falls back to
  // the server state from polling when null (i.e., after the next poll
  // overwrites it, the local copy is stale but harmless).
  const [localScoring, setLocalScoring] = useState<RubberState | null>(null);
  const scoring = localScoring ?? state.scoring;

  // ---- Mutation handlers ----

  /** Submit a new manual entry or update an existing one. */
  const handleSubmitEntry = useCallback(
    async (entry: {
      entry_id?: number;
      position?: number;
      level: number;
      suit: string;
      declarer: Seat;
      doubled: boolean;
      redoubled: boolean;
      tricks_taken?: number | null;
    }) => {
      const updated = await submitScoringEntry(state.id, entry);
      setLocalScoring(updated);
    },
    [state.id],
  );

  /** Delete an entry by id. */
  const handleDeleteEntry = useCallback(
    async (entryId: number) => {
      const updated = await deleteScoringEntry(state.id, entryId);
      setLocalScoring(updated);
    },
    [state.id],
  );

  /** Start a new rubber after the current one completes. */
  const handleNewRubber = useCallback(async () => {
    const updated = await startNewRubber(state.id);
    setLocalScoring(updated);
  }, [state.id]);

  return (
    <Sheet>
      {/* Trigger button rendered in the practice page header. */}
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-1.5">
          <Calculator className="size-4" />
          <span className="hidden sm:inline">Scoring</span>
        </Button>
      </SheetTrigger>

      {/* Sheet content: slides in from the right, full height. */}
      <SheetContent side="right" className="flex w-full flex-col overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Rubber Bridge Scoring</SheetTitle>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-4 pb-4">
          {scoring ? (
            <>
              {/* The visual scoresheet with above/below the line. */}
              <Scoresheet
                scoring={scoring}
                players={state.players}
                onEditEntry={handleSubmitEntry}
                onDeleteEntry={handleDeleteEntry}
              />

              {/* Rubber complete: show summary + new rubber button. */}
              {scoring.is_complete && (
                <RubberSummary scoring={scoring} onNewRubber={handleNewRubber} />
              )}

              {/* Score entry form for adding new deals. */}
              {!scoring.is_complete && (
                <ScoreEntry
                  scoring={scoring}
                  players={state.players}
                  onSubmit={handleSubmitEntry}
                />
              )}
            </>
          ) : (
            /* Scoring not yet initialized -- show a prompt to start. */
            <div className="flex flex-col items-center gap-4 py-8">
              <p className="text-muted-foreground text-center text-sm">
                Start tracking rubber bridge scores for this session.
              </p>
              <Button
                variant="outline"
                onClick={() =>
                  /* Initialize the rubber tracker by submitting a
                     dummy request -- the backend lazy-inits on first
                     scoring endpoint call. We use new-rubber which
                     creates an empty tracker. */
                  handleNewRubber()
                }
              >
                Start Scoring
              </Button>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
