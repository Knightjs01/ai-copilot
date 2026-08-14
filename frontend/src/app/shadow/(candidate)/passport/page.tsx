"use client";

import * as React from "react";
import { Download, Plus, Sparkles, Trash2, UploadCloud } from "lucide-react";

import { SecuringCvOverlay } from "@/components/candidate/securing-cv-overlay";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import {
  useApprovePassport,
  useDeleteOriginalCv,
  useDownloadOriginalCv,
  useMyPassport,
  useOriginalCvStatus,
  useParseCv,
  usePassportVersions,
  useSavePassport,
} from "@/lib/queries/phantom-passport";
import { CAREER_INTENT_LABEL, NOTICE_PERIOD_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import type { CareerEntryInput, CareerIntent, NoticePeriod, RemotePreference } from "@/lib/types";
import { useCandidateAuth } from "@/lib/candidate-auth-context";

const CAREER_INTENT_OPTIONS = (Object.keys(CAREER_INTENT_LABEL) as CareerIntent[]).map((value) => ({
  value,
  label: CAREER_INTENT_LABEL[value],
}));
const REMOTE_PREFERENCE_OPTIONS = (Object.keys(REMOTE_PREFERENCE_LABEL) as RemotePreference[]).map(
  (value) => ({ value, label: REMOTE_PREFERENCE_LABEL[value] })
);
const NOTICE_PERIOD_OPTIONS = (Object.keys(NOTICE_PERIOD_LABEL) as NoticePeriod[]).map((value) => ({
  value,
  label: NOTICE_PERIOD_LABEL[value],
}));

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

function AiFieldBadge({ field, aiSuggestedFields }: { field: string; aiSuggestedFields: string[] | null }) {
  if (aiSuggestedFields === null) return null;
  const suggested = aiSuggestedFields.includes(field);
  return (
    <Badge variant={suggested ? "info" : "success"} className="ml-2 align-middle">
      {suggested ? "✦ Suggested by Phantom AI" : "✓ Extracted from your CV"}
    </Badge>
  );
}

export default function PassportPage() {
  const { candidate } = useCandidateAuth();
  const { data: passport, isLoading } = useMyPassport();
  const savePassport = useSavePassport();
  const parseCv = useParseCv();
  const approvePassport = useApprovePassport();
  const { data: originalCv, isLoading: isLoadingOriginalCv } = useOriginalCvStatus();
  const downloadOriginalCv = useDownloadOriginalCv();
  const deleteOriginalCv = useDeleteOriginalCv();
  const { data: versions } = usePassportVersions();

  const [headline, setHeadline] = React.useState("");
  const [seniority, setSeniority] = React.useState("");
  const [yearsExperience, setYearsExperience] = React.useState("");
  const [summary, setSummary] = React.useState("");
  const [skillsText, setSkillsText] = React.useState("");
  const [industriesText, setIndustriesText] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | null>(null);
  const [salaryMin, setSalaryMin] = React.useState("");
  const [salaryMax, setSalaryMax] = React.useState("");
  const [noticePeriod, setNoticePeriod] = React.useState<NoticePeriod | null>(null);
  const [careerIntent, setCareerIntent] = React.useState<CareerIntent>("just_exploring");
  const [legalName, setLegalName] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [address, setAddress] = React.useState("");
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

  React.useEffect(() => {
    if (loadedOnce) return;
    if (passport) {
      setHeadline(passport.headline ?? "");
      setSeniority(passport.seniority ?? "");
      setYearsExperience(passport.years_experience != null ? String(passport.years_experience) : "");
      setSummary(passport.summary ?? "");
      setSkillsText(passport.skills.join(", "));
      setIndustriesText(passport.industries.join(", "));
      setLocation(passport.location ?? "");
      setRemotePreference(passport.remote_preference);
      setSalaryMin(passport.salary_min != null ? String(passport.salary_min) : "");
      setSalaryMax(passport.salary_max != null ? String(passport.salary_max) : "");
      setNoticePeriod(passport.notice_period);
      setCareerIntent(passport.career_intent);
      setLegalName(passport.personal_info.legal_name);
      setPhone(passport.personal_info.phone ?? "");
      setAddress(passport.personal_info.address ?? "");
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
      // No Passport yet, pre-fill the legal name from signup so it's one less field to type.
      setLegalName(candidate.full_name);
      setLoadedOnce(true);
    }
  }, [passport, candidate, loadedOnce]);

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
      if (result.skills.length > 0) setSkillsText(result.skills.join(", "));
      if (result.industries.length > 0) setIndustriesText(result.industries.join(", "));
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

  const handleSave = async (): Promise<boolean> => {
    setSaveMessage(null);
    try {
      await savePassport.mutateAsync({
        headline: headline || null,
        seniority: seniority || null,
        years_experience: yearsExperience ? Number(yearsExperience) : null,
        summary: summary || null,
        skills: skillsText.split(",").map((s) => s.trim()).filter(Boolean),
        industries: industriesText.split(",").map((s) => s.trim()).filter(Boolean),
        location: location || null,
        remote_preference: remotePreference,
        salary_min: salaryMin ? Number(salaryMin) : null,
        salary_max: salaryMax ? Number(salaryMax) : null,
        notice_period: noticePeriod,
        career_intent: careerIntent,
        personal_info: {
          legal_name: legalName,
          phone: phone || null,
          address: address || null,
        },
        career_entries: careerEntries.map((entry) => ({
          ...entry,
          company_name_anonymized: entry.company_name_anonymized || entry.company_name,
        })),
      });
      return true;
    } catch {
      setSaveMessage("Couldn't save. Check the required fields and try again.");
      return false;
    }
  };

  const handleSaveClick = async () => {
    const ok = await handleSave();
    if (ok) setSaveMessage("Passport saved.");
  };

  const handleApprove = async () => {
    setApproveError(null);
    const saved = await handleSave();
    if (!saved) return;
    try {
      await approvePassport.mutateAsync();
      setReviewed(false);
    } catch {
      setApproveError("Couldn't approve your Passport. Try again.");
    }
  };

  if (isLoading || !loadedOnce) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <SecuringCvOverlay active={securing} />
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Your Phantom Passport
          </h1>
          <p className="text-sm text-muted-foreground">
            Professional data and personal data are stored separately, recruiters only ever see
            what&apos;s below the line, never your name.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {passport?.current_version_number != null && (
            <Badge variant="success">Approved · Version {passport.current_version_number}</Badge>
          )}
          {passport && <Badge variant="info">{passport.completion_percentage}% complete</Badge>}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Parse from CV</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Dropzone
            label="Drop your CV here"
            hint="PDF or Word. Your original is stored privately in your Candidate Vault, and never shown to recruiters."
            isUploading={securing}
            onFileSelected={handleParseCv}
          />
          {cvError && <p className="text-sm font-medium text-danger">{cvError}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Professional profile</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Field label="Headline" htmlFor="headline">
            <Input
              id="headline"
              placeholder="e.g. Senior Product Leader"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Seniority" htmlFor="seniority">
              <Input
                id="seniority"
                placeholder="e.g. Senior"
                value={seniority}
                onChange={(e) => setSeniority(e.target.value)}
              />
            </Field>
            <Field label="Years of experience" htmlFor="yearsExperience">
              <Input
                id="yearsExperience"
                type="number"
                min={0}
                value={yearsExperience}
                onChange={(e) => setYearsExperience(e.target.value)}
              />
            </Field>
          </div>
          <Field label="Summary" htmlFor="summary">
            <Textarea id="summary" value={summary} onChange={(e) => setSummary(e.target.value)} />
          </Field>
          <Field
            label={
              <>
                Skills
                <AiFieldBadge field="skills" aiSuggestedFields={aiSuggestedFields} />
              </>
            }
            htmlFor="skills"
          >
            <Input
              id="skills"
              placeholder="Comma-separated, e.g. Product Strategy, Team Leadership"
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
            />
          </Field>
          <Field
            label={
              <>
                Industries
                <AiFieldBadge field="industries" aiSuggestedFields={aiSuggestedFields} />
              </>
            }
            htmlFor="industries"
          >
            <Input
              id="industries"
              placeholder="Comma-separated, e.g. FinTech, B2B SaaS"
              value={industriesText}
              onChange={(e) => setIndustriesText(e.target.value)}
            />
          </Field>
          <Field label="Location" htmlFor="location">
            <Input id="location" value={location} onChange={(e) => setLocation(e.target.value)} />
          </Field>
          <Field label="Remote preference">
            <PillToggleGroup
              options={REMOTE_PREFERENCE_OPTIONS}
              value={remotePreference}
              onChange={setRemotePreference}
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Minimum salary" htmlFor="salaryMin">
              <Input
                id="salaryMin"
                type="number"
                min={0}
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
              />
            </Field>
            <Field label="Maximum salary" htmlFor="salaryMax">
              <Input
                id="salaryMax"
                type="number"
                min={0}
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
              />
            </Field>
          </div>
          <Field label="Notice period">
            <PillToggleGroup options={NOTICE_PERIOD_OPTIONS} value={noticePeriod} onChange={setNoticePeriod} />
          </Field>
          <Field label="Career intent">
            <PillToggleGroup
              options={CAREER_INTENT_OPTIONS}
              value={careerIntent}
              onChange={setCareerIntent}
            />
          </Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Career history</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {careerEntries.map((entry, index) => (
            <div key={index} className="flex flex-col gap-3 rounded-xl border border-border p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="grid flex-1 grid-cols-2 gap-3">
                  <Field label="Title" htmlFor={`title-${index}`}>
                    <Input
                      id={`title-${index}`}
                      value={entry.title}
                      onChange={(e) => updateEntry(index, { title: e.target.value })}
                    />
                  </Field>
                  <Field label="Real employer" htmlFor={`company-${index}`}>
                    <Input
                      id={`company-${index}`}
                      placeholder="Never shown until you approve a reveal"
                      value={entry.company_name}
                      onChange={(e) => updateEntry(index, { company_name: e.target.value })}
                    />
                  </Field>
                </div>
                <button
                  type="button"
                  onClick={() => removeEntry(index)}
                  className="mt-6 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-danger"
                  aria-label="Remove entry"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <Field
                label={
                  <>
                    Anonymized employer
                    <AiFieldBadge
                      field="company_name_anonymized"
                      aiSuggestedFields={aiSuggestedFields}
                    />
                  </>
                }
                htmlFor={`anon-${index}`}
                error={undefined}
              >
                <Input
                  id={`anon-${index}`}
                  placeholder='e.g. "Global Payments Platform" instead of "Stripe": this is what recruiters see'
                  value={entry.company_name_anonymized}
                  onChange={(e) => updateEntry(index, { company_name_anonymized: e.target.value })}
                />
              </Field>
              <Field label="What you did" htmlFor={`resp-${index}`}>
                <Textarea
                  id={`resp-${index}`}
                  value={entry.responsibilities ?? ""}
                  onChange={(e) => updateEntry(index, { responsibilities: e.target.value })}
                />
              </Field>
              <Field label="Achievements" htmlFor={`achievements-${index}`}>
                <Input
                  id={`achievements-${index}`}
                  placeholder="Comma-separated"
                  value={(entry.achievements ?? []).join(", ")}
                  onChange={(e) =>
                    updateEntry(index, {
                      achievements: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                    })
                  }
                />
              </Field>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  checked={entry.is_current}
                  onChange={(e) => updateEntry(index, { is_current: e.target.checked })}
                />
                I currently work here
              </label>
            </div>
          ))}
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="self-start"
            onClick={() => setCareerEntries((entries) => [...entries, emptyCareerEntry()])}
          >
            <Plus className="h-4 w-4" /> Add role
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Personal information</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-xs text-muted-foreground">
            Encrypted and never shown to any company unless you approve a Reveal Request.
          </p>
          <Field label="Legal name" htmlFor="legalName">
            <Input id="legalName" value={legalName} onChange={(e) => setLegalName(e.target.value)} />
          </Field>
          <Field label="Phone" htmlFor="phone">
            <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </Field>
          <Field label="Address" htmlFor="address">
            <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} />
          </Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Candidate Vault</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-xs text-muted-foreground">
            Your original CV is stored privately here. Recruiters cannot access it — they only
            ever see the approved Passport data above.
          </p>
          {isLoadingOriginalCv ? (
            <Spinner className="h-4 w-4 text-muted-foreground" />
          ) : originalCv && !showVaultUploader ? (
            <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
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
                  onClick={() => downloadOriginalCv.mutate()}
                  disabled={downloadOriginalCv.isPending}
                >
                  <Download className="h-3.5 w-3.5" /> View
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setShowVaultUploader(true)}>
                  <UploadCloud className="h-3.5 w-3.5" /> Replace
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => {
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
                  disabled={deleteOriginalCv.isPending}
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
                  await handleParseCv(file);
                  setShowVaultUploader(false);
                }}
              />
              {originalCv && (
                <Button size="sm" variant="secondary" className="self-start" onClick={() => setShowVaultUploader(false)}>
                  Cancel
                </Button>
              )}
            </div>
          )}
          {vaultError && <p className="text-sm font-medium text-danger">{vaultError}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Review before publishing</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            We&apos;ve built this version of your Passport from your CV and any edits above.
            Phantom has automatically parsed your CV, but AI can occasionally make mistakes.
            Please review everything carefully — you have complete control over what&apos;s added
            to your Passport, and nothing becomes part of your discoverable Passport until you
            approve it.
          </p>
          {versions && versions.length > 0 && versions[0] && (
            <p className="text-xs text-muted-foreground">
              {passport?.current_version_number != null
                ? `Currently approved: Version ${passport.current_version_number} (${new Date(versions[0].approved_at).toLocaleDateString()})`
                : "Not yet approved."}
            </p>
          )}
          <label className="flex items-start gap-2.5 text-sm text-foreground">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={reviewed}
              onChange={(e) => setReviewed(e.target.checked)}
            />
            I have reviewed my Passport and approve the information above.
          </label>
          {approveError && <p className="text-sm font-medium text-danger">{approveError}</p>}
          <div className="flex justify-end">
            <Button
              variant="brand"
              size="lg"
              onClick={handleApprove}
              disabled={!reviewed || !legalName || approvePassport.isPending || savePassport.isPending}
            >
              <Sparkles className="h-4 w-4" />
              {approvePassport.isPending ? "Approving…" : "Approve & Build My Passport"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-end gap-3">
        {saveMessage && <p className="text-sm text-muted-foreground">{saveMessage}</p>}
        <Button
          variant="secondary"
          size="lg"
          onClick={handleSaveClick}
          disabled={savePassport.isPending || !legalName}
        >
          {savePassport.isPending ? "Saving…" : "Save draft"}
        </Button>
      </div>
    </div>
  );
}
