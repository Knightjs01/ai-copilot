"use client";

import { CheckCircle2, Download, Trash2, UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { Spinner } from "@/components/ui/spinner";
import type { CvDocumentStatus } from "@/lib/types";

interface UploadCvStepProps {
  onFileSelected: (file: File) => Promise<void>;
  securing: boolean;
  cvError: string | null;
  hasParsedData: boolean;
  parsedSummary: { headline: string | null; skillsCount: number; entriesCount: number } | null;
  originalCv: CvDocumentStatus | null | undefined;
  isLoadingOriginalCv: boolean;
  showVaultUploader: boolean;
  onShowVaultUploader: (show: boolean) => void;
  onDownloadOriginalCv: () => void;
  isDownloadingOriginalCv: boolean;
  onDeleteOriginalCv: () => void;
  isDeletingOriginalCv: boolean;
  vaultError: string | null;
}

export function UploadCvStep({
  onFileSelected,
  securing,
  cvError,
  hasParsedData,
  parsedSummary,
  originalCv,
  isLoadingOriginalCv,
  showVaultUploader,
  onShowVaultUploader,
  onDownloadOriginalCv,
  isDownloadingOriginalCv,
  onDeleteOriginalCv,
  isDeletingOriginalCv,
  vaultError,
}: UploadCvStepProps) {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Start with your CV</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            Upload your CV and Phantom will pull out your headline, skills, and career history
            for you. You&apos;ll review and can edit every field before anything is saved — nothing
            here is invented, only what Phantom actually found or you confirm yourself.
          </p>
          <Dropzone
            label={hasParsedData ? "Drop a new CV to re-parse" : "Drop your CV here"}
            hint="PDF or Word. Your original is stored privately in your Candidate Vault, and never shown to recruiters."
            isUploading={securing}
            onFileSelected={onFileSelected}
          />
          {cvError && <p className="text-sm font-medium text-danger">{cvError}</p>}
          {hasParsedData && parsedSummary && (
            <div className="flex items-start gap-2.5 rounded-xl border border-success/20 bg-success/5 px-4 py-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
              <div className="flex flex-col gap-0.5 text-sm">
                <p className="font-medium text-foreground">
                  {parsedSummary.headline ?? "CV parsed"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {parsedSummary.skillsCount} skill{parsedSummary.skillsCount === 1 ? "" : "s"} and{" "}
                  {parsedSummary.entriesCount} role
                  {parsedSummary.entriesCount === 1 ? "" : "s"} found. Continue to review and edit
                  everything on the next steps.
                </p>
              </div>
            </div>
          )}
          {!hasParsedData && (
            <p className="text-xs text-muted-foreground">
              Prefer to type it yourself? You can skip this and fill in every step by hand.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Candidate Vault</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-xs text-muted-foreground">
            Your original CV file is stored privately here, encrypted. Recruiters cannot access
            it — they only ever see the approved Passport data you build in the next steps.
          </p>
          {isLoadingOriginalCv ? (
            <Spinner className="h-4 w-4 text-muted-foreground" />
          ) : originalCv && !showVaultUploader ? (
            <div className="flex flex-col items-start justify-between gap-3 rounded-xl bg-background px-4 py-3 sm:flex-row sm:items-center">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-foreground">
                  {originalCv.original_filename}
                </span>
                <span className="text-xs text-muted-foreground">
                  🔒 Secure · Uploaded {new Date(originalCv.uploaded_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={onDownloadOriginalCv}
                  disabled={isDownloadingOriginalCv}
                >
                  <Download className="h-3.5 w-3.5" /> View
                </Button>
                <Button size="sm" variant="secondary" onClick={() => onShowVaultUploader(true)}>
                  <UploadCloud className="h-3.5 w-3.5" /> Replace
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={onDeleteOriginalCv}
                  disabled={isDeletingOriginalCv}
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <Dropzone
                label="Drop your CV here"
                hint="PDF or Word"
                isUploading={securing}
                onFileSelected={async (file) => {
                  await onFileSelected(file);
                  onShowVaultUploader(false);
                }}
              />
              {originalCv && (
                <Button
                  size="sm"
                  variant="secondary"
                  className="self-start"
                  onClick={() => onShowVaultUploader(false)}
                >
                  Cancel
                </Button>
              )}
            </div>
          )}
          {vaultError && <p className="text-sm font-medium text-danger">{vaultError}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
