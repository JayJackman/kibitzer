/**
 * Application routing configuration using React Router v7 data patterns.
 *
 * KEY CONCEPTS:
 *
 * Loaders -- functions that run BEFORE a route renders. The protected
 * layout route has a loader that checks if the user is logged in. If
 * not, it redirects to /login before the page ever appears. This
 * replaces the old ProtectedRoute component and AuthProvider entirely.
 *
 * Actions -- functions that handle form submissions. Instead of
 * useState + handleSubmit in each page component, the form logic lives
 * here. React Router's <Form> component submits to these automatically.
 *
 * Route structure:
 * - /login:    public, has an action to handle login form submission
 * - /register: public, has an action to handle registration
 * - /logout:   action-only route (no page), clears cookies and redirects
 * - /: protected layout (checks auth via loader), renders nav + Outlet
 *   - /: LobbyPage (child of the protected layout), with join-by-code action
 *   - /practice/new: action-only route that creates a session and redirects
 *   - /practice/:id: practice page with loader (state) + action (bid/redeal/join/leave)
 *   - /practice/:id/advise: loader-only route for fetcher-based advice loading
 *   - /analyzer: standalone auction analyzer (no loader, local state only)
 *   - /join/:code: loader-only route that looks up a join code and redirects
 * - *: catch-all redirects to /
 */
import {
  createBrowserRouter,
  redirect,
  Navigate,
  useRouteError,
  isRouteErrorResponse,
} from "react-router";
import type { ActionFunctionArgs, LoaderFunctionArgs } from "react-router";
import { AxiosError } from "axios";
import type { Seat, SessionMode } from "@/api/types";

/**
 * Extract a user-facing error message from a caught exception.
 * FastAPI returns errors as { detail: "..." }; fall back to a generic message.
 */
function actionError(err: unknown): { error: string } {
  if (err instanceof AxiosError && err.response?.data?.detail) {
    return { error: err.response.data.detail as string };
  }
  return { error: "Something went wrong. Please try again." };
}
import * as api from "@/api/endpoints";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/Login";
import RegisterPage from "@/pages/Register";
import LobbyPage from "@/pages/Lobby";
import PracticePage from "@/pages/Practice";
import AnalyzerPage from "@/pages/Analyzer";

// ---------------------------------------------------------------------------
// Loader: runs before any protected route renders.
// Calls GET /api/auth/me to check the session cookie. If the user is
// authenticated, returns their data. If not (401), redirects to /login.
//
// This replaces the old ProtectedRoute component. No more "isLoading"
// state or flash of wrong page -- the loader completes before React
// renders anything.
// ---------------------------------------------------------------------------
async function protectedLoader() {
  try {
    const user = await api.getMe();
    return { user };
  } catch (err) {
    // Only redirect to login on auth failures (401). Other errors
    // (network glitches, server 500s) should not log the user out.
    if (err instanceof AxiosError && err.response?.status === 401) {
      throw redirect("/login");
    }
    throw err;
  }
}

// ---------------------------------------------------------------------------
// Action: handles the login form submission.
// React Router calls this when a <Form method="post"> submits on /login.
// On success: cookies are set by the backend, then we redirect to /.
//   React Router then runs protectedLoader, which confirms the session.
// On failure: returns { error: "..." } which the page displays.
// ---------------------------------------------------------------------------
async function loginAction({ request }: ActionFunctionArgs) {
  const formData = await request.formData();

  try {
    await api.login({
      username: formData.get("username") as string,
      password: formData.get("password") as string,
    });
    // Redirect to the lobby. React Router will run protectedLoader,
    // which calls getMe() and finds the user is now authenticated.
    return redirect("/");
  } catch (err) {
    return actionError(err);
  }
}

// ---------------------------------------------------------------------------
// Action: handles the register form submission.
// Same pattern as login, but with password confirmation validation.
// ---------------------------------------------------------------------------
async function registerAction({ request }: ActionFunctionArgs) {
  const formData = await request.formData();
  const password = formData.get("password") as string;
  const confirmPassword = formData.get("confirmPassword") as string;

  // Client-side validation: passwords must match.
  if (password !== confirmPassword) {
    return { error: "Passwords do not match." };
  }

  try {
    await api.register({
      username: formData.get("username") as string,
      password,
    });
    return redirect("/");
  } catch (err) {
    return actionError(err);
  }
}

