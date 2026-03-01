/**
 * Typed API endpoint functions.
 *
 * Each function wraps a single API call and returns typed data.
 * Components call these instead of using axios directly, which keeps
 * URL strings and request/response shapes in one place.
 *
 * Types are defined in ./types.ts (mirroring backend Pydantic schemas).
 */
import api from "./client";
import type {
  Advice,
  AuthCredentials,
  BidFeedback,
  PracticeState,
  User,
} from "./types";

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

// --- Practice endpoints ---

/**
 * Create a new practice session.
 * Returns the session ID; redirect to /practice/{id} to fetch full state.
 */
export async function createPracticeSession(
  seat: string,
): Promise<{ id: string }> {
  const response = await api.post<{ id: string }>("/practice", { seat });
  return response.data;
}

/**
 * Get the current state of a practice session (hand, auction, legal bids, etc.).
 */
export async function getPracticeState(
  sessionId: string,
): Promise<PracticeState> {
  const response = await api.get<PracticeState>(`/practice/${sessionId}`);
  return response.data;
}

/**
 * Place a bid in the practice session.
 * Returns feedback on whether the bid matched the engine's recommendation.
 * After this call, computer seats bid automatically -- refetch state to see updates.
 */
export async function placeBid(
  sessionId: string,
  bid: string,
): Promise<BidFeedback> {
  const response = await api.post<BidFeedback>(
    `/practice/${sessionId}/bid`,
    { bid },
  );
  return response.data;
}

/**
 * Get the engine's bid recommendation for the current position.
 * Includes the full thought process (which rules were evaluated and why).
 */
export async function getAdvice(sessionId: string): Promise<Advice> {
  const response = await api.get<Advice>(`/practice/${sessionId}/advise`);
  return response.data;
}

/**
 * Deal new hands, rotate dealer, pick random vulnerability.
 * Refetch state after this call to get the new deal.
 */
export async function redeal(
  sessionId: string,
): Promise<{ ok: boolean }> {
  const response = await api.post<{ ok: boolean }>(
    `/practice/${sessionId}/redeal`,
  );
  return response.data;
}
