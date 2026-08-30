"use client";

import { RefreshCw } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { RediscoveryCandidateCard } from "@/components/candidate-search/rediscovery-candidate-card";
import { Spinner } from "@/components/ui/spinner";
import { useRediscoveryCandidates } from "@/lib/queries/candidate-activity";

export default function RediscoveryPage() {
  const { data: candidates, isLoading } = useRediscoveryCandidates();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-foreground">
          <RefreshCw className="h-5 w-5 text-brand" />
          Rediscovery
        </h1>
        <p className="text-sm text-muted-foreground">
          Candidates you passed on whose Passport has materially changed since — worth a second
          look.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && candidates?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              No passed candidates have materially updated their Passport yet.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && candidates && candidates.length > 0 && (
        <div className="flex flex-col gap-3">
          {candidates.map((candidate) => (
            <RediscoveryCandidateCard key={candidate.callsign} candidate={candidate} />
          ))}
        </div>
      )}
    </div>
  );
}
