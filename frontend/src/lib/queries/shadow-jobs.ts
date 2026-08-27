"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type {
  AuditEntry,
  CompanyInterviewSummary,
  CompetencyScore,
  Interview,
  InterviewScorecard,
  InterviewScorecardDraft,
  JobIntelligence,
  MessageThread,
  OverallRecommendation,
  ShadowApplication,
  ShadowJob,
  ShadowJobBoardListing,
  ShadowJobCreateInput,
  ShadowJobUpdateInput,
  ShadowPipelineStage,
  ShadowProfile,
  ShadowProfileCompanyWide,
} from "@/lib/types";

// --- Company side (company auth, apiClient) --------------------------------------------------

export function useMyShadowJobs() {
  return useQuery({
    queryKey: ["shadow-jobs", "mine"],
    queryFn: () => apiClient.get<ShadowJob[]>("/shadow-jobs/mine"),
  });
}

export function useMyShadowJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "mine", jobId],
    queryFn: () => apiClient.get<ShadowJob>(`/shadow-jobs/mine/${jobId}`),
    enabled: !!jobId,
  });
}

export function useCreateShadowJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ShadowJobCreateInput) => apiClient.post<ShadowJob>("/shadow-jobs", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function useUpdateShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ShadowJobUpdateInput) =>
      apiClient.patch<ShadowJob>(`/shadow-jobs/mine/${jobId}`, input),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "mine", jobId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function usePublishShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<ShadowJob>(`/shadow-jobs/mine/${jobId}/publish`),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "mine", jobId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function useCloseShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<ShadowJob>(`/shadow-jobs/mine/${jobId}/close`),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "mine", jobId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function useShadowJobApplicants(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "applicants", jobId],
    queryFn: () => apiClient.get<ShadowProfile[]>(`/shadow-jobs/mine/${jobId}/applicants`),
    enabled: !!jobId,
  });
}

// Single-applicant fetch for the dedicated candidate workspace page -- distinct from the
// list-then-filter-client-side approach every other consumer of this data uses today.
export function useApplicant(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "applicants", jobId, applicationId],
    queryFn: () =>
      apiClient.get<ShadowProfile>(`/shadow-jobs/mine/${jobId}/applicants/${applicationId}`),
    enabled: !!jobId && !!applicationId,
  });
}

export function useApplicantActivity(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "applicants", jobId, applicationId, "activity"],
    queryFn: () =>
      apiClient.get<AuditEntry[]>(`/shadow-jobs/mine/${jobId}/applicants/${applicationId}/activity`),
    enabled: !!jobId && !!applicationId,
  });
}

// Company-wide Candidates/Pipeline nav destination -- every Shadow applicant across every job
// for this tenant, mirroring useCompanyInterviews' exact shape.
export function useAllShadowApplicants(options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["shadow-jobs", "applicants", "mine-company"],
    queryFn: () => apiClient.get<ShadowProfileCompanyWide[]>("/shadow-jobs/applicants/mine"),
    enabled,
  });
}

// Recruiter-triggered application for a candidate who's already granted this company Talent Pool
// access -- the consent-gated replacement for manually creating a brand-new Candidate row.
export function useAddFromTalentPool(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (callsign: string) =>
      apiClient.post<ShadowApplication>(
        `/shadow-jobs/mine/${jobId}/applicants/add-from-talent-pool`,
        { callsign }
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
      void queryClient.invalidateQueries({ queryKey: ["talent-pool", "eligible"] });
      void queryClient.invalidateQueries({
        queryKey: ["shadow-jobs", "applicants", "mine-company"],
      });
    },
  });
}

export function useProjectShadowJob(projectId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "project", projectId],
    queryFn: () =>
      fetchOrNull(() => apiClient.get<ShadowJob>(`/projects/${projectId}/shadow-job`)),
    enabled: !!projectId,
  });
}

// The one-time-snapshot publish/re-publish action -- always sends the full current form state,
// never a partial diff, since each call is an explicit "copy this onto Shadow now" moment.
export function usePublishProjectToShadow(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ShadowJobCreateInput) =>
      apiClient.post<ShadowJob>(`/projects/${projectId}/shadow-job`, input),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "project", projectId], data);
    },
  });
}