// ---------------------------------------------------------------------------
// Action: handles logout. Called when the nav bar's logout form submits.
// Clears cookies on the backend, then redirects to /login.
// ---------------------------------------------------------------------------
async function logoutAction() {
  await api.logout();
  return redirect("/login");
}

// ---------------------------------------------------------------------------
// Practice routes: create, view, bid, redeal, and advise.
// ---------------------------------------------------------------------------

/**
 * Action: creates a new practice session and redirects to it.
 * The Lobby page's "Start Practice" form posts here with a seat choice
 * and an optional mode (defaults to "practice").
 *
 * Helper mode also sends dealer and vulnerability from the lobby form.
 */
async function createPracticeAction({ request }: ActionFunctionArgs) {
  const formData = await request.formData();
  const seat = ((formData.get("seat") as string) || "S") as Seat;
  const mode = (formData.get("mode") as string as SessionMode) || undefined;
  // Helper mode sends dealer and vulnerability from the lobby form.
  const dealer = (formData.get("dealer") as string as Seat) || undefined;
  const vulnerability = (formData.get("vulnerability") as string) || undefined;
  const { id } = await api.createPracticeSession(seat, mode, dealer, vulnerability);
  return redirect(`/practice/${id}`);
}

/**
 * Loader: fetches the full session state before PracticePage renders.
 * Runs on initial load and automatically after any action completes
 * (React Router revalidates loaders after mutations).
 *
 * If the user isn't seated at this session (403), catches the error and
 * fetches lightweight session info instead, returning { needsJoin: true }.
 * PracticePage then shows a JoinPanel instead of the full practice UI.
 */
async function practiceLoader({ params }: LoaderFunctionArgs) {
  try {
    return { state: await api.getPracticeState(params.id!) };
  } catch (err) {
    if (err instanceof AxiosError && err.response?.status === 403) {
      const info = await api.getSessionInfo(params.id!);
      return { needsJoin: true as const, info };
    }
    throw err;
  }
}

/**
 * Action: handles form submissions on the practice page.
 * Reads the hidden "intent" field to distinguish between:
 *   - "bid": places a bid, returns feedback (matched engine or not).
 *            In helper mode, may include for_seat for proxy bidding.
 *   - "set_hand": set a seat's hand via PBN (helper mode only)
 *   - "redeal": deals new hands, redirects to trigger a loader revalidation
 *   - "join": join the session at a specific seat, then revalidate
 *   - "leave": leave the session, redirect to the lobby
 */
async function practiceAction({ request, params }: ActionFunctionArgs) {
  const formData = await request.formData();
  const intent = formData.get("intent");

  if (intent === "bid") {
    // for_seat is set when proxy-bidding for an unoccupied seat in helper mode.
    const forSeat = (formData.get("for_seat") as string as Seat) || undefined;
    return await api.placeBid(
      params.id!,
      formData.get("bid") as string,
      forSeat,
    );
  }

  if (intent === "set_hand") {
    await api.setHand(
      params.id!,
      formData.get("seat") as Seat,
      formData.get("hand_pbn") as string,
    );
    // Redirect to trigger a fresh loader run so the hand appears in state.
    return redirect(`/practice/${params.id}`);
  }

  if (intent === "redeal") {
    await api.redeal(params.id!);
    return redirect(`/practice/${params.id}`);
  }

  if (intent === "undo") {
    await api.undoBid(params.id!);
    return redirect(`/practice/${params.id}`);
  }

  if (intent === "reset_auction") {
    await api.resetAuction(params.id!);
    return redirect(`/practice/${params.id}`);
  }

  if (intent === "join") {
    await api.joinSession(params.id!, formData.get("seat") as Seat);
    // Redirect to trigger a fresh loader run -- now the user is seated,
    // so getPracticeState will return 200 instead of 403.
    return redirect(`/practice/${params.id}`);
  }

  if (intent === "leave") {
    await api.leaveSession(params.id!);
    return redirect("/");
  }

  return null;
}

/**
 * Loader: fetches engine advice for the useFetcher() call.
 * This route has no page element -- it's only used by the fetcher
 * in PracticePage when the user clicks "Advise Me".
 */
async function adviceLoader({ params }: LoaderFunctionArgs) {
  return await api.getAdvice(params.id!);
}

/**
 * Action: handles the "Join Session" form on the lobby page.
 * Looks up a session by join code and redirects to the practice page,
 * where the practiceLoader will detect 403 and show the join flow.
 */
