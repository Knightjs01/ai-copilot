"use client";

import * as React from "react";
import { Plus, Sparkles, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface TagInputProps {
  id?: string;
  values: string[];
  onValuesChange: (values: string[]) => void;
  placeholder?: string;
  // Real AI-generated suggestions only — never a fabricated "smart" list. Filtered against
  // `values` internally (case-insensitive) so an already-selected tag never shows twice.
  suggestions?: string[];
  onRequestSuggestions?: () => void;
  isSuggesting?: boolean;
  suggestionsButtonLabel?: string;
}

function addTag(values: string[], raw: string): string[] {
  const trimmed = raw.trim();
  if (!trimmed) return values;
  const exists = values.some((v) => v.toLowerCase() === trimmed.toLowerCase());
  return exists ? values : [...values, trimmed];
}

export function TagInput({
  id,
  values,
  onValuesChange,
  placeholder,
  suggestions,
  onRequestSuggestions,
  isSuggesting,
  suggestionsButtonLabel = "Suggest more",
}: TagInputProps) {
  const [draft, setDraft] = React.useState("");

  const commitDraft = () => {
    if (!draft.trim()) return;
    onValuesChange(addTag(values, draft));
    setDraft("");
  };

  const offeredSuggestions = (suggestions ?? []).filter(
    (s) => !values.some((v) => v.toLowerCase() === s.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-2.5">
      <div
        className={cn(
          "flex min-h-[44px] flex-wrap items-center gap-1.5 rounded-xl border border-border bg-card px-2.5 py-2 focus-within:ring-2 focus-within:ring-ring"
        )}
      >
        {values.map((value) => (
          <span
            key={value}
            className="inline-flex items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-xs font-medium text-brand-foreground"
          >
            {value}
            <button
              type="button"
              onClick={() => onValuesChange(values.filter((v) => v !== value))}
              className="rounded-full p-0.5 transition-colors hover:bg-brand-foreground/20"
              aria-label={`Remove ${value}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          id={id}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              commitDraft();
            } else if (e.key === "Backspace" && draft === "" && values.length > 0) {
              onValuesChange(values.slice(0, -1));
            }
          }}
          onBlur={commitDraft}
          placeholder={placeholder}
          className="min-w-[120px] flex-1 border-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
        />
      </div>

      {onRequestSuggestions && (
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="self-start"
          onClick={onRequestSuggestions}
          disabled={isSuggesting}
        >
          <Sparkles className="h-3.5 w-3.5" />
          {isSuggesting ? "Thinking…" : suggestionsButtonLabel}
        </Button>
      )}

      {offeredSuggestions.length > 0 && (
        <div className="flex flex-col gap-2 rounded-xl border border-info/20 bg-info/5 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-info">
            Phantom AI suggests — tap to add
          </p>
          <div className="flex flex-wrap gap-2">
            {offeredSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => onValuesChange(addTag(values, suggestion))}
                className="inline-flex items-center gap-1 rounded-full border border-info/30 bg-card px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-info/10"
              >
                <Plus className="h-3 w-3" /> {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
