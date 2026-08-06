"use client";

import * as React from "react";
import { FileText, ShieldCheck, UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { useSanitizeCandidate, useSanitizedProfile } from "@/lib/queries/privacy-gateway";
import { useUploadResume } from "@/lib/queries/candidates";
import type { Candidate } from "@/lib/types";

export function ResumeCard({ candidate }: { candidate: Candidate }) {
  const uploadResume = useUploadResume(candidate.id);
  const { data: sanitizedProfile, isLoading: isLoadingSanitized } = useSanitizedProfile(
    candidate.id
  );
  const sanitize = useSanitizeCandidate(candidate.id);
  const [showUploader, setShowUploader] = React.useState(false);

  // The raw resume file is purged once sanitized (privacy gateway clears it on redact), so a
  // sanitized profile — not resume_original_filename — is the durable signal that a CV exists.
  const hasResumeOnFile = !!candidate.resume_original_filename;
  const hasContent = hasResumeOnFile || !!sanitizedProfile;
  const displayUploader = showUploader || (!isLoadingSanitized && !hasContent);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>CV snapshot</CardTitle>
        {hasContent && (
          <Button size="sm" variant="secondary" onClick={() => setShowUploader((v) => !v)}>
            <UploadCloud className="h-3.5 w-3.5" />
            {displayUploader ? "Cancel" : "Replace CV"}
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {displayUploader && (
          <Dropzone
            label="Drop the candidate's resume here"
            hint="PDF or DOCX"
            currentFileName={candidate.resume_original_filename}
            isUploading={uploadResume.isPending}
            onFileSelected={(file) => {
              uploadResume.mutate(file, { onSuccess: () => setShowUploader(false) });
            }}
          />
        )}

        {hasResumeOnFile && !displayUploader && (
          <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-2 text-sm text-foreground">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              Not yet redacted
            </div>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => sanitize.mutate()}
              disabled={sanitize.isPending || isLoadingSanitized}
            >
              {sanitize.isPending ? "Redacting…" : "Sanitize"}
            </Button>
          </div>
        )}

        {sanitizedProfile && !displayUploader && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-sm text-foreground">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              Resume redacted — safe to send to AI
            </div>
            <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <FileText className="h-3.5 w-3.5" />
              Anonymised CV
            </h4>
            <div className="max-h-96 overflow-y-auto rounded-xl border border-border bg-white px-4 py-3">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground">
                {sanitizedProfile.redacted_text}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
