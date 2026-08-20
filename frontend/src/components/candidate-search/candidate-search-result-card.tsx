"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { MATCH_TIER_VARIANT } from "@/lib/status-display";
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

export function CandidateSearchResultCard({ result }: { result: CandidateSearchResult }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h3 className="text-base font-semibold text-foreground">{result.callsign}</h3>
            {result.headline && (
              <p className="text-sm text-muted-foreground">{result.headline}</p>
            )}
          </div>
          <Badge variant={MATCH_TIER_VARIANT[result.match_tier]}>{result.match_tier}</Badge>
        </div>

        {result.summary && <p className="text-sm text-foreground">{result.summary}</p>}

        {result.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {result.skills.map((skill) => (
              <Badge key={skill} variant="outline">
                {skill}
              </Badge>
            ))}
          </div>
        )}

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
      </CardContent>
    </Card>
  );
}
