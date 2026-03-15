/**
 * Glossary slide-out sheet for bridge bidding terms.
 *
 * Opens from the right side of the screen when the user clicks the
 * "Glossary" button in the nav bar. Contains a scrollable list of
 * alphabetically-sorted SAYC bidding terms with definitions.
 *
 * A search input at the top filters terms in real time, matching
 * against both the term name and definition text (case-insensitive).
 */
import { useState } from "react";
import { BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { GLOSSARY } from "@/lib/glossary";

export default function Glossary() {
  const [search, setSearch] = useState("");

  // Filter entries by matching the search string against term or definition.
  const filtered = search
    ? GLOSSARY.filter((entry) => {
        const q = search.toLowerCase();
        return (
          entry.term.toLowerCase().includes(q) ||
          entry.definition.toLowerCase().includes(q)
        );
      })
    : GLOSSARY;

  return (
    <Sheet>
      {/* Trigger button rendered inline in the nav bar. */}
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-1.5">
          <BookOpen className="size-4" />
          <span className="hidden sm:inline">Glossary</span>
        </Button>
      </SheetTrigger>

      {/* Sheet content: slides in from the right. */}
      <SheetContent side="right" className="flex flex-col overflow-hidden">
        <SheetHeader>
          <SheetTitle>Bridge Glossary</SheetTitle>
        </SheetHeader>

        {/* Search input -- filters the term list below. */}
        <div className="px-4">
          <Input
            placeholder="Search terms..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 text-sm"
          />
        </div>

        {/* Scrollable list of glossary entries. */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          {filtered.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No matching terms found.
            </p>
          ) : (
            <dl className="space-y-4">
              {filtered.map((entry) => (
                <div key={entry.term}>
                  <dt className="font-semibold text-foreground">
                    {entry.term}
                  </dt>
                  <dd className="mt-0.5 text-sm leading-relaxed text-muted-foreground">
                    {entry.definition}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
