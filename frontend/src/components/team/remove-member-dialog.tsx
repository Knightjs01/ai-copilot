"use client";

import * as React from "react";
import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useRemoveUser } from "@/lib/queries/team";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";

export function RemoveMemberDialog({
  userId,
  fullName,
}: {
  userId: string;
  fullName: string;
}) {
  const [open, setOpen] = React.useState(false);
  const removeUser = useRemoveUser(userId);
  const container = useThemeScopeContainer();

  const handleConfirm = async () => {
    await removeUser.mutateAsync();
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-danger/10 hover:text-danger"
          aria-label={`Remove ${fullName}`}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </DialogTrigger>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>Remove {fullName}?</DialogTitle>
          <DialogDescription>
            They&apos;ll immediately lose access to this workspace. This doesn&apos;t affect
            hiring projects or candidates they&apos;ve already worked on.
          </DialogDescription>
        </DialogHeader>
        {removeUser.isError && (
          <p className="text-sm font-medium text-danger">Couldn&apos;t remove. Try again.</p>
        )}
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
            disabled={removeUser.isPending}
          >
            Cancel
          </Button>
          <Button type="button" variant="danger" onClick={handleConfirm} disabled={removeUser.isPending}>
            {removeUser.isPending ? "Removing…" : "Remove"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
