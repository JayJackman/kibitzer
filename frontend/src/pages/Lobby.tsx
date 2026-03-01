/**
 * Lobby page -- the home screen after login.
 *
 * For now this is a placeholder. In Step 4, it will show a list of
 * tables with their status (waiting/in-progress/completed) and a
 * "Create Table" button.
 *
 * Gets the user data from the protected route's loader via
 * useRouteLoaderData("protected"). The loader guarantees the user
 * is authenticated before this page renders.
 */
import { useRouteLoaderData } from "react-router";
import type { User } from "@/api/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LobbyPage() {
  const { user } = useRouteLoaderData("protected") as { user: User };

  return (
    <div className="container mx-auto py-8 px-4">
      <Card>
        <CardHeader>
          <CardTitle>Welcome, {user.username}!</CardTitle>
          <CardDescription>
            This is the lobby. Tables will appear here soon.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            No tables yet. This page will show available bridge tables once
            multiplayer is implemented.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
