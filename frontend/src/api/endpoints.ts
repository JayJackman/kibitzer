/**
 * Typed API endpoint functions.
 *
 * Each function wraps a single API call and returns typed data.
 * Components call these instead of using axios directly, which keeps
 * URL strings and request/response shapes in one place.
 *
 * The types here mirror the Pydantic schemas on the backend
 * (see src/bridge/api/auth/schemas.py).
 */
import api from "./client";

// --- Types ---

/** User info returned by the API after login/register/me. */
export interface User {
  id: number;
  username: string;
}

/** Shape of the register and login request bodies. */
export interface AuthCredentials {
  username: string;
  password: string;
}

// --- Auth endpoints ---

/**
 * Register a new user account.
 * On success, the backend sets auth cookies automatically.
 */
export async function register(credentials: AuthCredentials): Promise<User> {
  const response = await api.post<User>("/auth/register", credentials);
  return response.data;
}

/**
 * Log in with existing credentials.
 * On success, the backend sets auth cookies automatically.
 */
export async function login(credentials: AuthCredentials): Promise<User> {
  const response = await api.post<User>("/auth/login", credentials);
  return response.data;
}

/**
 * Log out. Tells the backend to clear the auth cookies.
 */
export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

/**
 * Check who is currently logged in by reading the session cookie.
 * Returns the user if authenticated, or throws 401 if not.
 * The 401 is handled by the axios interceptor (which tries to refresh).
 */
export async function getMe(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}
