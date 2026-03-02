/**
 * Lobby page -- the home screen after login.
 *
 * Shows a welcome message and four activity cards:
 *   1. Solo Practice -- bid against the engine alone
 *   2. Multiplayer Practice -- create a session and invite friends
 *   3. Helper Mode -- companion for physical bridge (enter real hands, get advice)
 *   4. Join Session -- enter a 6-character code to join an existing session
 *
 * Solo, Multiplayer, and Helper all post to /practice/new, which creates
 * the session and redirects to /practice/:id. The Join form posts to the
 * lobby route's own action (joinByCodeAction in App.tsx), which looks up
 * the code and redirects to the session's practice page.
 */
import { useState } from "react";
import { Form, useActionData, useNavigation, useRouteLoaderData } from "react-router";
import type { Seat, User } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/** The four seats the player can choose from. */
const SEATS: Seat[] = ["N", "E", "S", "W"];

/** Vulnerability options for the helper mode card. */
const VULN_OPTIONS = [
  { value: "None", label: "None" },
  { value: "NS", label: "N-S" },
  { value: "EW", label: "E-W" },
  { value: "Both", label: "Both" },
] as const;

export default function LobbyPage() {
  const { user } = useRouteLoaderData("protected") as { user: User };

  /**
   * useActionData reads the return value of the lobby route's action
   * (joinByCodeAction). If the code lookup fails, it returns { error }.
   */
  const actionData = useActionData() as { error?: string } | undefined;
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  /**
   * Each card has its own selection state because the user might
   * browse between cards before deciding.
   */
  const [soloSeat, setSoloSeat] = useState<Seat>("S");
  const [multiSeat, setMultiSeat] = useState<Seat>("S");
  const [helperSeat, setHelperSeat] = useState<Seat>("S");
  const [helperDealer, setHelperDealer] = useState<Seat>("N");
  const [helperVuln, setHelperVuln] = useState("None");

  return (
    <div className="container mx-auto flex flex-col gap-6 px-4 py-8">
      {/* Welcome card */}
      <Card>
        <CardHeader>
          <CardTitle>Welcome, {user.username}!</CardTitle>
          <CardDescription>
            Choose an activity below to get started.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* --- Solo Practice --- */}
      <Card>
        <CardHeader>
          <CardTitle>Solo Practice</CardTitle>
          <CardDescription>
            Practice bidding against the engine. Pick your seat and start a
            new hand.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form method="post" action="/practice/new" className="flex flex-col gap-4">
            <input type="hidden" name="seat" value={soloSeat} />
            <SeatPicker selected={soloSeat} onSelect={setSoloSeat} />
            <Button type="submit" className="w-fit" disabled={isSubmitting}>
              Start Practice
            </Button>
          </Form>
        </CardContent>
      </Card>

      {/* --- Multiplayer Practice --- */}
      <Card>
        <CardHeader>
          <CardTitle>Multiplayer Practice</CardTitle>
          <CardDescription>
            Create a session and share the join code with friends.
            Other players take human seats; the rest are played by the engine.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/*
           * Posts to the same /practice/new action as solo. The only
           * difference is the explicit mode field (both default to "practice",
           * but being explicit keeps intent clear for future modes).
           */}
          <Form method="post" action="/practice/new" className="flex flex-col gap-4">
            <input type="hidden" name="seat" value={multiSeat} />
            <input type="hidden" name="mode" value="practice" />
            <SeatPicker selected={multiSeat} onSelect={setMultiSeat} />
            <Button type="submit" className="w-fit" disabled={isSubmitting}>
              Create Session
            </Button>
          </Form>
        </CardContent>
      </Card>

      {/* --- Helper Mode --- */}
      <Card>
        <CardHeader>
          <CardTitle>Helper Mode</CardTitle>
          <CardDescription>
            Companion for physical bridge. Enter your real hands, record bids
            as they happen, and get engine advice when you need it.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/*
           * Posts to /practice/new with mode="helper" plus dealer and
           * vulnerability from the pickers below. The createPracticeAction
           * in App.tsx reads these extra fields and passes them to the API.
           */}
          <Form method="post" action="/practice/new" className="flex flex-col gap-4">
            <input type="hidden" name="mode" value="helper" />
            <input type="hidden" name="seat" value={helperSeat} />
            <input type="hidden" name="dealer" value={helperDealer} />
            <input type="hidden" name="vulnerability" value={helperVuln} />

            {/* Your seat */}
            <div>
              <p className="mb-1.5 text-sm font-medium">Your Seat</p>
              <SeatPicker selected={helperSeat} onSelect={setHelperSeat} />
            </div>

            {/* Dealer at the physical table */}
            <div>
              <p className="mb-1.5 text-sm font-medium">Dealer</p>
              <SeatPicker selected={helperDealer} onSelect={setHelperDealer} />
            </div>

            {/* Vulnerability at the physical table */}
            <div>
              <p className="mb-1.5 text-sm font-medium">Vulnerability</p>
              <VulnPicker selected={helperVuln} onSelect={setHelperVuln} />
            </div>

            <Button type="submit" className="w-fit" disabled={isSubmitting}>
              Create Session
            </Button>
          </Form>
        </CardContent>
      </Card>

      {/* --- Join Session --- */}
      <Card>
        <CardHeader>
          <CardTitle>Join Session</CardTitle>
          <CardDescription>
            Enter a 6-character code to join a friend's session.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/*
           * This form posts to the lobby route itself (no action= needed).
           * The joinByCodeAction in App.tsx handles the submission: looks up
           * the code via the API and redirects to /practice/{id}, where the
           * practiceLoader detects 403 and shows the seat picker.
           */}
          <Form method="post" className="flex flex-col gap-4">
            <div className="flex gap-2">
              <Input
                name="code"
                placeholder="ABC123"
                maxLength={6}
                className="w-32 font-mono uppercase"
                required
              />
              <Button type="submit" disabled={isSubmitting}>
                Join
              </Button>
            </div>
            {/* Error message from the action (e.g., invalid code) */}
            {actionData?.error && (
              <p className="text-sm text-destructive">{actionData.error}</p>
            )}
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared picker components
// ---------------------------------------------------------------------------

/**
 * Row of toggle buttons for picking a seat (N/E/S/W).
 * The selected seat is highlighted with the primary variant;
 * unselected seats use the outline variant with muted text.
 * Reused for both "your seat" and "dealer" selection.
 */
function SeatPicker({
  selected,
  onSelect,
}: {
  selected: Seat;
  onSelect: (seat: Seat) => void;
}) {
  return (
    <div className="flex gap-2">
      {SEATS.map((seat) => (
        <Button
          key={seat}
          type="button"
          variant={selected === seat ? "default" : "outline"}
          className={cn(
            "min-w-16",
            selected !== seat && "text-muted-foreground",
          )}
          onClick={() => onSelect(seat)}
        >
          {SEAT_LABELS[seat]}
        </Button>
      ))}
    </div>
  );
}

/**
 * Row of toggle buttons for picking vulnerability (None/NS/EW/Both).
 * Same visual style as SeatPicker.
 */
function VulnPicker({
  selected,
  onSelect,
}: {
  selected: string;
  onSelect: (vuln: string) => void;
}) {
  return (
    <div className="flex gap-2">
      {VULN_OPTIONS.map(({ value, label }) => (
        <Button
          key={value}
          type="button"
          variant={selected === value ? "default" : "outline"}
          className={cn(
            "min-w-16",
            selected !== value && "text-muted-foreground",
          )}
          onClick={() => onSelect(value)}
        >
          {label}
        </Button>
      ))}
    </div>
  );
}
