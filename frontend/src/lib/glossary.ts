/**
 * Glossary of SAYC bridge bidding terms.
 *
 * Each entry has a term (the heading) and a plain-text definition.
 * Entries are pre-sorted alphabetically so the component can render
 * them directly without sorting at render time.
 */

export interface GlossaryEntry {
  term: string;
  definition: string;
}

/**
 * All glossary entries, sorted A-Z by term.
 *
 * Focus is on SAYC (Standard American Yellow Card) bidding terms.
 * Play, scoring, and duplicate-specific terms are omitted.
 */
export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "Balanced",
    definition:
      "A hand shape with no singleton or void. The balanced patterns are " +
      "4-3-3-3, 4-4-3-2, and 5-3-3-2. Semi-balanced includes 5-4-2-2, " +
      "6-3-2-2.",
  },
  {
    term: "Bergen Points",
    definition:
      "Marty Bergen's method for opener to re-evaluate hand strength " +
      "after a trump fit is found. Formula: HCP + 2 for a singleton " +
      "+ 4 for a void + 1 for each trump card beyond five + 1 for a " +
      "4- or 5-card side suit. Bergen points help opener decide " +
      "whether to accept or decline an invitation after a raise.",
  },
  {
    term: "Blackwood",
    definition:
      "A 4NT bid (when not quantitative) that asks partner how many aces " +
      "they hold. Responses: 5C = 0 or 4 aces, 5D = 1, 5H = 2, 5S = 3. " +
      "Used to check for missing aces before bidding slam.",
  },
  {
    term: "Dealer",
    definition:
      "The player who gets the first chance to bid. The deal rotates " +
      "clockwise: North, East, South, West. The dealer may open or pass.",
  },
  {
    term: "Distribution Points",
    definition:
      "Points added to HCP for long or short suits. For opener: add 1 " +
      "for each card over four in any suit (a 6-card suit = 2 points). " +
      "For responder with a fit: add shortness points (see Dummy Points).",
  },
  {
    term: "Double",
    definition:
      "A call that increases the scoring value of the opponents' contract " +
      "if they play it. In competitive auctions, a double can also be " +
      "used conventionally (takeout double, negative double) to show " +
      "strength and shape rather than a desire to penalize.",
  },
  {
    term: "Doubleton",
    definition: "Exactly two cards in a suit.",
  },
  {
    term: "Dummy Points",
    definition:
      "Points added by responder (the future dummy) when raising " +
      "partner's suit. Add shortness points for the trump fit: " +
      "5 for a void, 3 for a singleton, 1 for a doubleton. These " +
      "reflect how short suits gain ruffing value when dummy.",
  },
  {
    term: "Fit",
    definition:
      "When the partnership holds 8 or more cards in a suit combined, " +
      "they have a fit in that suit. An 8-card fit is usually enough " +
      "to make that suit trump.",
  },
  {
    term: "Forcing",
    definition:
      "A bid that requires partner to bid again (not pass). A forcing " +
      "bid promises more information is coming. For example, a new suit " +
      "by an unpassed responder is forcing for one round in SAYC.",
  },
  {
    term: "Game",
    definition:
      "A contract worth enough tricks for game bonus: 3NT (9 tricks), " +
      "4H/4S (10 tricks), or 5C/5D (11 tricks). Typically requires " +
      "about 25-26 combined HCP.",
  },
  {
    term: "Gerber",
    definition:
      "A 4C bid directly over partner's 1NT or 2NT opening that asks " +
      "for aces (similar to Blackwood but at a lower level). Responses: " +
      "4D = 0 or 4 aces, 4H = 1, 4S = 2, 4NT = 3. A follow-up of " +
      "5C asks for kings.",
  },
  {
    term: "Grand Slam",
    definition:
      "A contract at the 7-level, requiring all 13 tricks. Typically " +
      "needs 37+ combined points and all four aces.",
  },
  {
    term: "HCP (High Card Points)",
    definition:
      "The basic hand evaluation method. Ace = 4, King = 3, Queen = 2, " +
      "Jack = 1. A full deck has 40 HCP total. An average hand has 10 HCP.",
  },
  {
    term: "Invitational",
    definition:
      "A bid that invites partner to bid game (or slam) but does not " +
      "force them. Partner can accept with a maximum or decline with a " +
      "minimum. For example, a raise from 2H to 3H is invitational.",
  },
  {
    term: "Jacoby 2NT",
    definition:
      "A 2NT response to partner's 1H or 1S opening, showing 13+ " +
      "points with 4+ card support. It's game-forcing and asks opener " +
      "to describe their hand further (shortness, extra length, or " +
      "strength).",
  },
  {
    term: "Jacoby Transfer",
    definition:
      "Over partner's 1NT opening, a 2D bid shows 5+ hearts and asks " +
      "opener to bid 2H, while a 2H bid shows 5+ spades and asks " +
      "opener to bid 2S. This lets the strong NT hand become declarer. " +
      "Used with any strength. Over 2NT, transfers are at the 3-level " +
      "(3D and 3H).",
  },
  {
    term: "Jump Shift",
    definition:
      "A response that skips a level in a new suit (e.g., 1H-3C). " +
      "In SAYC, a jump shift by responder shows 19+ points and is " +
      "forcing to game.",
  },
  {
    term: "Major Suit",
    definition:
      "Hearts and spades. Major suits score 30 points per trick, making " +
      "game reachable at the 4-level (4H or 4S = 10 tricks).",
  },
  {
    term: "Minor Suit",
    definition:
      "Clubs and diamonds. Minor suits score 20 points per trick, " +
      "requiring the 5-level for game (5C or 5D = 11 tricks). " +
      "Partnerships often prefer 3NT over a minor-suit game.",
  },
  {
    term: "Notrump",
    definition:
      "A contract played without a trump suit. The first trick in each " +
      "suit is worth 40 points, subsequent tricks 30 each, making game " +
      "at 3NT (9 tricks).",
  },
  {
    term: "Opening Bid",
    definition:
      "The first non-pass bid in the auction. In SAYC, opening " +
      "generally requires 13+ points (HCP + distribution) for a " +
      "1-level suit bid, 15-17 HCP balanced for 1NT, or special " +
      "requirements for other openings (2C, 2NT, preempts).",
  },
  {
    term: "Overcall",
    definition:
      "A bid made after the opponents have opened. Shows a good 5+ " +
      "card suit and roughly 8-16 HCP at the 1-level. Overcalls are " +
      "not currently implemented in Kibitzer's SAYC rules.",
  },
  {
    term: "Pass",
    definition:
      "A call that makes no bid. If all four players pass without " +
      "anyone bidding, the hand is passed out (no contract). Three " +
      "consecutive passes after a bid end the auction.",
  },
  {
    term: "Preempt",
    definition:
      "A high-level opening bid with a long suit and weak hand, " +
      "designed to consume bidding space from opponents. Weak twos " +
      "(2D/2H/2S) show 5-11 HCP with a good 6-card suit. Three-level " +
      "preempts show a 7-card suit.",
  },
  {
    term: "Puppet (to 3C)",
    definition:
      "Over 1NT, a 2S bid that forces opener to bid 3C. Responder " +
      "then passes (with clubs) or corrects to 3D (with diamonds). " +
      "This sign-off mechanism lets the weak hand play in a minor at " +
      "the 3-level. Over 2NT, the puppet bid is 3S (forcing 4C).",
  },
  {
    term: "Quantitative 4NT",
    definition:
      "A 4NT bid directly over partner's NT opening that invites " +
      "slam (not Blackwood). Opener passes with a minimum or bids " +
      "6NT with a maximum. Example: 1NT-4NT with 15-17 HCP.",
  },
  {
    term: "Quick Tricks",
    definition:
      "A measure of how many tricks a hand can take immediately. " +
      "AK in a suit = 2, AQ = 1.5, A alone = 1, KQ = 1, K alone = 0.5. " +
      "Opening bids typically need at least 2 quick tricks.",
  },
  {
    term: "Rebid",
    definition:
      "Opener's second bid. After opening and hearing partner's " +
      "response, the opener rebids to further describe their hand " +
      "(strength and shape).",
  },
  {
    term: "Redouble",
    definition:
      "A call available only after the opponents double. Increases " +
      "scoring further. Can also be used conventionally to show " +
      "strength (10+ HCP after partner's opening is doubled).",
  },
  {
    term: "Reresponse",
    definition:
      "Responder's second bid (the fourth bid of the auction). After " +
      "the opening, response, and rebid, the responder makes their " +
      "second call to place the final contract or continue exploring.",
  },
  {
    term: "Response",
    definition:
      "The first bid by opener's partner. A new suit at the 1-level " +
      "shows 6+ points, a 2-over-1 response shows 10+ points, and " +
      "a 1NT response shows 6-10 HCP.",
  },
  {
    term: "SAYC",
    definition:
      "Standard American Yellow Card. A widely-used bidding system " +
      "published by the ACBL (American Contract Bridge League). It " +
      "uses 5-card majors, a strong 1NT (15-17), 2-over-1 forcing " +
      "one round, and standard conventions (Stayman, Jacoby, etc.).",
  },
  {
    term: "Sign-off",
    definition:
      "A bid that says 'I want to stop here.' Partner is expected " +
      "to pass. For example, after a Jacoby transfer is completed " +
      "(1NT-2D-2H), passing 2H is a sign-off.",
  },
  {
    term: "Singleton",
    definition: "Exactly one card in a suit.",
  },
  {
    term: "Slam",
    definition:
      "A contract at the 6-level (small slam, 12 tricks) or 7-level " +
      "(grand slam, 13 tricks). A small slam typically requires 33+ " +
      "combined points.",
  },
  {
    term: "Stayman",
    definition:
      "Over partner's 1NT, a 2C bid asks whether opener has a 4-card " +
      "major. Opener replies 2D (no major), 2H (4+ hearts), or 2S " +
      "(4+ spades). Requires 8+ HCP and a 4-card major. Over 2NT, " +
      "Stayman is 3C with the same meaning.",
  },
  {
    term: "Strong 2C",
    definition:
      "A 2C opening showing 22+ HCP (or 9+ tricks). The strongest " +
      "opening bid in SAYC. It is artificial and forcing; responder " +
      "usually bids 2D (waiting) unless holding a good 5+ card suit " +
      "with 8+ HCP.",
  },
  {
    term: "Support",
    definition:
      "Holding cards in partner's suit. Three-card support for a " +
      "major (partner opened 5+) gives an 8-card fit. Four-card " +
      "support is stronger and may warrant a jump raise.",
  },
  {
    term: "Texas Transfer",
    definition:
      "Over 1NT or 2NT, a jump to 4D transfers to 4H and 4H " +
      "transfers to 4S. Used with 6+ card majors and game values " +
      "when you want to play in 4 of a major as a sign-off.",
  },
  {
    term: "Total Points",
    definition:
      "HCP plus distribution points. Used to evaluate hand strength " +
      "for suit contracts. For example, a hand with 12 HCP and a " +
      "6-card suit has 14 total points (12 + 2 length points).",
  },
  {
    term: "Trump",
    definition:
      "The suit named in the final contract. Trump cards beat cards " +
      "of other suits. Choosing the right trump suit (one where the " +
      "partnership has a fit) is a key goal of bidding.",
  },
  {
    term: "Void",
    definition: "No cards in a suit. Very valuable for trump contracts.",
  },
  {
    term: "Vulnerability",
    definition:
      "A scoring condition that increases both bonuses and penalties. " +
      "Each side is either vulnerable or not vulnerable. Vulnerable " +
      "games and slams score more, but going down costs more too.",
  },
  {
    term: "Weak Two",
    definition:
      "An opening bid of 2D, 2H, or 2S showing a good 6-card suit " +
      "and 5-11 HCP. A preemptive bid that describes the hand " +
      "precisely while consuming opponents' bidding space. 2C is " +
      "reserved for strong hands in SAYC.",
  },
];
