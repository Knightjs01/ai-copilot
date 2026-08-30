"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useRecentActivity } from "@/lib/queries/candidate-activity";

function formatOccurredAt(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// Real, chronological Shadow activity across every candidate at this company -- distinct from
// "Today's Priorities" above it, which only ever lists outstanding gaps to close, never a
// history of what's happened.
export function RecentActivityCard() {
  const { data: entries, isLoading } = useRecentActivity(10);

  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold tracking-tight text-foreground">
        Recent Shadow Activity
      </h2>
      <Card>
        {isLoading ? (
          <CardContent className="flex justify-center py-10">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        ) : entries && entries.length > 0 ? (
          <CardContent className="flex flex-col gap-3 py-3">
            {entries.map((entry, i) => (
              <div key={i} className="flex items-start justify-between gap-3 text-sm">
                <p className="text-foreground">{entry.description}</p>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatOccurredAt(entry.occurred_at)}
                </span>
              </div>
            ))}
          </CardContent>
        ) : (
          <CardContent className="py-10 text-center">
            <p className="text-sm text-muted-foreground">No recent Shadow activity yet.</p>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