export function useUpdateApplicantPipelineStage(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      applicationId,
      pipelineStage,
    }: {
      applicationId: string;
      pipelineStage: ShadowPipelineStage;
    }) =>
      apiClient.patch<ShadowProfile>(`/shadow-jobs/mine/${jobId}/applicants/${applicationId}`, {
        pipeline_stage: pipelineStage,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

// Fire-and-forget: the caller marks a card viewed once (e.g. on click, or when its detail
// mounts) — the backend itself is idempotent (mark_viewed is a no-op once viewed_at is set), so
// there's no harm in calling this more than once for the same applicant.
export function useMarkApplicantViewed(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (applicationId: string) =>
      apiClient.post<ShadowProfile>(
        `/shadow-jobs/mine/${jobId}/applicants/${applicationId}/mark-viewed`
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useApplicantMessages(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["messages", "applicant-thread", jobId, applicationId],
    queryFn: () =>
      apiClient.get<MessageThread>(`/messages/mine/${jobId}/applicants/${applicationId}`),
    enabled: !!jobId && !!applicationId,
    refetchInterval: 20000,
  });
}

export function useSendCompanyMessage(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      apiClient.post<MessageThread>(`/messages/mine/${jobId}/applicants/${applicationId}`, {
        body,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["messages", "applicant-thread", jobId, applicationId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

// Company-wide Interviews nav destination -- every interview across every job for this tenant.
export function useCompanyInterviews(options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["interviews", "mine-company"],
    queryFn: () => apiClient.get<CompanyInterviewSummary[]>("/interviews/mine"),
    enabled,
  });
}

export function useApplicantInterviews(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["interviews", "applicant", jobId, applicationId],
    queryFn: () =>
      apiClient.get<Interview[]>(`/interviews/mine/${jobId}/applicants/${applicationId}`),
    enabled: !!jobId && !!applicationId,
  });
}

interface ScheduleInterviewInput {
  scheduled_at: string;
  location?: string | null;
  meeting_link?: string | null;
  interviewer_user_ids?: string[];
}

export function useScheduleInterview(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ScheduleInterviewInput) =>
      apiClient.post<Interview>(`/interviews/mine/${jobId}/applicants/${applicationId}`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useUpdateInterview(jobId: string, applicationId: string, interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ScheduleInterviewInput) =>
      apiClient.patch<Interview>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}`,
        input
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useCancelInterview(jobId: string, applicationId: string, interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<Interview>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/cancel`
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useCompleteInterview(jobId: string, applicationId: string, interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<Interview>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/complete`
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

interface GenerateScorecardInput {
  notes: string;
}

export function useGenerateInterviewScorecard(
  jobId: string,
  applicationId: string,
  interviewId: string
) {
  return useMutation({
    mutationFn: (input: GenerateScorecardInput) =>
      apiClient.post<InterviewScorecardDraft>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/scorecard/generate`,
        input
      ),
  });
}

interface SaveScorecardInput {
  notes: string;
  competency_scores: CompetencyScore[];
  overall_recommendation: OverallRecommendation;
}

export function useSaveInterviewScorecard(
  jobId: string,
  applicationId: string,
  interviewId: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveScorecardInput) =>
      apiClient.put<InterviewScorecard>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/scorecard`,
        input
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "scorecards", jobId, applicationId, interviewId],
      });
      // Saving also marks the interview completed as a side effect.
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
    },
  });
}

export function useInterviewScorecards(
  jobId: string | undefined,
  applicationId: string | undefined,
  interviewId: string | undefined
) {
  return useQuery({
    queryKey: ["interviews", "scorecards", jobId, applicationId, interviewId],
    queryFn: () =>
      apiClient.get<InterviewScorecard[]>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/scorecards`
      ),
    enabled: !!jobId && !!applicationId && !!interviewId,
  });
}

// --- Public job board (no auth required) ------------------------------------------------------

export interface ShadowBoardFilters {
  seniority?: string;
  remote_preference?: string;
  employment_type?: string;
  location?: string;
}

function boardQueryString(filters: ShadowBoardFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function useShadowBoard(filters: ShadowBoardFilters = {}) {
  return useQuery({
    queryKey: ["shadow-jobs", "board", filters],
    queryFn: () =>
      apiClient.get<ShadowJobBoardListing[]>(`/shadow-jobs/board${boardQueryString(filters)}`),
  });
}

export function useShadowBoardJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "board", jobId],
    queryFn: () => apiClient.get<ShadowJobBoardListing>(`/shadow-jobs/board/${jobId}`),
    enabled: !!jobId,
  });
}

export function useJobIntelligence(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "board", jobId, "intelligence"],
    queryFn: () => apiClient.get<JobIntelligence>(`/shadow-jobs/board/${jobId}/intelligence`),
    enabled: !!jobId,
  });
}

// --- Candidate side (candidate auth, candidateApiClient) ---------------------------------------

export function useApplyToShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      candidateApiClient.post<ShadowApplication>(`/shadow-jobs/board/${jobId}/apply`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applications", "me"] });
    },
  });
}

export function useMyApplications() {
  return useQuery({
    queryKey: ["shadow-jobs", "applications", "me"],
    queryFn: () => candidateApiClient.get<ShadowApplication[]>("/shadow-jobs/applications/me"),
  });
}

export function useMyApplication(applicationId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "applications", "me", applicationId],
    queryFn: () =>
      fetchOrNull(() =>
        candidateApiClient.get<ShadowApplication>(`/shadow-jobs/applications/me/${applicationId}`)
      ),
    enabled: !!applicationId,
  });
}

export function useWithdrawApplication(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      candidateApiClient.post<ShadowApplication>(
        `/shadow-jobs/applications/me/${applicationId}/withdraw`
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "applications", "me", applicationId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applications", "me"] });
    },
  });
}
