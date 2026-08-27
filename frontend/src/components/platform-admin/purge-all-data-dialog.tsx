"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api-client";
import { usePurgeAllData } from "@/lib/queries/platform-admin";

const CONFIRMATION_PHRASE = "DELETE ALL DATA";

// Password re-entry used to live in this dialog too, before Danger Zone required a page-level
// step-up (password + MFA) just to reach this point -- asking for it a second time here would be
// redundant, so the only remaining friction is the typed confirmation phrase.
export function PurgeAllDataDialog({ stepUpToken }: { stepUpToken: string }) {
  const [open, setOpen] = React.useState(false);
  const [phrase, setPhrase] = React.useState("");
  const [result, setResult] = React.useState<number | null>(null);
  const purge = usePurgeAllData();

  const canSubmit = phrase === CONFIRMATION_PHRASE && !purge.isPending;

  const onOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setPhrase("");
      setResult(null);
      purge.reset();
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    purge.mutate(
      { confirmationPhrase: phrase, stepUpToken },
      { onSuccess: (res) => setResult(res.tables_cleared) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <Button type="button" variant="danger" onClick={() => setOpen(true)}>
        Purge all data
      </Button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Purge all data</DialogTitle>
        </DialogHeader>

        {result !== null ? (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-foreground">
              Done. {result} table{result === 1 ? "" : "s"} cleared. Your platform-admin login is
              unaffected.
            </p>
            <DialogFooter>
              <Button type="button" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <p className="text-sm text-muted-foreground">
              This deletes every company, user, candidate, project, and application on the
              platform. It cannot be undone. Type <strong className="text-foreground">
                {CONFIRMATION_PHRASE}
              </strong>{" "}
              to continue.
            </p>
            <Field label={`Type "${CONFIRMATION_PHRASE}"`} htmlFor="purge-phrase">
              <Input
                id="purge-phrase"
                value={phrase}
                onChange={(e) => setPhrase(e.target.value)}
                autoComplete="off"
              />
            </Field>
            {purge.isError && (
              <p className="text-sm font-medium text-danger">
                {purge.error instanceof ApiError && purge.error.status === 403
                  ? "Your verification expired — reload this page and confirm it's you again."
                  : "Couldn't purge — check the phrase and try again."}
              </p>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="secondary"
                onClick={() => onOpenChange(false)}
                disabled={purge.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" variant="danger" disabled={!canSubmit}>
                {purge.isPending ? "Purging…" : "Purge everything"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
