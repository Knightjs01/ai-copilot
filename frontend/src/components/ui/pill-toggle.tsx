"use client";

import { cn } from "@/lib/utils";

interface PillOption<T extends string> {
  value: T;
  label: string;
}

interface PillToggleGroupProps<T extends string> {
  options: PillOption<T>[];
  value: T | null | undefined;
  onChange: (value: T) => void;
  disabled?: boolean;
  className?: string;
}

export function PillToggleGroup<T extends string>({
  options,
  value,
  onChange,
  disabled = false,
  className,
}: PillToggleGroupProps<T>) {
  return (
    <div className={cn("inline-flex flex-wrap gap-2", className)}>
      {options.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
              isActive
                ? "border-primary bg-primary text-primary-foreground"
                // bg-card, not bg-white — see Card's comment in card.tsx for why.
                : "border-border bg-card text-foreground hover:bg-secondary"
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
