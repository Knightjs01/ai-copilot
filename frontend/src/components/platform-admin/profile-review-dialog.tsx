"use client";

import * as React from "react";

import { CompanyProfilePreview } from "@/components/company/company-profile-preview";
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
import { Textarea } from "@/components/ui/textarea";
import {
  useAdminProfilePreview,
  useApproveProfileReview,
  useRejectProfileReview,
} from "@/lib/queries/platform-admin";

export function ProfileReviewDialog({
  companyId,
  companyName,
}: {
  companyId: string;
  companyName: string;
}) {
  const [open, setOpen] = React.useState(false);
  const [rejecting, setRejecting] = React.useState(false);
  const [reason, setReason] = React.useState("");
  const { data: preview, isLoading } = useAdminProfilePreview(open ? companyId : undefined);
  const approve = useApproveProfileReview();
  const reject = useRejectProfileReview();

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="brand" size="sm">
          Review profile
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{companyName} — profile review</DialogTitle>
          <DialogDescription>
            This is exactly what candidates will see once approved.
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        )}
        {preview && <CompanyProfilePreview company={preview} />}

        {rejecting && (
          <Textarea
            placeholder="Reason (optional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
          />
        )}

        {(approve.isError || reject.isError) && (
          <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
        )}

        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button
            type="button"
            variant="brand"
            onClick={() => approve.mutate(companyId, { onSuccess: () => setOpen(false) })}
            disabled={approve.isPending || reject.isPending}
          >
            {approve.isPending ? "Approving…" : "Approve"}
          </Button>
          {rejecting ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() =>
                reject.mutate(
                  { companyId, reason: reason || undefined },
                  { onSuccess: () => setOpen(false) }
                )
              }
              disabled={reject.isPending || approve.isPending}
            >
              {reject.isPending ? "Rejecting…" : "Confirm reject"}
            </Button>
          ) : (
            <Button
              type="button"
              variant="secondary"
              onClick={() => setRejecting(true)}
              disabled={approve.isPending || reject.isPending}
            >
              Reject
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
