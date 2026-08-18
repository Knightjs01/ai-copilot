"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export interface PassportWizardStep {
  id: string;
  label: string;
}

interface PassportStepRailProps {
  steps: PassportWizardStep[];
  activeIndex: number;
  completedIndices: Set<number>;
  onStepClick: (index: number) => void;
}

export function PassportStepRail({
  steps,
  activeIndex,
  completedIndices,
  onStepClick,
}: PassportStepRailProps) {
  return (
    <>
      <nav className="hidden flex-col gap-1 lg:flex" aria-label="Passport setup steps">
        {steps.map((step, index) => {
          const isCompleted = completedIndices.has(index);
          const isActive = index === activeIndex;
          // Only lets you jump to a step you've already reached — never past the current one,
          // since later steps may depend on earlier data (e.g. Review reads everything).
          const clickable = isCompleted || index <= activeIndex;
          return (
            <button
              key={step.id}
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onStepClick(index)}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors",
                isActive ? "bg-secondary font-medium text-foreground" : "text-muted-foreground",
                clickable && !isActive && "hover:bg-secondary/60 hover:text-foreground",
                !clickable && "cursor-default opacity-60"
              )}
            >
              <span
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px] font-semibold",
                  isCompleted
                    ? "border-brand bg-brand text-brand-foreground"
                    : isActive
                      ? "border-brand text-brand"
                      : "border-border text-muted-foreground"
                )}
              >
                {isCompleted ? <Check className="h-3.5 w-3.5" /> : index + 1}
              </span>
              {step.label}
            </button>
          );
        })}
      </nav>

      <div className="flex items-center gap-2 lg:hidden" aria-label="Passport setup steps">
        {steps.map((step, index) => {
          const isCompleted = completedIndices.has(index);
          const isActive = index === activeIndex;
          return (
            <div key={step.id} className="flex min-w-0 flex-1 flex-col items-center gap-1.5">
              <span
                className={cn(
                  "h-1.5 w-full rounded-full",
                  isCompleted || isActive ? "bg-brand" : "bg-secondary"
                )}
              />
              <span
                className={cn(
                  "w-full truncate text-center text-[10px] font-medium",
                  isActive ? "text-foreground" : "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </>
  );
}