async function joinByCodeAction({ request }: ActionFunctionArgs) {
  const formData = await request.formData();
  const code = (formData.get("code") as string).trim();
  try {
    const info = await api.lookupByCode(code);
    return redirect(`/practice/${info.id}`);
  } catch (err) {
    if (err instanceof AxiosError && err.response?.status === 404) {
      return { error: "No session found for that code." };
    }
    return actionError(err);
  }
}

/**
 * Loader: handles shareable /join/:code URLs.
 * Looks up the session by code and redirects to /practice/:id.
 */
async function joinByCodeLoader({ params }: LoaderFunctionArgs) {
  const info = await api.lookupByCode(params.code!);
  return redirect(`/practice/${info.id}`);
}

// ---------------------------------------------------------------------------
// Global error boundary -- catches any unhandled errors from loaders/actions.
// Displays the full error details so nothing gets silently swallowed.
// ---------------------------------------------------------------------------

function RootErrorBoundary() {
  const error = useRouteError();

  let title = "Something went wrong";
  let detail = "An unexpected error occurred.";

  if (isRouteErrorResponse(error)) {
    // HTTP error thrown from a loader/action (e.g. 422, 404, 500).
    title = `${error.status} ${error.statusText}`;
    detail = typeof error.data === "string" ? error.data : JSON.stringify(error.data, null, 2);
  } else if (error instanceof AxiosError && error.response) {
    // Axios wraps the HTTP error — dig out the backend's message.
    const status = error.response.status;
    const data = error.response.data;
    title = `${status} Error`;
    // FastAPI returns errors as { detail: "..." }.
    detail = data?.detail ?? (typeof data === "string" ? data : JSON.stringify(data, null, 2));
  } else if (error instanceof Error) {
    title = error.name;
    detail = error.message;
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="max-w-lg rounded-lg border border-red-200 bg-red-50 p-6 text-left">
        <h1 className="mb-2 text-xl font-bold text-red-800">{title}</h1>
        <pre className="whitespace-pre-wrap text-sm text-red-700">{detail}</pre>
        <a href="/" className="mt-4 inline-block text-sm text-red-600 underline">
          Go home
        </a>
      </div>
    </div>
  );
}

/**
 * The router definition. Passed to <RouterProvider> in main.tsx.
 */
export const router = createBrowserRouter([
  // --- Public routes (no auth required) ---
  // Each has an action to handle its form submission.
  { path: "/login", element: <LoginPage />, action: loginAction, errorElement: <RootErrorBoundary /> },
  { path: "/register", element: <RegisterPage />, action: registerAction, errorElement: <RootErrorBoundary /> },

  // --- Logout (action-only, no page) ---
  // GET /logout redirects to home. POST /logout runs the action.
  { path: "/logout", action: logoutAction, loader: () => redirect("/") },

  // --- Protected routes (auth required) ---
  // The loader checks auth before rendering. If not logged in,
  // the user is redirected to /login before anything renders.
  // The "id" lets child components access loader data via
  // useRouteLoaderData("protected").
  {
    id: "protected",
    loader: protectedLoader,
    element: <AppLayout />,
    errorElement: <RootErrorBoundary />,
    children: [
      // Lobby: home screen with solo/multiplayer cards and join-by-code form.
      // The action handles the join-by-code form submission.
      { path: "/", element: <LobbyPage />, action: joinByCodeAction },

      // Action-only: POST creates a session, redirects to /practice/:id.
      { path: "/practice/new", action: createPracticeAction },

      // Practice page: loader fetches state (or session info for join flow),
      // action handles bid, redeal, join, and leave.
      {
        path: "/practice/:id",
        element: <PracticePage />,
        loader: practiceLoader,
        action: practiceAction,
      },

      // Advice loader: used by useFetcher() in PracticePage (no element).
      { path: "/practice/:id/advise", loader: adviceLoader },

      // Auction Analyzer: standalone page, no loader or action needed
      // (all state is local, API calls happen in the component).
      { path: "/analyzer", element: <AnalyzerPage /> },

      // Shareable join link: looks up the code and redirects to the session.
      { path: "/join/:code", loader: joinByCodeLoader },
    ],
  },

  // Catch-all: redirect unknown paths to the lobby
  { path: "*", element: <Navigate to="/" replace /> },
]);
