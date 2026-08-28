"use client";

import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ContentItem } from "@/lib/types";

const MAX_ITEMS = 12;

// Shared editor for `values` and `hiring_highlights` -- both are the same {title, body} shape,
// rendered as repeatable rows (add/edit/remove), same interaction pattern as TagInput but with
// two fields per entry instead of one.
export function ContentItemListEditor({
  items,
  onChange,
  addLabel,
}: {
  items: ContentItem[];
  onChange: (items: ContentItem[]) => void;
  addLabel: string;
}) {
  const updateItem = (index: number, patch: Partial<ContentItem>) => {
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const addItem = () => {
    onChange([...items, { title: "", body: "" }]);
  };

  return (
    <div className="flex flex-col gap-3">
      {items.map((item, index) => (
        <div
          key={index}
          className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3.5"
        >
          <div className="flex items-center gap-2">
            <Input
              value={item.title}
              onChange={(e) => updateItem(index, { title: e.target.value })}
              placeholder="Title"
              maxLength={100}
              className="flex-1"
            />
            <button
              type="button"
              onClick={() => removeItem(index)}
              className="shrink-0 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Remove"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <Textarea
            value={item.body}
            onChange={(e) => updateItem(index, { body: e.target.value })}
            placeholder="Short description…"
            rows={2}
            maxLength={300}
          />
        </div>
      ))}
      {items.length < MAX_ITEMS && (
        <Button type="button" variant="secondary" size="sm" onClick={addItem} className="self-start">
          <Plus className="h-3.5 w-3.5" />
          {addLabel}
        </Button>
      )}
    </div>
  );
}
