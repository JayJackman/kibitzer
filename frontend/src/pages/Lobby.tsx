/**
 * Lobby page -- the home screen after login.
 *
 * Shows a welcome message and a "Solo Practice" section where the user
 * can pick a seat and start a practice bidding session.
 *
 * The practice form posts to /practice/new (an action-only route in
 * App.tsx), which creates the session and redirects to /practice/:id.
 *
 * Gets the user data from the protected route's loader via
 * useRouteLoaderData("protected"). The loader guarantees the user
 * is authenticated before this page renders.
 */
import { useState } from "react";
import { Form, useRouteLoaderData } from "react-router";
import type { Seat, User } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/** The four seats the player can choose from. */
const SEATS: Seat[] = ["N", "E", "S", "W"];

export default function LobbyPage() {
  const { user } = useRouteLoaderData("protected") as { user: User };

  /**
   * Track which seat the user has selected. Defaults to South, the
   * most common seat for solo practice in bridge.
   */
  const [selectedSeat, setSelectedSeat] = useState<Seat>("S");

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

      {/* Solo Practice card with seat picker */}
      <Card>
        <CardHeader>
          <CardTitle>Solo Practice</CardTitle>
          <CardDescription>
            Practice bidding against the engine. Pick your seat and start a
            new hand.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {/*
           * The form posts to /practice/new. The action reads the "seat"
           * value from the hidden input, creates the session, and redirects.
           */}
          <Form method="post" action="/practice/new" className="flex flex-col gap-4">
            {/*
             * Hidden input carries the selected seat value to the action.
             * We use a hidden input (instead of putting the value on the
             * submit button) because the seat is chosen via toggle buttons,
             * not the submit button itself.
             */}
            <input type="hidden" name="seat" value={selectedSeat} />

            {/* Seat picker: 4 toggle buttons in a row */}
            <div className="flex gap-2">
              {SEATS.map((seat) => (
                <Button
                  key={seat}
                  type="button"
                  variant={selectedSeat === seat ? "default" : "outline"}
                  className={cn(
                    "min-w-16",
                    // Muted styling for unselected seats.
                    selectedSeat !== seat && "text-muted-foreground",
                  )}
                  onClick={() => setSelectedSeat(seat)}
                >
                  {SEAT_LABELS[seat]}
                </Button>
              ))}
            </div>

            <Button type="submit" className="w-fit">
              Start Practice
            </Button>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
