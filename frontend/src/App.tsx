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
 *   - /: LobbyPage (child of the protected layout)
 * - *: catch-all redirects to /
 */
import { createBrowserRouter, redirect, Navigate } from "react-router";
import type { ActionFunctionArgs } from "react-router";
import { AxiosError } from "axios";
import * as authApi from "@/api/endpoints";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/Login";
import RegisterPage from "@/pages/Register";
import LobbyPage from "@/pages/Lobby";

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
    const user = await authApi.getMe();
    return { user };
  } catch {
    // Not authenticated -- throw redirect to bail out immediately.
    // throw (not return) signals "stop everything, you can't be here."
    throw redirect("/login");
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
    await authApi.login({
      username: formData.get("username") as string,
      password: formData.get("password") as string,
    });
    // Redirect to the lobby. React Router will run protectedLoader,
    // which calls getMe() and finds the user is now authenticated.
    return redirect("/");
  } catch (err) {
    if (err instanceof AxiosError && err.response?.data?.detail) {
      return { error: err.response.data.detail as string };
    }
    return { error: "Something went wrong. Please try again." };
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
    await authApi.register({
      username: formData.get("username") as string,
      password,
    });
    return redirect("/");
  } catch (err) {
    if (err instanceof AxiosError && err.response?.data?.detail) {
      return { error: err.response.data.detail as string };
    }
    return { error: "Something went wrong. Please try again." };
  }
}

// ---------------------------------------------------------------------------
// Action: handles logout. Called when the nav bar's logout form submits.
// Clears cookies on the backend, then redirects to /login.
// ---------------------------------------------------------------------------
async function logoutAction() {
  await authApi.logout();
  return redirect("/login");
}

/**
 * The router definition. Passed to <RouterProvider> in main.tsx.
 */
export const router = createBrowserRouter([
  // --- Public routes (no auth required) ---
  // Each has an action to handle its form submission.
  { path: "/login", element: <LoginPage />, action: loginAction },
  { path: "/register", element: <RegisterPage />, action: registerAction },

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
    children: [
      { path: "/", element: <LobbyPage /> },
    ],
  },

  // Catch-all: redirect unknown paths to the lobby
  { path: "*", element: <Navigate to="/" replace /> },
]);
