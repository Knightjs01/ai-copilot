"use client";

import * as React from "react";
import { UserPlus } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
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
import { Spinner } from "@/components/ui/spinner";
import { ApiError } from "@/lib/api-client";
import { useAddFromTalentPool } from "@/lib/queries/shadow-jobs";
import { useEligibleTalentPoolForProject } from "@/lib/queries/talent-pool";

function EligibleCandidateRow({
  candidate,
  shadowJobId,
}: {
  candidate: { callsign: string; headline: string | null; seniority: string | null; source_role_title: string };
  shadowJobId: string;
}) {
  const [error, setError] = React.useState<string | null>(null);
  const [added, setAdded] = React.useState(false);
  const addFromTalentPool = useAddFromTalentPool(shadowJobId);

  const handleAdd = async () => {
    setError(null);
    try {
      await addFromTalentPool.mutateAsync(candidate.callsign);
      setAdded(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't add this candidate. Try again.");
    }
  };

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-border p-3">
      <div className="flex min-w-0 items-center gap-3">
        <Avatar name={candidate.callsign} className="h-8 w-8 shrink-0 text-xs" />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-foreground">{candidate.callsign}</p>
          <p className="truncate text-xs text-muted-foreground">
            {[candidate.headline, candidate.seniority].filter(Boolean).join(" · ") || "—"}
          </p>
          {error && <p className="text-xs font-medium text-danger">{error}</p>}
        </div>
      </div>
      {added ? (
        <Badge variant="success" className="shrink-0">
          Added
        </Badge>
      ) : (
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={handleAdd}
          disabled={addFromTalentPool.isPending}
          className="shrink-0"
        >
          {addFromTalentPool.isPending ? "Adding…" : "Add to pipeline"}
        </Button>
      )}
    </div>
  );
}

export function AddExistingCandidateDialog({
  projectId,
  shadowJobId,
}: {
  projectId: string;
  shadowJobId: string | undefined;
}) {
  const [open, setOpen] = React.useState(false);
  const { data: eligible, isLoading } = useEligibleTalentPoolForProject(
    open ? projectId : undefined
  );

  if (!shadowJobId) {
    return (
      <Button type="button" variant="secondary" disabled title="Post this role to Shadow first">
        <UserPlus className="h-3.5 w-3.5" />
        Add existing candidate
      </Button>
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="secondary">
          <UserPlus className="h-3.5 w-3.5" />
          Add existing candidate
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add an existing candidate</DialogTitle>
          <DialogDescription>
            Only candidates who&apos;ve already granted this company Talent Pool access are shown
            — adding them here creates a real application on their behalf, using their approved
            Passport, and lets them know it happened.
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex justify-center py-8">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </div>
        )}

        {!isLoading && (eligible?.length ?? 0) === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No granted Talent Pool candidates are eligible for this project yet.
          </p>
        )}

        {!isLoading && eligible && eligible.length > 0 && (
          <div className="flex max-h-80 flex-col gap-2 overflow-y-auto">
            {eligible.map((candidate) => (
              <EligibleCandidateRow
                key={candidate.id}
                candidate={candidate}
                shadowJobId={shadowJobId}
              />
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
