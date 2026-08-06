"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useCandidates } from "@/lib/queries/candidates";
import {
  CANDIDATE_SOURCE_LABEL,
  CANDIDATE_STATUS_LABEL,
  PRESCREEN_OUTCOME_LABEL,
  PRESCREEN_OUTCOME_VARIANT,
} from "@/lib/status-display";

export function CandidatesListTab({ projectId }: { projectId: string }) {
  const { data: candidates, isLoading } = useCandidates(projectId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight text-foreground">All candidates</h2>
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-3">Callsign</th>
                  <th className="px-4 py-3">Candidate ID</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Pre-screen outcome</th>
                  <th className="px-4 py-3">Expected salary</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((candidate) => (
                  <tr key={candidate.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3">
                      <Link
                        href={`/projects/${projectId}/candidates/${candidate.id}`}
                        className="font-medium text-foreground hover:underline"
                      >
                        {candidate.callsign}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{candidate.candidate_ref}</td>
                    <td className="px-4 py-3">
                      <Badge variant="neutral">{CANDIDATE_STATUS_LABEL[candidate.status]}</Badge>
                    </td>
                    <td className="px-4 py-3 text-foreground">
                      {CANDIDATE_SOURCE_LABEL[candidate.source]}
                      {candidate.source === "agency" && candidate.agency_name
                        ? ` (${candidate.agency_name})`
                        : ""}
                    </td>
                    <td className="px-4 py-3">
                      {candidate.prescreen_outcome ? (
                        <Badge variant={PRESCREEN_OUTCOME_VARIANT[candidate.prescreen_outcome]}>
                          {PRESCREEN_OUTCOME_LABEL[candidate.prescreen_outcome]}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-foreground">
                      {candidate.expected_salary != null
                        ? `£${candidate.expected_salary.toLocaleString()}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
