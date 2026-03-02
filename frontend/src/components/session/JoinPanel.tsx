/**
 * Shown when the user isn't seated at the session (loader returned 403).
 * Displays the session info and a seat picker so the user can join.
 *
 * Each available seat is a form button that submits intent=join with
 * the chosen seat. The practiceAction calls joinSession(), then
 * redirects to trigger a fresh loader run (now returning full state).
 */
import { Form, useNavigation } from "react-router";

import type { SessionInfo } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { ALL_SEATS } from "@/lib/bridge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function JoinPanel({ info }: { info: SessionInfo }) {
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  return (
    <div className="container mx-auto flex flex-col items-center gap-6 px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Join Session</CardTitle>
          <p className="text-card-muted-foreground text-sm">
            Code: <span className="font-mono font-semibold">{info.join_code}</span>
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Show who's already seated */}
          <div className="text-sm">
            {ALL_SEATS.map((seat) => (
              <div key={seat} className="flex items-center gap-2 py-0.5">
                <span className="w-14 font-medium">{SEAT_LABELS[seat]}</span>
                <span className="text-card-muted-foreground">
                  {info.players[seat] ?? "Computer"}
                </span>
              </div>
            ))}
          </div>

          {/* Seat picker: one button per available seat */}
          <p className="text-sm font-medium">Pick a seat:</p>
          <div className="flex gap-2">
            {info.available_seats.map((seat) => (
              <Form method="post" key={seat}>
                <input type="hidden" name="intent" value="join" />
                <input type="hidden" name="seat" value={seat} />
                <Button type="submit" variant="outline" disabled={isSubmitting}>
                  {SEAT_LABELS[seat]}
                </Button>
              </Form>
            ))}
          </div>

          {info.available_seats.length === 0 && (
            <p className="text-card-muted-foreground text-sm">
              No seats available -- the session is full.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
