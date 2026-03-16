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
  AllBidsAnalysis,
  AuctionAnalysis,
  AuthCredentials,
  BidAnalysis,
  BidFeedback,
  PracticeState,
  Seat,
  SessionInfo,
  SessionMode,
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
 * Returns the session ID and join code; redirect to /practice/{id} to fetch full state.
 *
 * In helper mode, `dealer` and `vulnerability` specify the physical table's
 * dealer and vulnerability instead of using random/auto-assigned values.
 */
export async function createPracticeSession(
  seat: Seat,
  mode?: SessionMode,
  dealer?: Seat,
  vulnerability?: string,
): Promise<{ id: string; join_code: string }> {
  const body: {
    seat: Seat;
    mode?: SessionMode;
    dealer?: Seat;
    vulnerability?: string;
  } = { seat };
  if (mode) body.mode = mode;
  if (dealer) body.dealer = dealer;
  if (vulnerability) body.vulnerability = vulnerability;
  const response = await api.post<{ id: string; join_code: string }>(
    "/practice",
    body,
  );
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
 *
 * In helper mode, `forSeat` enables proxy bidding: a seated player can bid
 * on behalf of an unoccupied seat.
 */
export async function placeBid(
  sessionId: string,
  bid: string,
  forSeat?: Seat,
): Promise<BidFeedback> {
  const body: { bid: string; for_seat?: Seat } = { bid };
  if (forSeat) body.for_seat = forSeat;
  const response = await api.post<BidFeedback>(
    `/practice/${sessionId}/bid`,
    body,
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

/**
 * Undo the last round of bids.
 * Practice mode: removes the last human bid + computer follow-ups.
 * Helper mode: removes exactly one bid.
 */
export async function undoBid(
  sessionId: string,
): Promise<{ ok: boolean }> {
  const response = await api.post<{ ok: boolean }>(
    `/practice/${sessionId}/undo`,
  );
  return response.data;
}

/**
 * Reset the auction to its initial state (before any human bids).
 * Keeps hands, dealer, and vulnerability intact.
 */
export async function resetAuction(
  sessionId: string,
): Promise<{ ok: boolean }> {
  const response = await api.post<{ ok: boolean }>(
    `/practice/${sessionId}/reset`,
  );
  return response.data;
}

/**
 * Set the hand for a seat (helper mode only).
 * Accepts PBN format: "AKJ52.KQ3.84.A73" (Spades.Hearts.Diamonds.Clubs).
 * Any seated player can set any seat's hand.
 */
export async function setHand(
  sessionId: string,
  seat: Seat,
  handPbn: string,
): Promise<{ ok: boolean }> {
  const response = await api.post<{ ok: boolean }>(
    `/practice/${sessionId}/hand`,
    { hand_pbn: handPbn, seat },
  );
  return response.data;
}

/**
 * Get lightweight session info (seats, mode, join code).
 * Accessible to any authenticated user, not just seated players.
 * Used by the join flow when GET /practice/{id} returns 403.
 */
export async function getSessionInfo(
  sessionId: string,
): Promise<SessionInfo> {
  const response = await api.get<SessionInfo>(
    `/practice/${sessionId}/info`,
  );
  return response.data;
}

/**
 * Join a session at a specific seat.
 * Returns updated session info after joining.
 */
export async function joinSession(
  sessionId: string,
  seat: Seat,
): Promise<SessionInfo> {
  const response = await api.post<SessionInfo>(
    `/practice/${sessionId}/join`,
    { seat },
  );
  return response.data;
}

/**
 * Leave a session (seat reverts to computer control).
 * Redirects to the lobby after leaving.
 */
export async function leaveSession(
  sessionId: string,
): Promise<{ ok: boolean }> {
  const response = await api.post<{ ok: boolean }>(
    `/practice/${sessionId}/leave`,
  );
  return response.data;
}

/**
 * Look up a session by its 6-character join code.
 * Returns session info so the frontend can redirect to the join flow.
 */
export async function lookupByCode(code: string): Promise<SessionInfo> {
  const response = await api.get<SessionInfo>(`/practice/join/${code}`);
  return response.data;
}

// --- Analyze endpoints (Q1/Q2 query system) ---

/**
 * Analyze what a single bid means in the given auction position (Q2).
 * Returns matching rules and their combined promise about the hand.
 */
export async function analyzeBid(
  dealer: Seat,
  vulnerability: string,
  bids: string[],
  bid: string,
): Promise<BidAnalysis> {
  const response = await api.post<BidAnalysis>("/analyze/bid", {
    dealer,
    vulnerability,
    bids,
    bid,
  });
  return response.data;
}

/**
 * Analyze all legal bids at the current auction position (batch Q2).
 * Returns a dict mapping each legal bid string to its analysis.
 * Used by the practice page to pre-fetch all hover previews at once.
 */
export async function analyzeAllBids(
  dealer: Seat,
  vulnerability: string,
  bids: string[],
): Promise<AllBidsAnalysis> {
  const response = await api.post<AllBidsAnalysis>("/analyze/all-bids", {
    dealer,
    vulnerability,
    bids,
  });
  return response.data;
}

/**
 * Analyze the full auction: what do we know about each player's hand? (Q1).
 * Returns per-player hand descriptions, per-bid breakdowns, legal bids,
 * and whose turn it is. Used by the standalone auction analyzer page.
 */
export async function analyzeAuction(
  dealer: Seat,
  vulnerability: string,
  bids: string[],
): Promise<AuctionAnalysis> {
  const response = await api.post<AuctionAnalysis>("/analyze/auction", {
    dealer,
    vulnerability,
    bids,
  });
  return response.data;
}
