"use client";

import * as React from "react";
import Link from "next/link";
import { Archive, CheckCircle2, FileText, History, Sparkles } from "lucide-react";

import { AnonymisedCvDialog } from "@/components/candidate/passport-wizard/anonymised-cv-dialog";
import { PassportCard } from "@/components/candidate/passport-wizard/passport-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";
import type { CareerEntryInput, PassportVersionSummary, PhantomPassport } from "@/lib/types";

const PRIVACY_CHECKLIST = [
  "Your name, email, and phone are encrypted and stored separately from your professional profile.",
  "Your real employer names stay hidden — only the anonymized names below are ever shown.",
  "Your original CV file stays in your private Candidate Vault and is never sent to a company.",
  "A company can only see your real identity after you personally approve a Reveal Request.",
];

interface ReviewStepProps {
  passport: PhantomPassport | null | undefined;
  versions: PassportVersionSummary[] | undefined;
  careerEntries: CareerEntryInput[];
  headline: string;
  seniority: string;
  summary: string;
  skills: string[];
  industries: string[];
  canApprove: boolean;
  reviewed: boolean;
  onReviewedChange: (value: boolean) => void;
  onNavigateToProfileStep: () => void;
  approveError: string | null;
  onApprove: () => void;
  isApproving: boolean;
  isSaving: boolean;
}

export function ReviewStep({
  passport,
  versions,
  careerEntries,
  headline,
  seniority,
  summary,
  skills,
  industries,
  canApprove,
  reviewed,
  onReviewedChange,
  onNavigateToProfileStep,
  approveError,
  onApprove,
  isApproving,
  isSaving,
}: ReviewStepProps) {
  const [showCvDialog, setShowCvDialog] = React.useState(false);
  const isPublished = passport?.current_version_number != null;
  const latestVersion = versions?.[0];

  return (
    <div className="flex flex-col gap-6">
      {isPublished && passport && (
        <PassportCard
          callsign={passport.callsign}
          headline={headline || passport.headline}
          verificationStatus={passport.verification_status}
          completionPercentage={passport.completion_percentage}
          versionNumber={passport.current_version_number ?? 1}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle>Privacy summary</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div className="flex flex-col gap-1 rounded-xl bg-background p-3">
              <dt className="text-xs text-muted-foreground">Personal</dt>
              <dd>
                <Badge variant="neutral">Locked</Badge>
              </dd>
            </div>
            <div className="flex flex-col gap-1 rounded-xl bg-background p-3">
              <dt className="text-xs text-muted-foreground">Professional</dt>
              <dd>
                {isPublished ? (
                  <Badge variant="success">Approved</Badge>
                ) : (
                  <Badge variant="neutral">Draft</Badge>
                )}
              </dd>
            </div>
            <div className="flex flex-col gap-1 rounded-xl bg-background p-3">
              <dt className="text-xs text-muted-foreground">Verification</dt>
              <dd>
                {passport ? (
                  <Badge variant={VERIFICATION_STATUS_VARIANT[passport.verification_status]}>
                    {VERIFICATION_STATUS_LABEL[passport.verification_status]}
                  </Badge>
                ) : (
                  <Badge variant="neutral">—</Badge>
                )}
              </dd>
            </div>
            <div className="flex flex-col gap-1 rounded-xl bg-background p-3">
              <dt className="text-xs text-muted-foreground">Identity</dt>
              <dd>
                <Badge variant="neutral">Callsign only</Badge>
              </dd>
            </div>
          </dl>
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              variant="secondary"
              className="self-start"
              onClick={() => setShowCvDialog(true)}
            >
              <FileText className="h-4 w-4" /> View my anonymised CV
            </Button>
            <Button type="button" variant="secondary" className="self-start" asChild>
              <Link href="/shadow/passport/identity-activity">
                <History className="h-4 w-4" /> Identity activity
              </Link>
            </Button>
            <Button type="button" variant="secondary" className="self-start" asChild>
              <Link href="/shadow/passport/talent-memory">
                <Archive className="h-4 w-4" /> Talent memory
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      <AnonymisedCvDialog
        open={showCvDialog}
        onOpenChange={setShowCvDialog}
        headline={headline}
        seniority={seniority}
        summary={summary}
        skills={skills}
        industries={industries}
        careerEntries={careerEntries}
        onApprove={() => onReviewedChange(true)}
        onDeclineAndEdit={() => {
          onReviewedChange(false);
          onNavigateToProfileStep();
        }}
      />

      <Card>
        <CardHeader>
          <CardTitle>Phantom Privacy Check</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2.5">
          {PRIVACY_CHECKLIST.map((item) => (
            <div key={item} className="flex items-start gap-2.5 text-sm">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
              <span className="text-foreground">{item}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Approve & publish</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            We&apos;ve built this version of your Passport from your CV and any edits you made.
            Phantom parses CVs automatically, but AI can occasionally make mistakes — please
            review everything carefully. Nothing becomes part of your discoverable Passport until
            you approve it here.
          </p>
          {latestVersion && (
            <p className="text-xs text-muted-foreground">
              {isPublished
                ? `Currently approved: Version ${passport?.current_version_number} (${new Date(latestVersion.approved_at).toLocaleDateString()})`
                : "Not yet approved."}
            </p>
          )}
          <label className="flex items-start gap-2.5 text-sm text-foreground">
            <input
              type="checkbox"
              className="mt-0.5 accent-brand"
              checked={reviewed}
              onChange={(e) => onReviewedChange(e.target.checked)}
            />
            I have reviewed my Passport and approve the information above.
          </label>
          {approveError && <p className="text-sm font-medium text-danger">{approveError}</p>}
          <div className="flex justify-end">
            <Button
              variant="brand"
              size="lg"
              onClick={onApprove}
              disabled={!reviewed || !canApprove || isApproving || isSaving}
            >
              <Sparkles className="h-4 w-4" />
              {isApproving ? "Approving…" : "Approve & Build My Passport"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
