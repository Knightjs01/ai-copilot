"use client";

import * as React from "react";
import { ClipboardList, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth-context";
import {
  useGenerateInterviewScorecard,
  useInterviewScorecards,
  useSaveInterviewScorecard,
} from "@/lib/queries/shadow-jobs";
import { useTeam } from "@/lib/queries/team";
import { DIMENSION_RATING_VARIANT, OVERALL_RECOMMENDATION_VARIANT } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";
import type { CompetencyRating, CompetencyScore, OverallRecommendation } from "@/lib/types";

const RATINGS: CompetencyRating[] = ["Strong", "Moderate", "Weak"];
const RECOMMENDATIONS: OverallRecommendation[] = [
  "Strong Hire",
  "Hire",
  "No Hire",
  "Strong No Hire",
];

export function InterviewScorecardDialog({
  jobId,
  applicationId,
  interviewId,
}: {
  jobId: string;
  applicationId: string;
  interviewId: string;
}) {
  const { user } = useAuth();
  const container = useThemeScopeContainer();
  const toast = useToast();
  const { data: team } = useTeam();
  const [open, setOpen] = React.useState(false);
  const [notes, setNotes] = React.useState("");
  const [competencyScores, setCompetencyScores] = React.useState<CompetencyScore[]>([]);
  const [overallRecommendation, setOverallRecommendation] =
    React.useState<OverallRecommendation>("Hire");
  const [hasDraft, setHasDraft] = React.useState(false);

  const generate = useGenerateInterviewScorecard(jobId, applicationId, interviewId);
  const save = useSaveInterviewScorecard(jobId, applicationId, interviewId);
  const { data: scorecards } = useInterviewScorecards(
    open ? jobId : undefined,
    open ? applicationId : undefined,
    open ? interviewId : undefined
  );

  const myScorecard = scorecards?.find((s) => s.submitted_by_user_id === user?.id);
  const otherScorecards = scorecards?.filter((s) => s.submitted_by_user_id !== user?.id) ?? [];

  React.useEffect(() => {
    if (myScorecard && !hasDraft) {
      setNotes(myScorecard.notes);
      setCompetencyScores(myScorecard.competency_scores);
      setOverallRecommendation(myScorecard.overall_recommendation);
      setHasDraft(true);
    }
    // Only ever hydrate once per open — after that, edits are the user's own, not overwritten by
    // a background refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [myScorecard]);

  const handleGenerate = () => {
    if (!notes.trim()) return;
    generate.mutate(
      { notes },
      {
        onSuccess: (draft) => {
          setCompetencyScores(draft.competency_scores);
          setOverallRecommendation(draft.overall_recommendation);
          setHasDraft(true);
        },
        onError: () => toast({ title: "Couldn't generate a scorecard", variant: "danger" }),
      }
    );
  };

  const handleSave = () => {
    save.mutate(
      { notes, competency_scores: competencyScores, overall_recommendation: overallRecommendation },
      {
        onSuccess: () => {
          toast({ title: "Scorecard saved", variant: "success" });
          setOpen(false);
        },
        onError: () => toast({ title: "Couldn't save the scorecard", variant: "danger" }),
      }
    );
  };

  const updateCompetency = (index: number, patch: Partial<CompetencyScore>) => {
    setCompetencyScores((current) =>
      current.map((c, i) => (i === index ? { ...c, ...patch } : c))
    );
  };

  const memberName = (userId: string) =>
    team?.find((m) => m.id === userId)?.full_name ?? "A teammate";

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button
          type="button"
          className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-brand"
          aria-label="Interview scorecard"
        >
          <ClipboardList className="h-4 w-4" />
        </button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Interview scorecard</DialogTitle>
          <DialogDescription>
            Type up your notes and let Phantom draft competency scores grounded in what you
            actually wrote — review and edit before saving.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <Field label="Your notes" htmlFor="scorecardNotes">
            <Textarea
              id="scorecardNotes"
              rows={5}
              placeholder="What did you observe? How did they answer, what stood out..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </Field>

          <div className="flex justify-end">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleGenerate}
              disabled={!notes.trim() || generate.isPending}
            >
              <Sparkles className="h-3.5 w-3.5" />
              {generate.isPending ? "Generating…" : "Generate scorecard"}
            </Button>
          </div>

          {hasDraft && (
            <>
              <div className="flex flex-col gap-3">
                {competencyScores.map((score, i) => (
                  <div
                    key={i}
                    className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3"
                  >
                    <div className="flex items-center gap-2">
                      <Input
                        value={score.competency}
                        onChange={(e) => updateCompetency(i, { competency: e.target.value })}
                        className="flex-1"
                      />
                      <Select
                        value={score.rating}
                        onValueChange={(value) =>
                          updateCompetency(i, { rating: value as CompetencyRating })
                        }
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent container={container}>
                          {RATINGS.map((r) => (
                            <SelectItem key={r} value={r}>
                              {r}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Textarea
                      value={score.evidence}
                      onChange={(e) => updateCompetency(i, { evidence: e.target.value })}
                      rows={2}
                      className="text-sm"
                    />
                  </div>
                ))}
              </div>

              <Field label="Overall recommendation">
                <Select
                  value={overallRecommendation}
                  onValueChange={(value) =>
                    setOverallRecommendation(value as OverallRecommendation)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent container={container}>
                    {RECOMMENDATIONS.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>

              <div className="flex justify-end">
                <Button type="button" variant="brand" onClick={handleSave} disabled={save.isPending}>
                  {save.isPending ? "Saving…" : myScorecard ? "Update scorecard" : "Save scorecard"}
                </Button>
              </div>
            </>
          )}

          {otherScorecards.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Other submitted scorecards
              </h4>
              {otherScorecards.map((s) => (
                <div key={s.id} className="rounded-xl border border-border bg-card p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-foreground">
                      {memberName(s.submitted_by_user_id)}
                    </p>
                    <Badge variant={OVERALL_RECOMMENDATION_VARIANT[s.overall_recommendation]}>
                      {s.overall_recommendation}
                    </Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {s.competency_scores.map((cs, i) => (
                      <Badge key={i} variant={DIMENSION_RATING_VARIANT[cs.rating]}>
                        {cs.competency}: {cs.rating}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
