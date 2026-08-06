"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { CandidateInfoCard } from "@/components/candidate/candidate-info-card";
import { HandoffRecommendationsCard } from "@/components/candidate/handoff-recommendations-card";
import { IntelligencePackCard } from "@/components/candidate/intelligence-pack-card";
import { PrescreenAssessmentCard } from "@/components/candidate/prescreen-assessment-card";
import { PrescreenOutcomeCard } from "@/components/candidate/prescreen-outcome-card";
import { ResumeCard } from "@/components/candidate/resume-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Tabs } from "@/components/ui/tabs";
import { useCandidate } from "@/lib/queries/candidates";
import { CANDIDATE_STATUS_LABEL } from "@/lib/status-display";

type CandidateTab = "overview" | "info";

const TAB_OPTIONS: { value: CandidateTab; label: string }[] = [
  { value: "overview", label: "Overview" },
  { value: "info", label: "Candidate Info" },
];

export default function CandidateDetailPage() {
  const params = useParams<{ id: string; candidateId: string }>();
  const { data: candidate, isLoading } = useCandidate(params.candidateId);
  const [activeTab, setActiveTab] = React.useState<CandidateTab>("overview");

  if (isLoading || !candidate) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Link
          href={`/projects/${params.id}`}
          className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to project
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {candidate.full_name}
          </h1>
          <Badge variant="neutral">{CANDIDATE_STATUS_LABEL[candidate.status]}</Badge>
        </div>
        {candidate.email && (
          <p className="mt-1 text-sm text-muted-foreground">{candidate.email}</p>
        )}
      </div>

      <Tabs options={TAB_OPTIONS} value={activeTab} onChange={setActiveTab} />

      {activeTab === "overview" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ResumeCard candidate={candidate} />
          <IntelligencePackCard candidateId={candidate.id} projectId={candidate.project_id} />
          <PrescreenAssessmentCard candidate={candidate} />
          <PrescreenOutcomeCard candidate={candidate} />
          <HandoffRecommendationsCard candidate={candidate} />
        </div>
      )}

      {activeTab === "info" && <CandidateInfoCard candidate={candidate} />}
    </div>
  );
}
