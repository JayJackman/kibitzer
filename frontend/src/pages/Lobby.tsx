/**
 * Lobby page -- the home screen after login.
 *
 * Shows a welcome card (with join-by-code) and two activity cards:
 *   1. Practice -- create a session, bid against the engine, share the
 *      join code with friends if you want multiplayer
 *   2. Helper Mode -- companion for physical bridge (enter real hands, get advice)
 *
 * Practice and Helper both post to /practice/new, which creates the session
 * and redirects to /practice/:id. The join-by-code form in the welcome card
 * posts to the lobby route's own action (joinByCodeAction in App.tsx), which
 * looks up the code and redirects to the session's practice page.
 */
import { useState } from "react";
import { Form, useActionData, useNavigation, useRouteLoaderData } from "react-router";
import type { Seat, User } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import SeatPicker from "@/components/ui/SeatPicker";
import VulnPicker from "@/components/ui/VulnPicker";

export default function LobbyPage() {
  const { user } = useRouteLoaderData("protected") as { user: User };

  /**
   * useActionData reads the return value of the lobby route's action
   * (joinByCodeAction). If the code lookup fails, it returns { error }.
   */
  const actionData = useActionData() as { error?: string } | undefined;
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  const [practiceSeat, setPracticeSeat] = useState<Seat>("S");
  const [helperSeat, setHelperSeat] = useState<Seat>("S");
  const [helperDealer, setHelperDealer] = useState<Seat>("N");
  const [helperVuln, setHelperVuln] = useState("None");

  return (
    <div className="container mx-auto flex flex-col gap-6 px-4 py-8">
      {/* Welcome card with join-by-code on the right */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle>Welcome, {user.username}!</CardTitle>
              <CardDescription>
                Choose an activity below to get started.
              </CardDescription>
            </div>
            {/*
             * Join-by-code form. Posts to the lobby route itself (no action=
             * needed). The joinByCodeAction in App.tsx looks up the code and
             * redirects to /practice/{id}, where the practiceLoader detects
             * 403 and shows the seat picker.
             */}
            <Form method="post" className="flex items-center gap-2">
              <Input
                name="code"
                placeholder="Join code"
                maxLength={6}
                className="w-32 font-mono uppercase"
                required
              />
              <Button type="submit" variant="outline" disabled={isSubmitting}>
                Join
              </Button>
            </Form>
          </div>
          {/* Error message from the action (e.g., invalid code) */}
          {actionData?.error && (
            <p className="mt-2 text-sm text-destructive">{actionData.error}</p>
          )}
        </CardHeader>
      </Card>

      {/* Practice and Helper Mode side by side */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* --- Practice --- */}
        <Card>
          <CardHeader>
            <CardTitle>Practice</CardTitle>
            <CardDescription>
              Practice bidding against the engine. Share the join code with
              friends to practice together.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form method="post" action="/practice/new" className="flex flex-col gap-4">
              <input type="hidden" name="seat" value={practiceSeat} />
              <SeatPicker selected={practiceSeat} onSelect={setPracticeSeat} />
              <Button type="submit" variant="action" className="w-fit" disabled={isSubmitting}>
                Start Practice
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

              <Button type="submit" variant="action" className="w-fit" disabled={isSubmitting}>
                Create Session
              </Button>
            </Form>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
