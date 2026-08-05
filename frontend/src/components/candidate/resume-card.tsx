"use client";

import { ShieldCheck } from "lucide-react";

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resume</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Dropzone
          label="Drop the candidate's resume here"
          hint="PDF or DOCX"
          currentFileName={candidate.resume_original_filename}
          isUploading={uploadResume.isPending}
          onFileSelected={(file) => uploadResume.mutate(file)}
        />

        {candidate.resume_original_filename && (
          <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-2 text-sm text-foreground">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              {sanitizedProfile
                ? "Resume redacted — safe to send to AI"
                : "Not yet redacted"}
            </div>
            {!sanitizedProfile && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => sanitize.mutate()}
                disabled={sanitize.isPending || isLoadingSanitized}
              >
                {sanitize.isPending ? "Redacting…" : "Sanitize"}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
