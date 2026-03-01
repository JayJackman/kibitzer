/**
 * TypeScript interfaces mirroring the backend Pydantic schemas.
 *
 * These are the shapes of JSON data returned by the API. Keeping them
 * separate from the endpoint functions lets components import just the
 * types they need without pulling in the axios client.
 *
 * Backend sources:
 * - Auth types: src/bridge/api/auth/schemas.py
 * - Practice types: src/bridge/api/practice/schemas.py
 */

// --- Auth types ---

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

// --- Practice types ---

/** Cards grouped by suit, each as a list of rank strings (e.g. ["A", "K", "10", "3"]). */
export interface Hand {
  spades: string[];
  hearts: string[];
  diamonds: string[];
  clubs: string[];
}

/** Pre-computed hand metrics (HCP, shape, etc.). */
export interface HandEvaluation {
  hcp: number;
  length_points: number;
  total_points: number;
  distribution_points: number;
  controls: number;
  quick_tricks: number;
  losers: number;
  shape: number[];
  is_balanced: boolean;
}

/** Final contract of a completed auction. */
export interface Contract {
  level: number;
  suit: string;
  declarer: string;
  doubled: boolean;
  redoubled: boolean;
  passed_out: boolean;
}

/** A single bid in the auction history. */
export interface AuctionBid {
  seat: string;
  bid: string;
  explanation: string | null;
}

/** Full auction state: history, dealer, vulnerability, and optional contract. */
export interface Auction {
  dealer: string;
  vulnerability: string;
  bids: AuctionBid[];
  is_complete: boolean;
  current_seat: string | null;
  contract: Contract | null;
}

/** A bid placed by a computer-controlled seat (with engine explanation). */
export interface ComputerBid {
  seat: string;
  bid: string;
  explanation: string;
}

/** Feedback after the human places a bid -- did it match the engine? */
export interface BidFeedback {
  matched_engine: boolean;
  engine_bid: string;
  engine_explanation: string;
}

/** Full session state returned by GET /api/practice/{id}. */
export interface PracticeState {
  id: string;
  your_seat: string;
  hand: Hand;
  hand_evaluation: HandEvaluation;
  auction: Auction;
  computer_bids: ComputerBid[];
  is_my_turn: boolean;
  legal_bids: string[];
  last_feedback: BidFeedback | null;
  all_hands: Record<string, Hand> | null;
  hand_number: number;
}

/** A single condition evaluation result in the thought process. */
export interface Condition {
  label: string;
  detail: string;
  passed: boolean;
}

/** One rule evaluated during the engine's thought process. */
export interface ThoughtStep {
  rule_name: string;
  passed: boolean;
  bid: string | null;
  conditions: Condition[];
}

/** Full trace of how the engine reached its decision. */
export interface ThoughtProcess {
  steps: ThoughtStep[];
}

/** A single rule's bid recommendation. */
export interface RuleResult {
  bid: string;
  rule_name: string;
  explanation: string;
  forcing: boolean;
  alerts: string[];
}

/** Engine recommendation with thought process (GET /api/practice/{id}/advise). */
export interface Advice {
  recommended: RuleResult;
  alternatives: RuleResult[];
  thought_process: ThoughtProcess;
  phase: string;
}
