"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { AiRecommendation, RediscoveryCandidate, TimelineEntry } from "@/lib/types";

// One candidate's full real history with this company, merged across every event source that
// already exists (applications, reveal requests, Talent Pool grants, passes, introductions,
// conversations) -- see backend candidate_activity/service.py::list_candidate_timeline.
export function useCandidateTimeline(callsign: string | undefined, options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["candidate-activity", "timeline", callsign],
    queryFn: () =>
      apiClient.get<TimelineEntry[]>(`/candidate-activity/mine/candidates/${callsign}/timeline`),
    enabled: enabled && !!callsign,
  });
}

// Company-wide recent activity across every candidate -- powers the Home dashboard's "Recent
// Shadow Activity" card.
export function useRecentActivity(limit = 15) {
  return useQuery({
    queryKey: ["candidate-activity", "recent", limit],
    queryFn: () => apiClient.get<TimelineEntry[]>(`/candidate-activity/mine/recent?limit=${limit}`),
  });
}

// Candidates this company passed on whose Passport has materially changed since -- see backend
// candidate_activity/diffing.py.
export function useRediscoveryCandidates() {
  return useQuery({
    queryKey: ["candidate-activity", "rediscovery"],
    queryFn: () => apiClient.get<RediscoveryCandidate[]>("/candidate-activity/mine/rediscovery"),
  });
}

// One real, evidence-backed suggestion from the exact same matching engine search-candidates
// uses -- deliberately not fetched automatically (enabled: false) so it never runs an LLM
// scoring pass unless the dashboard card that shows it is actually rendered.
export function useAiRecommendation(options?: { enabled?: boolean }) {
  const { enabled = false } = options ?? {};
  return useQuery({
    queryKey: ["candidate-activity", "recommendation"],
    queryFn: () => apiClient.get<AiRecommendation | null>("/candidate-activity/mine/recommendation"),
    enabled,
  });
}
