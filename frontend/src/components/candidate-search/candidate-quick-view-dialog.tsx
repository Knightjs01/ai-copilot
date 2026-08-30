"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight, MessageCircle, X } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { DimensionBreakdownList } from "@/components/dimension-breakdown-list";
import { MatchToneList } from "@/components/shadow/match-tone-list";
import type { QuickTalentPoolAction } from "@/components/candidate-search/candidate-search-result-card";
import { Spinner } from "@/components/ui/spinner";
import {
  MATCH_TIER_VARIANT,
  RELATIONSHIP_STATUS_LABEL,
  RELATIONSHIP_STATUS_VARIANT,
} from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { cn } from "@/lib/utils";
import type { CandidateSearchResult } from "@/lib/types";

export function CandidateQuickViewDialog({
  open,
  onOpenChange,
  result,
  hasPrevious,
  hasNext,
  onPrevious,
  onNext,
  talentPoolAction,
  onPass,
  onRequestIntroduction,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: CandidateSearchResult | null;
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
  talentPoolAction?: QuickTalentPoolAction;
  onPass?: () => void;
  onRequestIntroduction?: () => void;
}) {
  const container = useThemeScopeContainer();

  React.useEffect(() => {
    if (!open || !result) return;
    const activeResult = result;

    function isTypingTarget(target: EventTarget | null): boolean {
      if (!(target instanceof HTMLElement)) return false;
      const tag = target.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (isTypingTarget(document.activeElement) || isTypingTarget(event.target)) return;

      switch (event.key) {
        case "j":
        case "ArrowRight":
          if (hasNext) {
            event.preventDefault();
            onNext();
          }
          break;
        case "k":
        case "ArrowLeft":
          if (hasPrevious) {
            event.preventDefault();
            onPrevious();
          }
          break;
        case "s":
          if (talentPoolAction?.state === "idle") {
            event.preventDefault();
            talentPoolAction.onAdd();
          }
          break;
        case "p":
          if (onPass) {
            event.preventDefault();
            onPass();
          }
          break;
        case "i":
          if (onRequestIntroduction && activeResult.relationship_status !== "introduction_pending") {
            event.preventDefault();
            onRequestIntroduction();
          }
          break;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, result, hasNext, hasPrevious, onNext, onPrevious, talentPoolAction, onPass, onRequestIntroduction]);

  if (!result) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container} className="max-w-2xl">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <Avatar name={result.callsign} className="mt-0.5 h-10 w-10 shrink-0 text-sm" />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-foreground">{result.callsign}</h2>
                {result.relationship_status !== "new" && (
                  <Badge variant={RELATIONSHIP_STATUS_VARIANT[result.relationship_status]}>
                    {RELATIONSHIP_STATUS_LABEL[result.relationship_status]}
                  </Badge>
                )}
              </div>
              {result.headline && (
                <p className="text-sm text-muted-foreground">{result.headline}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {[
                  result.seniority,
                  result.years_experience != null ? `${result.years_experience} yrs` : null,
                  result.location,
                  result.remote_preference,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1 pr-8">
            <Badge variant={MATCH_TIER_VARIANT[result.match_tier]}>{result.match_tier}</Badge>
            <span className="text-xs font-medium text-muted-foreground">
              {result.match_score}% match
            </span>
          </div>
        </div>

        <div className="mt-4 flex max-h-[60vh] flex-col gap-5 overflow-y-auto pr-1">
          {result.summary && <p className="text-sm text-foreground">{result.summary}</p>}

          {result.skills.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Skills
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {result.skills.map((skill) => (
                  <Badge key={skill} variant="outline" className="text-[10px]">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {result.career_entries.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Career history
              </h4>
              <div className="flex flex-col gap-1.5 text-sm text-muted-foreground">
                {result.career_entries.map((entry, i) => (
                  <p key={i}>
                    {entry.title} · {entry.company_name_anonymized}
                    {entry.is_current ? " (current)" : ""}
                  </p>
                ))}
              </div>
            </div>
          )}

          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Why Phantom recommends them
            </h4>
            <p className="mb-3 text-sm text-foreground">{result.match_summary}</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <MatchToneList title="Strengths" items={result.strengths} tone="positive" />
              <MatchToneList title="Gaps" items={result.gaps} tone="caution" />
            </div>
          </div>

          {result.dimension_breakdown.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Match breakdown
              </h4>
              <DimensionBreakdownList dimensions={result.dimension_breakdown} />
            </div>
          )}
        </div>

        <div className="mt-5 flex items-center justify-between gap-3 border-t border-border pt-4">
          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={onPrevious}
              disabled={!hasPrevious}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button type="button" variant="secondary" size="sm" onClick={onNext} disabled={!hasNext}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center gap-2">
            {onPass && (
              <Button type="button" variant="secondary" size="sm" onClick={onPass}>
                <X className="mr-1 h-3.5 w-3.5" />
                Pass
              </Button>
            )}
            {onRequestIntroduction && (
              <Button
                type="button"
                variant="brand"
                size="sm"
                onClick={onRequestIntroduction}
                disabled={result.relationship_status === "introduction_pending"}
              >
                <MessageCircle className="mr-1 h-3.5 w-3.5" />
                {result.relationship_status === "introduction_pending"
                  ? "Introduction requested"
                  : "Request introduction"}
              </Button>
            )}
            {talentPoolAction && (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={talentPoolAction.onAdd}
                disabled={talentPoolAction.state !== "idle"}
                className={cn(talentPoolAction.state === "added" && "opacity-70")}
              >
                {talentPoolAction.state === "pending" && (
                  <Spinner className="mr-1 h-3.5 w-3.5" />
                )}
                {talentPoolAction.state === "idle" && "Save"}
                {talentPoolAction.state === "pending" && "Adding…"}
                {talentPoolAction.state === "added" && "Saved"}
                {talentPoolAction.state === "skipped" && (talentPoolAction.skipReason ?? "Skipped")}
              </Button>
            )}
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Kbd>J</Kbd>/<Kbd>K</Kbd> browse
          </span>
          <span className="flex items-center gap-1">
            <Kbd>S</Kbd> save
          </span>
          <span className="flex items-center gap-1">
            <Kbd>P</Kbd> pass
          </span>
          <span className="flex items-center gap-1">
            <Kbd>I</Kbd> request intro
          </span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="rounded border border-border bg-secondary px-1 py-0.5 font-mono text-[10px] font-semibold text-foreground">
      {children}
    </kbd>
  );
}
