/**
 * Row of toggle buttons for picking a seat (N/E/S/W).
 * The selected seat is highlighted with the action variant;
 * unselected seats use the outline variant with muted text.
 * Reused for both "your seat" and "dealer" selection on the lobby.
 */
import type { Seat } from "@/api/types";
import { SEAT_LABELS } from "@/lib/constants";
import { ALL_SEATS } from "@/lib/bridge";
import { Button } from "@/components/ui/button";

interface SeatPickerProps {
  selected: Seat;
  onSelect: (seat: Seat) => void;
}

export default function SeatPicker({ selected, onSelect }: SeatPickerProps) {
  return (
    <div className="flex gap-2">
      {ALL_SEATS.map((seat) => (
        <Button
          key={seat}
          type="button"
          variant={selected === seat ? "action" : "outline"}
          className="min-w-16"
          onClick={() => onSelect(seat)}
        >
          {SEAT_LABELS[seat]}
        </Button>
      ))}
    </div>
  );
}
