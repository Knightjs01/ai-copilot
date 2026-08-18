"use client";

import { CheckCircle2, ThumbsDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { CareerEntryInput } from "@/lib/types";

interface AnonymisedCvDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  headline: string;
  seniority: string;
  summary: string;
  skills: string[];
  industries: string[];
  careerEntries: CareerEntryInput[];
  // Approve = "this looks right", equivalent to ticking the review checkbox below and closing.
  // Decline & Edit = un-tick the checkbox (if set) and jump back to the Professional Profile
  // step — the checkbox stays the one real source of truth for approval, this dialog is just a
  // richer, focused way to reach the same decision.
  onApprove: () => void;
  onDeclineAndEdit: () => void;
}

export function AnonymisedCvDialog({
  open,
  onOpenChange,
  headline,
  seniority,
  summary,
  skills,
  industries,
  careerEntries,
  onApprove,
  onDeclineAndEdit,
}: AnonymisedCvDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Your anonymised CV</DialogTitle>
          <DialogDescription>
            Exactly what a company sees after you apply — your real name and employer names never
            appear here.
          </DialogDescription>
        </DialogHeader>

        <div className="flex max-h-[55vh] flex-col gap-5 overflow-y-auto rounded-xl border border-border bg-background p-5">
          <div className="flex flex-col gap-1">
            <p className="text-lg font-semibold text-foreground">{headline || "Untitled role"}</p>
            {seniority && <p className="text-sm text-muted-foreground">{seniority}</p>}
          </div>

          {summary && <p className="text-sm text-foreground">{summary}</p>}

          {skills.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {skills.map((skill) => (
                  <Badge key={skill} variant="neutral">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {industries.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Industries
              </p>
              <div className="flex flex-wrap gap-1.5">
                {industries.map((industry) => (
                  <Badge key={industry} variant="neutral">
                    {industry}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {careerEntries.length > 0 && (
            <div className="flex flex-col gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Career history
              </p>
              {careerEntries.map((entry, index) => (
                <div key={index} className="flex flex-col gap-1 rounded-lg bg-card p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-foreground">
                      {entry.title || "Untitled role"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {entry.company_name_anonymized || "Anonymized employer"}
                    </p>
                  </div>
                  {entry.responsibilities && (
                    <p className="text-xs text-muted-foreground">{entry.responsibilities}</p>
                  )}
                  {(entry.achievements ?? []).length > 0 && (
                    <ul className="mt-1 list-disc pl-4 text-xs text-muted-foreground">
                      {(entry.achievements ?? []).map((achievement) => (
                        <li key={achievement}>{achievement}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              onDeclineAndEdit();
              onOpenChange(false);
            }}
          >
            <ThumbsDown className="h-4 w-4" /> Decline & edit
          </Button>
          <Button
            type="button"
            variant="brand"
            onClick={() => {
              onApprove();
              onOpenChange(false);
            }}
          >
            <CheckCircle2 className="h-4 w-4" /> Looks good
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
