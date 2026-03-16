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

// --- Shared domain types ---

/** The four compass seats at a bridge table. */
export type Seat = "N" | "E" | "S" | "W";

/** Session mode (mirrors backend SessionMode enum values). */
export type SessionMode = "practice" | "helper";

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
  declarer: Seat;
  doubled: boolean;
  redoubled: boolean;
  passed_out: boolean;
}

/** A single bid in the auction history. */
export interface AuctionBid {
  seat: Seat;
  bid: string;
  explanation: string | null;
  /** Whether this player bid matched the engine's recommendation (null for computer bids). */
  matched_engine: boolean | null;
}

/** Full auction state: history, dealer, vulnerability, and optional contract. */
export interface Auction {
  dealer: Seat;
  vulnerability: string;
  bids: AuctionBid[];
  is_complete: boolean;
  current_seat: Seat | null;
  contract: Contract | null;
}

/** A bid placed by a computer-controlled seat (with engine explanation). */
export interface ComputerBid {
  seat: Seat;
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
  mode: SessionMode;
  join_code: string;
  your_seat: Seat;
  /** Player's hand (null in helper mode before hand entry via set_hand). */
  hand: Hand | null;
  /** Hand metrics (null when hand is null). */
  hand_evaluation: HandEvaluation | null;
  auction: Auction;
  computer_bids: ComputerBid[];
  is_my_turn: boolean;
  legal_bids: string[];
  last_feedback: BidFeedback | null;
  all_hands: Record<Seat, Hand> | null;
  hand_number: number;
  /** Username per seat (null = computer). */
  players: Record<Seat, string | null>;
  /** Which human seat we're waiting on (null if computer's turn or auction complete). */
  waiting_for: Seat | null;
  /** True when an unoccupied seat needs to bid and the caller can proxy-bid (helper mode). */
  can_proxy_bid: boolean;
  /** The unoccupied seat to proxy-bid for (set when can_proxy_bid is true). */
  proxy_seat: Seat | null;
  /** Whether there are bids that can be undone. */
  can_undo: boolean;
}

/** Lightweight session info for the join UI and session lookup. */
export interface SessionInfo {
  id: string;
  mode: SessionMode;
  join_code: string;
  players: Record<Seat, string | null>;
  available_seats: Seat[];
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

// --- Analyze types (Q1/Q2 query system) ---
// Backend source: src/bridge/api/analyze/schemas.py

/** A min/max range. null means unconstrained on that side. */
export interface Bound {
  min: number | null;
  max: number | null;
}

/** What we know about a hand from the auction (HCP, suit lengths, shape, aces/kings). */
export interface HandDescription {
  hcp: Bound;
  total_pts: Bound;
  /** Suit lengths keyed by lowercase suit name ("spades", "hearts", etc.). */
  lengths: Record<string, Bound>;
  balanced: boolean | null;
  /** Ace count range (0-4). */
  aces: Bound;
  /** King count range (0-4). */
  kings: Bound;
}

/** A single rule that matched a bid, with what it promises about the hand. */
export interface AnalysisRuleMatch {
  rule_name: string;
  explanation: string;
  promise: HandDescription;
}

/** Analysis of what a single bid means: matching rules + combined promise. */
export interface BidAnalysis {
  bid: string;
  matches: AnalysisRuleMatch[];
  /** Union of all matches' promises (weakest guarantee across candidates). */
  promise: HandDescription;
}

/** Batch analysis of all legal bids at the current position. */
export interface AllBidsAnalysis {
  /** Maps bid strings (e.g. "1S", "Pass") to their analysis. */
  analyses: Record<string, BidAnalysis>;
}

/** Full auction analysis: what we know about each player + per-bid breakdown. */
export interface AuctionAnalysis {
  /** Per-seat hand descriptions, keyed by seat letter ("N", "E", "S", "W"). */
  players: Record<string, HandDescription>;
  /** Per-bid analyses in auction order (non-pass bids only). */
  bid_analyses: BidAnalysis[];
  /** Cumulative per-seat hand descriptions at each bid point (parallel to bid_analyses). */
  bid_cumulative: HandDescription[];
  /** Legal bids at the current position (empty if auction is complete). */
  legal_bids: string[];
  /** Whose turn it is (null if auction is complete). */
  current_seat: Seat | null;
}
