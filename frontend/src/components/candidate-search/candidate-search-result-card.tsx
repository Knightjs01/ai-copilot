"use client";

import * as React from "react";
import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { MATCH_TIER_VARIANT } from "@/lib/status-display";
import { cn } from "@/lib/utils";
import type { CandidateSearchResult } from "@/lib/types";

function ToneList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "caution";
}) {
  if (items.length === 0) return null;
  const Icon = tone === "positive" ? CheckCircle2 : AlertTriangle;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <ul
        className={
          tone === "positive"
            ? "flex flex-col gap-1.5 rounded-xl border border-success/20 bg-success/5 p-3"
            : "flex flex-col gap-1.5 rounded-xl border border-warning/20 bg-warning/5 p-3"
        }
      >
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-foreground">
            <Icon
              className={
                tone === "positive"
                  ? "mt-0.5 h-3.5 w-3.5 shrink-0 text-success"
                  : "mt-0.5 h-3.5 w-3.5 shrink-0 text-warning"
              }
            />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CandidateSearchResultCard({
  result,
  contextLine,
  selected,
  onToggleSelected,
}: {
  result: CandidateSearchResult;
  contextLine?: ReactNode;
  // Optional — omitted entirely on pages that don't wire up a selection/bulk-action toolbar.
  selected?: boolean;
  onToggleSelected?: () => void;
}) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <Card className={cn(selected && "border-brand/50 bg-brand/5")}>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            {onToggleSelected && (
              <input
                type="checkbox"
                checked={!!selected}
                onChange={onToggleSelected}
                className="mt-1 h-4 w-4 shrink-0 accent-brand"
                aria-label={`Select ${result.callsign}`}
              />
            )}
            <Avatar name={result.callsign} className="mt-0.5 h-8 w-8 shrink-0 text-xs" />
            <div className="min-w-0">
              <h3 className="truncate text-sm font-semibold text-foreground">
                {result.callsign}
              </h3>
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
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <Badge variant={MATCH_TIER_VARIANT[result.match_tier]}>{result.match_tier}</Badge>
            <span className="text-xs font-medium text-muted-foreground">
              {result.match_score}% match
            </span>
          </div>
        </div>

        {result.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pl-11">
            {result.skills.slice(0, 4).map((skill) => (
              <Badge key={skill} variant="outline" className="text-[10px]">
                {skill}
              </Badge>
            ))}
            {result.skills.length > 4 && (
              <span className="text-[10px] text-muted-foreground">
                +{result.skills.length - 4} more
              </span>
            )}
          </div>
        )}

        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="ml-11 flex w-fit items-center gap-1 text-xs font-medium text-brand hover:underline"
        >
          {expanded ? (
            <>
              Hide details <ChevronUp className="h-3 w-3" />
            </>
          ) : (
            <>
              Show details <ChevronDown className="h-3 w-3" />
            </>
          )}
        </button>

        {expanded && (
          <div className="flex flex-col gap-3 pl-11">
            {result.summary && <p className="text-sm text-foreground">{result.summary}</p>}

            {result.career_entries.length > 0 && (
              <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                {result.career_entries.map((entry, i) => (
                  <p key={i}>
                    {entry.title} · {entry.company_name_anonymized}
                    {entry.is_current ? " (current)" : ""}
                  </p>
                ))}
              </div>
            )}

            <p className="text-sm text-foreground">{result.match_summary}</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <ToneList title="Strengths" items={result.strengths} tone="positive" />
              <ToneList title="Gaps" items={result.gaps} tone="caution" />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
