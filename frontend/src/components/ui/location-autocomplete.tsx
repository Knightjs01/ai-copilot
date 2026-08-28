"use client";

import * as React from "react";
import { MapPin } from "lucide-react";

import { Input } from "@/components/ui/input";
import { useLocationAutocomplete } from "@/lib/queries/geocoding";
import { cn } from "@/lib/utils";

interface LocationAutocompleteProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

// A plain Input + floating suggestion list, not cmdk -- cmdk's chrome here is styled specifically
// for the ⌘K command palette, not a normal form field. Free-typing always stays possible (the
// value isn't locked to a selected suggestion) so a candidate whose town isn't in Geoapify's
// results, or running against a backend with no GEOAPIFY_API_KEY configured, is never blocked.
export function LocationAutocomplete({
  id,
  value,
  onChange,
  placeholder,
}: LocationAutocompleteProps) {
  const [debouncedValue, setDebouncedValue] = React.useState(value);
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handle = setTimeout(() => setDebouncedValue(value), 300);
    return () => clearTimeout(handle);
  }, [value]);

  const { data: suggestions } = useLocationAutocomplete(debouncedValue);

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const showDropdown = open && !!suggestions && suggestions.length > 0;

  return (
    <div ref={containerRef} className="relative">
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        autoComplete="off"
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
      />
      {showDropdown && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-border bg-card shadow-lg shadow-slate-900/10">
          {suggestions.map((suggestion) => (
            <button
              key={`${suggestion.formatted}-${suggestion.lat}-${suggestion.lon}`}
              type="button"
              onClick={() => {
                onChange(suggestion.formatted);
                setOpen(false);
              }}
              className={cn(
                "flex w-full items-center gap-2 px-3.5 py-2.5 text-left text-sm text-foreground",
                "hover:bg-secondary"
              )}
            >
              <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="truncate">{suggestion.formatted}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
