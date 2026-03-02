/**
 * Row of toggle buttons for picking vulnerability (None/NS/EW/Both).
 * Same visual style as SeatPicker.
 */
import { Button } from "@/components/ui/button";

/** Vulnerability options matching the backend's enum values. */
const VULN_OPTIONS = [
  { value: "None", label: "None" },
  { value: "NS", label: "N-S" },
  { value: "EW", label: "E-W" },
  { value: "Both", label: "Both" },
] as const;

interface VulnPickerProps {
  selected: string;
  onSelect: (vuln: string) => void;
}

export default function VulnPicker({ selected, onSelect }: VulnPickerProps) {
  return (
    <div className="flex gap-2">
      {VULN_OPTIONS.map(({ value, label }) => (
        <Button
          key={value}
          type="button"
          variant={selected === value ? "action" : "outline"}
          className="min-w-16"
          onClick={() => onSelect(value)}
        >
          {label}
        </Button>
      ))}
    </div>
  );
}
