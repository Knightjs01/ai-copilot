"use client";

import * as React from "react";
import { formatDistanceToNow } from "date-fns";
import { StickyNote } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useApplicantNotes, useCreateApplicantNote } from "@/lib/queries/applicant-notes";
import { useToast } from "@/lib/toast-context";

export function NotesSection({ jobId, applicationId }: { jobId: string; applicationId: string }) {
  const { data: notes, isLoading } = useApplicantNotes(jobId, applicationId);
  const createNote = useCreateApplicantNote(jobId, applicationId);
  const toast = useToast();
  const [body, setBody] = React.useState("");

  const handleAdd = () => {
    const trimmed = body.trim();
    if (!trimmed) return;
    createNote.mutate(trimmed, {
      onSuccess: () => setBody(""),
      onError: () => toast({ title: "Couldn't add note", variant: "danger" }),
    });
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-1.5">
        <StickyNote className="h-3.5 w-3.5 text-muted-foreground" />
        <h3 className="text-sm font-medium text-foreground">Notes</h3>
        <span className="text-xs text-muted-foreground">Private to your hiring team</span>
      </div>

      {!isLoading && notes && notes.length > 0 && (
        <div className="flex flex-col gap-2.5">
          {notes.map((note) => (
            <div key={note.id} className="rounded-lg bg-secondary/40 p-2.5">
              <p className="text-sm text-foreground">{note.body}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {note.author_email} · {formatDistanceToNow(new Date(note.created_at), { addSuffix: true })}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-2">
        <Textarea
          placeholder="Add a note for your team…"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          disabled={createNote.isPending}
          className="min-h-[70px] text-sm"
        />
        <div className="flex justify-end">
          <Button
            size="sm"
            variant="secondary"
            onClick={handleAdd}
            disabled={!body.trim() || createNote.isPending}
          >
            {createNote.isPending ? "Adding…" : "Add note"}
          </Button>
        </div>
      </div>
    </div>
  );
}
