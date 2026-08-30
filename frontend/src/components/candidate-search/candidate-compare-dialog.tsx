"use client";

import * as React from "react";
import { AlertTriangle, CheckCircle2, MessageCircle, Plus, X } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import type { QuickTalentPoolAction } from "@/components/candidate-search/candidate-search-result-card";
import {
  DIMENSION_RATING_VARIANT,
  MATCH_TIER_VARIANT,
  RELATIONSHIP_STATUS_LABEL,
  RELATIONSHIP_STATUS_VARIANT,
} from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { cn } from "@/lib/utils";
import type { CandidateSearchResult } from "@/lib/types";

const PLAIN_FACT_ROWS: {
  label: string;
  render: (result: CandidateSearchResult) => React.ReactNode;
}[] = [
  { label: "Seniority", render: (r) => r.seniority ?? "—" },
  {
    label: "Experience",
    render: (r) => (r.years_experience != null ? `${r.years_experience} yrs` : "—"),
  },
  { label: "Location", render: (r) => r.location ?? "—" },
  { label: "Remote preference", render: (r) => r.remote_preference ?? "—" },
];

export function CandidateCompareDialog({
  open,
  onOpenChange,
  results,
  totalSelected,
  talentPoolActionFor,
  onPass,
  onRequestIntroduction,
  onRemove,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  results: CandidateSearchResult[];
  totalSelected: number;
  talentPoolActionFor: (callsign: string) => QuickTalentPoolAction;
  onPass: (callsign: string) => void;
  onRequestIntroduction: (callsign: string) => void;
  onRemove: (callsign: string) => void;
}) {
  const container = useThemeScopeContainer();

  const dimensionNames = React.useMemo(() => {
    const seen = new Set<string>();
    const names: string[] = [];
    for (const result of results) {
      for (const dim of result.dimension_breakdown) {
        if (!seen.has(dim.dimension)) {
          seen.add(dim.dimension);
          names.push(dim.dimension);
        }
      }
    }
    return names;
  }, [results]);

  if (results.length === 0) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container} className="max-w-5xl">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-semibold text-foreground">
            Compare {results.length} candidate{results.length === 1 ? "" : "s"}
          </h2>
          {totalSelected > results.length && (
            <p className="text-xs text-muted-foreground">
              Comparing the top {results.length} of {totalSelected} selected.
            </p>
          )}
        </div>

        <div className="mt-4 max-h-[70vh] overflow-y-auto pr-1">
          <div className="overflow-x-auto rounded-2xl border border-border">
            <table className="w-full min-w-[560px] border-collapse bg-card text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/20">
                  <th className="sticky left-0 z-10 bg-secondary/20 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Candidate
                  </th>
                  {results.map((result) => (
                    <th key={result.callsign} className="min-w-[180px] px-4 py-3 text-left">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <Avatar name={result.callsign} className="h-6 w-6 shrink-0 text-[10px]" />
                          <span className="text-sm font-semibold text-foreground">
                            {result.callsign}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => onRemove(result.callsign)}
                          aria-label={`Remove ${result.callsign} from comparison`}
                          className="text-muted-foreground transition-colors hover:text-foreground"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                        <Badge variant={MATCH_TIER_VARIANT[result.match_tier]}>
                          {result.match_tier}
                        </Badge>
                        <span className="text-[11px] font-medium text-muted-foreground">
                          {result.match_score}% match
                        </span>
                      </div>
                      {result.relationship_status !== "new" && (
                        <Badge
                          variant={RELATIONSHIP_STATUS_VARIANT[result.relationship_status]}
                          className="mt-1.5"
                        >
                          {RELATIONSHIP_STATUS_LABEL[result.relationship_status]}
                        </Badge>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {PLAIN_FACT_ROWS.map((row) => (
                  <tr key={row.label} className="border-b border-border">
                    <td className="sticky left-0 z-10 bg-card px-4 py-2.5 text-xs font-medium text-foreground">
                      {row.label}
                    </td>
                    {results.map((result) => (
                      <td key={result.callsign} className="px-4 py-2.5 text-xs text-foreground">
                        {row.render(result)}
                      </td>
                    ))}
                  </tr>
                ))}

                <tr className="border-b border-border bg-secondary/30">
                  <td
                    colSpan={results.length + 1}
                    className="sticky left-0 px-4 py-2 text-xs font-semibold text-foreground"
                  >
                    Match breakdown
                  </td>
                </tr>
                {dimensionNames.map((dimension) => (
                  <tr key={dimension} className="border-b border-border last:border-b-0">
                    <td className="sticky left-0 z-10 bg-card px-4 py-2.5 text-xs font-medium text-foreground">
                      {dimension}
                    </td>
                    {results.map((result) => {
                      const dim = result.dimension_breakdown.find(
                        (d) => d.dimension === dimension
                      );
                      return (
                        <td key={result.callsign} className="px-4 py-2.5">
                          {dim ? (
                            <Badge variant={DIMENSION_RATING_VARIANT[dim.rating]}>
                              {dim.rating}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}

                <tr>
                  <td className="sticky left-0 z-10 bg-card px-4 py-2.5 text-xs font-medium text-foreground">
                    Skills
                  </td>
                  {results.map((result) => (
                    <td key={result.callsign} className="px-4 py-2.5">
                      <div className="flex flex-wrap gap-1">
                        {result.skills.slice(0, 5).map((skill) => (
                          <Badge key={skill} variant="outline" className="text-[10px]">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          <div
            className="mt-4 grid gap-3"
            style={{ gridTemplateColumns: `repeat(${results.length}, minmax(0, 1fr))` }}
          >
            {results.map((result) => {
              const topStrength = result.strengths[0];
              const topGap = result.gaps[0];
              const talentPoolAction = talentPoolActionFor(result.callsign);
              return (
                <div
                  key={result.callsign}
                  className="flex flex-col gap-2 rounded-xl border border-border p-3"
                >
                  {topStrength && (
                    <p className="flex items-start gap-1.5 text-xs text-foreground">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                      <span>{topStrength}</span>
                    </p>
                  )}
                  {topGap && (
                    <p className="flex items-start gap-1.5 text-xs text-foreground">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
                      <span>{topGap}</span>
                    </p>
                  )}
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => onPass(result.callsign)}
                      className="flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-danger hover:text-danger"
                    >
                      <X className="h-3 w-3" />
                      Pass
                    </button>
                    <button
                      type="button"
                      onClick={() => onRequestIntroduction(result.callsign)}
                      disabled={result.relationship_status === "introduction_pending"}
                      className="flex items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-xs font-medium text-brand-foreground transition-colors hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
                    >
                      <MessageCircle className="h-3 w-3" />
                      {result.relationship_status === "introduction_pending"
                        ? "Requested"
                        : "Introduce"}
                    </button>
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
                      <span className={cn("px-2.5 py-1 text-xs font-medium text-success")}>
                        Saved
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
