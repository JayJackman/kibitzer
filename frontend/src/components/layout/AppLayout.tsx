/**
 * Shared layout for all authenticated pages.
 *
 * Renders a top navigation bar with the app name, the current user's
 * username, and a logout button. Below the nav bar, React Router's
 * <Outlet /> renders whichever child route is active (e.g., Lobby).
 *
 * Gets the user data from the protected route's loader (defined in
 * App.tsx). The loader already verified the user is authenticated
 * before this component renders, so `user` is guaranteed to exist.
 *
 * Logout uses a fetcher form -- a small form that submits to the
 * /logout action without navigating away from the current page.
 * The action clears cookies and returns a redirect to /login.
 */
import { Outlet, useFetcher, useRouteLoaderData } from "react-router";
import type { User } from "@/api/types";
import { Button } from "@/components/ui/button";

export default function AppLayout() {
  // useRouteLoaderData("protected") reads the data returned by the
  // protectedLoader in App.tsx. The "protected" string matches the
  // route's `id` field. The loader returns { user: User }.
  const { user } = useRouteLoaderData("protected") as { user: User };

  // useFetcher() creates a "fetcher" -- a way to submit forms or
  // call actions without a full page navigation. We use it here so
  // the logout button can POST to /logout without navigating first.
  const fetcher = useFetcher();

  return (
    <div className="min-h-screen bg-background">
      {/* --- Top navigation bar --- */}
      <nav className="border-b bg-card">
        <div className="container mx-auto flex items-center justify-between px-4 py-3">
          {/* App name / logo area */}
          <h1 className="text-2xl font-bold">Kibitzer</h1>

          {/* Right side: username + logout */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user.username}
            </span>
            {/*
              fetcher.Form submits a POST to /logout, which triggers
              the logoutAction in App.tsx. The action clears cookies
              and returns redirect("/login").
            */}
            <fetcher.Form method="post" action="/logout">
              <Button variant="outline" size="sm" type="submit">
                Log out
              </Button>
            </fetcher.Form>
          </div>
        </div>
      </nav>

      {/* --- Page content --- */}
      {/* Outlet renders the matched child route (e.g., LobbyPage). */}
      <Outlet />
    </div>
  );
}
