"use client";

import * as React from "react";
import type { ReactNode } from "react";
import { AlertTriangle, Check, CheckCircle2, MessageCircle, Plus, X } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  MATCH_TIER_VARIANT,
  RELATIONSHIP_STATUS_LABEL,
  RELATIONSHIP_STATUS_VARIANT,
} from "@/lib/status-display";
import { cn } from "@/lib/utils";
import type { CandidateSearchResult } from "@/lib/types";

export type QuickTalentPoolState = "idle" | "pending" | "added" | "skipped";

export interface QuickTalentPoolAction {
  state: QuickTalentPoolState;
  skipReason?: string;
  onAdd: () => void;
}

function ToneLine({
  label,
  text,
  tone,
}: {
  label: string;
  text: string;
  tone: "positive" | "caution";
}) {
  const Icon = tone === "positive" ? CheckCircle2 : AlertTriangle;
  return (
    <p className="flex items-start gap-1.5 text-xs text-foreground">
      <Icon
        className={cn(
          "mt-0.5 h-3.5 w-3.5 shrink-0",
          tone === "positive" ? "text-success" : "text-warning"
        )}
      />
      <span>
        <span className="font-medium text-muted-foreground">{label}: </span>
        {text}
      </span>
    </p>
  );
}

export function CandidateSearchResultCard({
  result,
  contextLine,
  selected,
  onToggleSelected,
  talentPoolAction,
  onOpenQuickView,
  onPass,
  onRequestIntroduction,
}: {
  result: CandidateSearchResult;
  contextLine?: ReactNode;
  // Optional — omitted entirely on pages that don't wire up a selection/bulk-action toolbar.
  selected?: boolean;
  onToggleSelected?: () => void;
  // Optional per-card quick-add to Talent Pool — omitted on pages where it doesn't apply (e.g.
  // Talent Pool's own "find matches" section, where the candidate is already granted).
  talentPoolAction?: QuickTalentPoolAction;
  // Opens the Quick View dialog for this candidate — omitted where there's no result set to page
  // through (e.g. a single-applicant view).
  onOpenQuickView?: () => void;
  // Opens the Pass confirmation for this candidate — omitted where passing doesn't apply.
  onPass?: () => void;
  // Opens the Request Introduction dialog — omitted where requesting doesn't apply.
  onRequestIntroduction?: () => void;
}) {
  const topStrength = result.strengths[0];
  const topGap = result.gaps[0];
  const evidence = [
    result.career_entries[0]
      ? `${result.career_entries[0].title} · ${result.career_entries[0].company_name_anonymized}`
      : null,
    ...result.skills.slice(0, 3),
  ].filter((v): v is string => !!v);

  return (
    <Card className={cn(selected && "border-brand/50 bg-brand/5")}>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex items-start justify-between gap-4">
          <button
            type="button"
            onClick={onOpenQuickView}
            disabled={!onOpenQuickView}
            className={cn(
              "flex min-w-0 flex-1 items-start gap-3 text-left",
              onOpenQuickView && "cursor-pointer"
            )}
          >
            {onToggleSelected && (
              <input
                type="checkbox"
                checked={!!selected}
                onChange={(e) => {
                  e.stopPropagation();
                  onToggleSelected();
                }}
                onClick={(e) => e.stopPropagation()}
                className="mt-1 h-4 w-4 shrink-0 accent-brand"
                aria-label={`Select ${result.callsign}`}
              />
            )}
            <Avatar name={result.callsign} className="mt-0.5 h-8 w-8 shrink-0 text-xs" />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="truncate text-sm font-semibold text-foreground">
                  {result.callsign}
                </h3>
                {result.relationship_status !== "new" && (
                  <Badge variant={RELATIONSHIP_STATUS_VARIANT[result.relationship_status]}>
                    {RELATIONSHIP_STATUS_LABEL[result.relationship_status]}
                  </Badge>
                )}
              </div>
              {result.headline && (
                <p className="truncate text-xs text-muted-foreground">{result.headline}</p>
              )}
              <p className="truncate text-xs text-muted-foreground">
                {[
                  result.seniority,
                  result.years_experience != null ? `${result.years_experience} yrs` : null,
                  result.location,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              {contextLine && <p className="text-xs text-muted-foreground">{contextLine}</p>}
            </div>
          </button>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <Badge variant={MATCH_TIER_VARIANT[result.match_tier]}>{result.match_tier}</Badge>
            <span className="text-xs font-medium text-muted-foreground">
              {result.match_score}% match
            </span>
          </div>
        </div>

        {evidence.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pl-11">
            {evidence.map((item) => (
              <Badge key={item} variant="outline" className="text-[10px]">
                {item}
              </Badge>
            ))}
          </div>
        )}

        {(topStrength || topGap) && (
          <div className="flex flex-col gap-1 pl-11">
            {topStrength && <ToneLine label="Match insight" text={topStrength} tone="positive" />}
            {topGap && <ToneLine label="Potential gap" text={topGap} tone="caution" />}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2 pl-11">
          {onRequestIntroduction && (
            <button
              type="button"
              onClick={onRequestIntroduction}
              disabled={result.relationship_status === "introduction_pending"}
              className="flex items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-xs font-medium text-brand-foreground transition-colors hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
            >
              <MessageCircle className="h-3 w-3" />
              {result.relationship_status === "introduction_pending"
                ? "Introduction requested"
                : "Request introduction"}
            </button>
          )}
          {talentPoolAction && (
            <>
              {talentPoolAction.state === "idle" && (
                <button
                  type="button"
                  onClick={talentPoolAction.onAdd}
                  className="flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-brand hover:text-brand"
                >
                  <Plus className="h-3 w-3" />
                  Save
                </button>
              )}
              {talentPoolAction.state === "pending" && (
                <span className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-muted-foreground">
                  <Spinner className="h-3 w-3" />
                  Adding…
                </span>
              )}
              {talentPoolAction.state === "added" && (
                <span className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-success">
                  <Check className="h-3 w-3" />
                  Saved
                </span>
              )}
              {talentPoolAction.state === "skipped" && (
                <span className="px-2.5 py-1 text-xs font-medium text-muted-foreground">
                  {talentPoolAction.skipReason ?? "Skipped"}
                </span>
              )}
            </>
          )}
          {onPass && (
            <button
              type="button"
              onClick={onPass}
              className="flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-danger hover:text-danger"
            >
              <X className="h-3 w-3" />
              Pass
            </button>
          )}
          {onOpenQuickView && (
            <button
              type="button"
              onClick={onOpenQuickView}
              className="ml-auto text-xs font-medium text-brand hover:underline"
            >
              View full passport
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
