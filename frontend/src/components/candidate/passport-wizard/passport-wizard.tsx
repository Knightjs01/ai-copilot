"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { SecuringCvOverlay } from "@/components/candidate/securing-cv-overlay";
import { PassportProgressRing } from "@/components/candidate/passport-wizard/passport-progress-ring";
import { PassportStepRail, type PassportWizardStep } from "@/components/candidate/passport-wizard/passport-step-rail";
import { PassportSuccessOverlay } from "@/components/candidate/passport-wizard/passport-success-overlay";
import { PersonalInfoStep } from "@/components/candidate/passport-wizard/steps/personal-info-step";
import { PreferencesStep } from "@/components/candidate/passport-wizard/steps/preferences-step";
import { ProfessionalProfileStep } from "@/components/candidate/passport-wizard/steps/professional-profile-step";
import { ReviewStep } from "@/components/candidate/passport-wizard/steps/review-step";
import { UploadCvStep } from "@/components/candidate/passport-wizard/steps/upload-cv-step";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import {
  useApprovePassport,
  useDeleteOriginalCv,
  useDownloadOriginalCv,
  useMyPassport,
  useOriginalCvStatus,
  useParseCv,
  usePassportVersions,
  useSavePassport,
  useSuggestIndustries,
  useSuggestSkills,
  useSuggestSummary,
} from "@/lib/queries/phantom-passport";
import type { CareerEntryInput, CareerIntent, NoticePeriod, RemotePreference } from "@/lib/types";

const STEPS: PassportWizardStep[] = [
  { id: "upload", label: "Upload CV" },
  { id: "personal", label: "Personal Info" },
  { id: "professional", label: "Professional Profile" },
  { id: "preferences", label: "Preferences" },
  { id: "review", label: "Review & Publish" },
];

// Same floor as burn-project-dialog.tsx's purge animation — a fast parse-cv response shouldn't
// cut the "Securing your CV" sequence short.
const MIN_SECURING_MS = 2600;

function emptyCareerEntry(): CareerEntryInput {
  return {
    title: "",
    company_name: "",
    company_name_anonymized: "",
    start_date: null,
    end_date: null,
    is_current: false,
    responsibilities: "",
    achievements: [],
  };
}

function splitFullName(fullName: string): { first: string; last: string } {
  const trimmed = fullName.trim();
  if (!trimmed) return { first: "", last: "" };
  const parts = trimmed.split(/\s+/);
  return { first: parts[0] ?? "", last: parts.slice(1).join(" ") };
}

