"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { MATCH_TIER_VARIANT } from "@/lib/status-display";
import { useAiRecommendation } from "@/lib/queries/candidate-activity";

// Reuses the real search-candidates matching engine for the company's most recently published
// job -- fetched only once this card actually mounts (enabled: true here, not on page load), so
// it never runs an LLM scoring pass for a company that never looks at the dashboard.
export function AiRecommendationCard() {
  const { data: recommendation, isLoading } = useAiRecommendation({ enabled: true });

  if (!isLoading && !recommendation) return null;

  return (
    <div>
      <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold tracking-tight text-foreground">
        <Sparkles className="h-4 w-4 text-brand" />
        AI Recommendation
      </h2>
      <Card>
        {isLoading ? (
          <CardContent className="flex justify-center py-10">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        ) : recommendation ? (
          <CardContent className="flex flex-col gap-3 py-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-foreground">{recommendation.callsign}</p>
                <p className="text-xs text-muted-foreground">
                  For {recommendation.job_title}
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <Badge variant={MATCH_TIER_VARIANT[recommendation.match_tier]}>
                  {recommendation.match_tier}
                </Badge>
                <span className="text-xs font-medium text-muted-foreground">
                  {recommendation.match_score}% match
                </span>
              </div>
            </div>
            <p className="text-sm text-foreground">{recommendation.match_summary}</p>
            <Button asChild variant="secondary" size="sm" className="self-start">
              <Link href={`/search-candidates?job=${recommendation.job_id}`}>
                View candidate
              </Link>
            </Button>
          </CardContent>
        ) : null}
      </Card>
    </div>
  );
}
