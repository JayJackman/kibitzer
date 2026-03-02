/**
 * Shown when the auction is complete: displays the final contract
 * and all 4 hands arranged in a compass layout.
 *
 * In helper mode, some seats may not have hands entered -- those
 * positions are left empty in the compass layout.
 */
import type { PracticeState, Seat } from "@/api/types";
import { SUIT_COLORS, SUIT_SYMBOLS } from "@/lib/constants";
import { countHcp, DECLARER_ARROW, EMPTY_HAND } from "@/lib/bridge";
import HandDisplay from "@/components/hand/HandDisplay";

export default function AuctionComplete({ state }: { state: PracticeState }) {
  const { auction, all_hands } = state;

  /** Get the hand for a seat, falling back to an empty placeholder. */
  function handFor(seat: Seat) {
    return all_hands?.[seat] ?? EMPTY_HAND;
  }

  /** Title with HCP if the hand has cards, just the seat name otherwise. */
  function titleFor(seat: Seat, label: string) {
    const h = all_hands?.[seat];
    return h ? `${label} (${countHcp(h)})` : label;
  }

  return (
    <div className="flex flex-col gap-4">
      {/*
       * All 4 hands in compass layout with contract in the center:
       *            North
       *   West   [Contract]   East
       *            South
       * Seats without hands render with empty suit rows.
       */}
      <div className="grid grid-cols-3 gap-2">
        {/* Top row: North in the center */}
        <div />
        <HandDisplay hand={handFor("N")} title={titleFor("N", "North")} isPlayer={state.your_seat === "N"} />
        <div />

        {/* Middle row: West, Contract, East */}
        <HandDisplay hand={handFor("W")} title={titleFor("W", "West")} isPlayer={state.your_seat === "W"} />
        {auction.contract ? (
          <ContractDisplay contract={auction.contract} />
        ) : (
          <div />
        )}
        <HandDisplay hand={handFor("E")} title={titleFor("E", "East")} isPlayer={state.your_seat === "E"} />

        {/* Bottom row: South in the center */}
        <div />
        <HandDisplay hand={handFor("S")} title={titleFor("S", "South")} isPlayer={state.your_seat === "S"} />
        <div />
      </div>
    </div>
  );
}

/**
 * Displays the contract in the center of the compass layout with an arrow
 * pointing toward the declarer. For N/S the arrow is above/below the bid
 * (vertical stack). For W/E the arrow is to the left/right (horizontal).
 */
function ContractDisplay({ contract }: { contract: PracticeState["auction"]["contract"] }) {
  if (!contract) return null;

  if (contract.passed_out) {
    return (
      <div className="flex items-center justify-center">
        <p className="text-center text-2xl font-bold">Passed Out</p>
      </div>
    );
  }

  /*
   * Grid trick: both the bid and arrow occupy the same single cell
   * (row 1 / col 1). The bid is centered, the arrow is self-aligned
   * to the edge nearest the declarer's hand. This keeps the bid
   * perfectly centered regardless of arrow size or direction.
   */
  const d = contract.declarer;
  const arrowAlign: Record<Seat, string> = {
    N: "self-start justify-self-center",   // top center
    S: "self-end justify-self-center",     // bottom center
    W: "self-center justify-self-start",   // middle left
    E: "self-center justify-self-end",     // middle right
  };

  return (
    <div className="grid">
      {/* Bid -- centered in the cell */}
      <span className="col-start-1 row-start-1 place-self-center text-3xl font-bold">
        {contract.level}
        <ContractSuit suit={contract.suit} />
        {contract.doubled && " X"}
        {contract.redoubled && " XX"}
      </span>
      {/* Arrow -- same cell, pushed to the edge toward the declarer */}
      <span className={`col-start-1 row-start-1 text-4xl leading-none ${arrowAlign[d]}`}>
        {DECLARER_ARROW[d]}
      </span>
    </div>
  );
}

/**
 * Renders the contract's suit as a colored Unicode symbol.
 * For suit contracts (C/D/H/S), shows the symbol in the suit's color.
 * For notrump, shows "NT" unstyled.
 */
function ContractSuit({ suit }: { suit: string }) {
  if (suit in SUIT_SYMBOLS) {
    const key = suit as keyof typeof SUIT_SYMBOLS;
    return (
      <span className={SUIT_COLORS[key]}>
        {SUIT_SYMBOLS[key]}
      </span>
    );
  }
  return <>{suit}</>;
}