export function PassportWizard() {
  const { candidate } = useCandidateAuth();
  const { data: passport, isLoading } = useMyPassport();
  const savePassport = useSavePassport();
  const parseCv = useParseCv();
  const approvePassport = useApprovePassport();
  const { data: originalCv, isLoading: isLoadingOriginalCv } = useOriginalCvStatus();
  const downloadOriginalCv = useDownloadOriginalCv();
  const deleteOriginalCv = useDeleteOriginalCv();
  const { data: versions } = usePassportVersions();
  const suggestSummary = useSuggestSummary();
  const suggestSkills = useSuggestSkills();
  const suggestIndustries = useSuggestIndustries();

  const [headline, setHeadline] = React.useState("");
  const [seniority, setSeniority] = React.useState("");
  const [yearsExperience, setYearsExperience] = React.useState("");
  const [summary, setSummary] = React.useState("");
  const [skills, setSkills] = React.useState<string[]>([]);
  const [industries, setIndustries] = React.useState<string[]>([]);
  const [location, setLocation] = React.useState("");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | null>(null);
  const [salaryMin, setSalaryMin] = React.useState("");
  const [salaryMax, setSalaryMax] = React.useState("");
  const [noticePeriod, setNoticePeriod] = React.useState<NoticePeriod | null>(null);
  const [careerIntent, setCareerIntent] = React.useState<CareerIntent>("just_exploring");
  const [firstName, setFirstName] = React.useState("");
  const [lastName, setLastName] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [careerEntries, setCareerEntries] = React.useState<CareerEntryInput[]>([]);
  const [loadedOnce, setLoadedOnce] = React.useState(false);
  const [saveMessage, setSaveMessage] = React.useState<string | null>(null);
  const [cvError, setCvError] = React.useState<string | null>(null);
  const [securing, setSecuring] = React.useState(false);
  const [aiSuggestedFields, setAiSuggestedFields] = React.useState<string[] | null>(null);
  const [reviewed, setReviewed] = React.useState(false);
  const [approveError, setApproveError] = React.useState<string | null>(null);
  const [showVaultUploader, setShowVaultUploader] = React.useState(false);
  const [vaultError, setVaultError] = React.useState<string | null>(null);
  const [showSuccessOverlay, setShowSuccessOverlay] = React.useState(false);

  const [activeStep, setActiveStep] = React.useState(0);
  const [stepInitialized, setStepInitialized] = React.useState(false);

  const [summarySuggestion, setSummarySuggestion] = React.useState<string | null>(null);
  const [summarySuggestionError, setSummarySuggestionError] = React.useState<string | null>(null);
  const [skillsSuggestions, setSkillsSuggestions] = React.useState<string[] | null>(null);
  const [skillsSuggestionError, setSkillsSuggestionError] = React.useState<string | null>(null);
  const [industriesSuggestions, setIndustriesSuggestions] = React.useState<string[] | null>(null);
  const [industriesSuggestionError, setIndustriesSuggestionError] = React.useState<string | null>(
    null
  );
  // Guards the auto-suggest-on-arrival effect so it only ever fires once per visit to Step 3,
  // not on every render while the step is active.
  const autoSuggestedRef = React.useRef(false);

  React.useEffect(() => {
    if (loadedOnce) return;
    if (passport) {
      const { first, last } = splitFullName(passport.personal_info.legal_name);
      setHeadline(passport.headline ?? "");
      setSeniority(passport.seniority ?? "");
      setYearsExperience(passport.years_experience != null ? String(passport.years_experience) : "");
      setSummary(passport.summary ?? "");
      setSkills(passport.skills);
      setIndustries(passport.industries);
      setLocation(passport.location ?? "");
      setRemotePreference(passport.remote_preference);
      setSalaryMin(passport.salary_min != null ? String(passport.salary_min) : "");
      setSalaryMax(passport.salary_max != null ? String(passport.salary_max) : "");
      setNoticePeriod(passport.notice_period);
      setCareerIntent(passport.career_intent);
      setFirstName(first);
      setLastName(last);
      setPhone(passport.personal_info.phone ?? "");
      setCareerEntries(
        passport.career_entries.map((entry) => ({
          title: entry.title,
          company_name: entry.company_name,
          company_name_anonymized: entry.company_name_anonymized,
          start_date: entry.start_date,
          end_date: entry.end_date,
          is_current: entry.is_current,
          responsibilities: entry.responsibilities ?? "",
          achievements: entry.achievements,
        }))
      );
      setLoadedOnce(true);
    } else if (passport === null && candidate) {
      // No Passport yet, pre-fill the name from signup so it's one less field to type.
      const { first, last } = splitFullName(candidate.full_name);
      setFirstName(first);
      setLastName(last);
      setLoadedOnce(true);
    }
  }, [passport, candidate, loadedOnce]);

  // Resume-in-progress: land on the first step that still has real, missing data instead of
  // always resetting to Step 1 — grounded in the real fields already saved, no new backend state.
  React.useEffect(() => {
    if (stepInitialized || !loadedOnce) return;
    let resumeStep = 0;
    if (passport?.current_version_number != null) {
      resumeStep = 4;
    } else if (headline || summary || careerEntries.length > 0 || originalCv) {
      if (!firstName || !location) resumeStep = 1;
      else if (!headline || !summary) resumeStep = 2;
      else if (!remotePreference) resumeStep = 3;
      else resumeStep = 4;
    }
    setActiveStep(resumeStep);
    setStepInitialized(true);
    // Only ever runs once, right after the initial data load settles.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepInitialized, loadedOnce]);

  const updateEntry = (index: number, patch: Partial<CareerEntryInput>) => {
    setCareerEntries((entries) =>
      entries.map((entry, i) => (i === index ? { ...entry, ...patch } : entry))
    );
  };

  const removeEntry = (index: number) => {
    setCareerEntries((entries) => entries.filter((_, i) => i !== index));
  };

  const handleParseCv = async (file: File) => {
    setCvError(null);
    setSecuring(true);
    setReviewed(false);
    const minDelay = new Promise((resolve) => setTimeout(resolve, MIN_SECURING_MS));
    try {
      const [result] = await Promise.all([parseCv.mutateAsync(file), minDelay]);
      setHeadline((prev) => result.headline ?? prev);
      setSeniority((prev) => result.seniority ?? prev);
      setYearsExperience((prev) =>
        result.years_experience != null ? String(result.years_experience) : prev
      );
      setSummary((prev) => result.summary ?? prev);
      if (result.skills.length > 0) setSkills(result.skills);
      if (result.industries.length > 0) setIndustries(result.industries);
      if (result.detected_phone) setPhone(result.detected_phone);
      if (result.career_entries.length > 0) {
        setCareerEntries(
          result.career_entries.map((entry) => ({
            title: entry.title,
            company_name: entry.company_name,
            company_name_anonymized: entry.company_name_anonymized,
            start_date: entry.start_date,
            end_date: entry.end_date,
            is_current: entry.is_current,
            responsibilities: entry.responsibilities ?? "",
            achievements: entry.achievements,
          }))
        );
      }
      setAiSuggestedFields(result.ai_suggested_fields);
    } catch {
      setCvError("Couldn't parse that file. You can still fill in your Passport by hand.");
    } finally {
      setSecuring(false);
    }
  };

  const legalName = [firstName.trim(), lastName.trim()].filter(Boolean).join(" ");
  const canSave = firstName.trim().length > 0;

  const handleSave = async (): Promise<boolean> => {
    if (!canSave) return true;
    setSaveMessage(null);
    try {
      await savePassport.mutateAsync({
        headline: headline || null,
        seniority: seniority || null,
        years_experience: yearsExperience ? Number(yearsExperience) : null,
        summary: summary || null,
        skills,
        industries,
        location: location || null,
        remote_preference: remotePreference,
        salary_min: salaryMin ? Number(salaryMin) : null,
        salary_max: salaryMax ? Number(salaryMax) : null,
        notice_period: noticePeriod,
        career_intent: careerIntent,
        personal_info: {
          legal_name: legalName,
          phone: phone || null,
        },
        career_entries: careerEntries.map((entry) => ({
          ...entry,
          company_name_anonymized: entry.company_name_anonymized || entry.company_name,
        })),
      });
      setSaveMessage("Saved just now.");
      return true;
    } catch {
      setSaveMessage("Couldn't save. Check the required fields and try again.");
      return false;
    }
  };

  const handleApprove = () => {
    setApproveError(null);
    void (async () => {
      const saved = await handleSave();
      if (!saved) return;
      approvePassport.mutate(undefined, {
        onSuccess: () => {
          setReviewed(false);
          setShowSuccessOverlay(true);
        },
        onError: () => setApproveError("Couldn't approve your Passport. Try again."),
      });
    })();
  };

  const goToStep = (index: number) => {
    setActiveStep(Math.max(0, Math.min(STEPS.length - 1, index)));
  };

  const handleContinue = async () => {
    if (canSave) {
      const ok = await handleSave();
      if (!ok) return;
    }
    goToStep(activeStep + 1);
  };

  const handleRequestSummarySuggestion = async () => {
    setSummarySuggestionError(null);
    try {
      const result = await suggestSummary.mutateAsync({
        headline: headline || null,
        summary,
        skills,
      });
      setSummarySuggestion(result.suggested_summary);
    } catch {
      setSummarySuggestionError("Couldn't get a suggestion right now. Try again.");
    }
  };

  const handleRequestSkillsSuggestion = React.useCallback(async () => {
    setSkillsSuggestionError(null);
    try {
      const result = await suggestSkills.mutateAsync({
        headline: headline || null,
        summary: summary || null,
        existing_skills: skills,
      });
      setSkillsSuggestions(result.suggested_skills);
    } catch {
      setSkillsSuggestionError("Couldn't get suggestions right now. Try again.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [headline, summary, skills]);

  const handleRequestIndustriesSuggestion = React.useCallback(async () => {
    setIndustriesSuggestionError(null);
    try {
      const result = await suggestIndustries.mutateAsync({
        headline: headline || null,
        summary: summary || null,
        existing_industries: industries,
      });
      setIndustriesSuggestions(result.suggested_industries);
    } catch {
      setIndustriesSuggestionError("Couldn't get suggestions right now. Try again.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [headline, summary, industries]);

  // Reduces the "too manual" friction of an empty Skills/Industries step: as soon as the
  // candidate arrives with enough to work from (a headline or summary) and hasn't already added
  // anything, fetch real AI suggestions once automatically instead of requiring a button click
  // first. Still just a suggestion — nothing is added until the candidate taps a chip.
  React.useEffect(() => {
    if (activeStep !== 2 || autoSuggestedRef.current) return;
    // Waits for a headline or summary to exist before firing — reacts to typing while already
    // on this step, not just to the moment of arrival, since most candidates land here empty
    // and fill Core Profile in before Skills & Industries has anything to suggest from.
    if (!headline && !summary) return;
    autoSuggestedRef.current = true;
    if (skills.length === 0) void handleRequestSkillsSuggestion();
    if (industries.length === 0) void handleRequestIndustriesSuggestion();
    // Deliberately fires only once per Passport — re-running handleRequestSkillsSuggestion here
    // would refire on every keystroke since it closes over headline/summary/skills.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeStep, headline, summary]);

  if (isLoading || !loadedOnce) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const hasParsedData = Boolean(headline || summary || careerEntries.length > 0);
  const completedIndices = new Set<number>();
  if (hasParsedData || originalCv) completedIndices.add(0);
  if (firstName && location) completedIndices.add(1);
  if (headline && summary) completedIndices.add(2);
  if (remotePreference) completedIndices.add(3);
  if (passport?.current_version_number != null) completedIndices.add(4);

  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border bg-background p-6 shadow-xl shadow-slate-900/5 sm:p-10">
      <SecuringCvOverlay active={securing} />
      <PassportSuccessOverlay
        active={showSuccessOverlay}
        onDismiss={() => setShowSuccessOverlay(false)}
        callsign={passport?.callsign ?? null}
        headline={headline || passport?.headline || null}
        verificationStatus={passport?.verification_status ?? "unverified"}
        completionPercentage={passport?.completion_percentage ?? 0}
        versionNumber={passport?.current_version_number ?? 1}
      />

      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Build your Phantom Passport
        </h1>
        <p className="text-sm text-muted-foreground">
          One professional identity, your control. Recruiters only ever see what you approve —
          never your name, until you choose to reveal it.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[260px_1fr] md:items-start">
        <div className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-5 md:sticky md:top-24">
          <div className="flex justify-center md:justify-start">
            <PassportProgressRing percentage={passport?.completion_percentage ?? 0} />
          </div>
          <PassportStepRail
            steps={STEPS}
            activeIndex={activeStep}
            completedIndices={completedIndices}
            onStepClick={goToStep}
          />
        </div>

        <div className="flex flex-col gap-6">
          <div>
            {activeStep === 0 && (
              <UploadCvStep
                onFileSelected={handleParseCv}
                securing={securing}
                cvError={cvError}
                hasParsedData={hasParsedData}
                parsedSummary={
                  hasParsedData
                    ? { headline: headline || null, skillsCount: skills.length, entriesCount: careerEntries.length }
                    : null
                }
                originalCv={originalCv}
                isLoadingOriginalCv={isLoadingOriginalCv}
                showVaultUploader={showVaultUploader}
                onShowVaultUploader={setShowVaultUploader}
                onDownloadOriginalCv={() => downloadOriginalCv.mutate()}
                isDownloadingOriginalCv={downloadOriginalCv.isPending}
                onDeleteOriginalCv={() => {
                  if (
                    window.confirm(
                      "Delete your original CV? You'll need to re-upload it to reprocess your Passport later. Your approved Passport data is not affected."
                    )
                  ) {
                    setVaultError(null);
                    deleteOriginalCv.mutate(undefined, {
                      onError: () => setVaultError("Couldn't delete your CV. Try again."),
                    });
                  }
                }}
                isDeletingOriginalCv={deleteOriginalCv.isPending}
                vaultError={vaultError}
              />
            )}

            {activeStep === 1 && (
              <PersonalInfoStep
                firstName={firstName}
                onFirstNameChange={setFirstName}
                lastName={lastName}
                onLastNameChange={setLastName}
                email={candidate?.email ?? ""}
                phone={phone}
                onPhoneChange={setPhone}
                location={location}
                onLocationChange={setLocation}
              />
            )}

            {activeStep === 2 && (
              <ProfessionalProfileStep
                headline={headline}
                onHeadlineChange={setHeadline}
                seniority={seniority}
                onSeniorityChange={setSeniority}
                yearsExperience={yearsExperience}
                onYearsExperienceChange={setYearsExperience}
                summary={summary}
                onSummaryChange={setSummary}
                skills={skills}
                onSkillsChange={setSkills}
                industries={industries}
                onIndustriesChange={setIndustries}
                aiSuggestedFields={aiSuggestedFields}
                careerEntries={careerEntries}
                onUpdateEntry={updateEntry}
                onRemoveEntry={removeEntry}
                onAddEntry={() => setCareerEntries((entries) => [...entries, emptyCareerEntry()])}
                onRequestSummarySuggestion={handleRequestSummarySuggestion}
                isSuggestingSummary={suggestSummary.isPending}
                summarySuggestion={summarySuggestion}
                summarySuggestionError={summarySuggestionError}
                onApplySummarySuggestion={() => {
                  if (summarySuggestion) setSummary(summarySuggestion);
                  setSummarySuggestion(null);
                }}
                onDismissSummarySuggestion={() => setSummarySuggestion(null)}
                onRequestSkillsSuggestion={() => void handleRequestSkillsSuggestion()}
                isSuggestingSkills={suggestSkills.isPending}
                skillsSuggestions={skillsSuggestions}
                skillsSuggestionError={skillsSuggestionError}
                onRequestIndustriesSuggestion={() => void handleRequestIndustriesSuggestion()}
                isSuggestingIndustries={suggestIndustries.isPending}
                industriesSuggestions={industriesSuggestions}
                industriesSuggestionError={industriesSuggestionError}
              />
            )}

            {activeStep === 3 && (
              <PreferencesStep
                remotePreference={remotePreference}
                onRemotePreferenceChange={setRemotePreference}
                salaryMin={salaryMin}
                onSalaryMinChange={setSalaryMin}
                salaryMax={salaryMax}
                onSalaryMaxChange={setSalaryMax}
                noticePeriod={noticePeriod}
                onNoticePeriodChange={setNoticePeriod}
                careerIntent={careerIntent}
                onCareerIntentChange={setCareerIntent}
              />
            )}

            {activeStep === 4 && (
              <ReviewStep
                passport={passport}
                versions={versions}
                careerEntries={careerEntries}
                headline={headline}
                seniority={seniority}
                summary={summary}
                skills={skills}
                industries={industries}
                canApprove={canSave}
                reviewed={reviewed}
                onReviewedChange={setReviewed}
                onNavigateToProfileStep={() => goToStep(2)}
                approveError={approveError}
                onApprove={handleApprove}
                isApproving={approvePassport.isPending}
                isSaving={savePassport.isPending}
              />
            )}
          </div>

          <div className="flex items-center justify-between gap-3 border-t border-border pt-5">
            <Button
              type="button"
              variant="secondary"
              onClick={() => goToStep(activeStep - 1)}
              disabled={activeStep === 0}
            >
              <ChevronLeft className="h-4 w-4" /> Back
            </Button>
            <div className="flex items-center gap-3">
              {saveMessage && <span className="text-xs text-muted-foreground">{saveMessage}</span>}
              {activeStep < STEPS.length - 1 ? (
                <Button
                  type="button"
                  variant="brand"
                  onClick={handleContinue}
                  disabled={savePassport.isPending}
                >
                  {savePassport.isPending ? "Saving…" : "Continue"} <ChevronRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void handleSave()}
                  disabled={savePassport.isPending || !canSave}
                >
                  {savePassport.isPending ? "Saving…" : "Save draft"}
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
