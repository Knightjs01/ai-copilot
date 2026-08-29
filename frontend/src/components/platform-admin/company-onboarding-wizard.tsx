"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { AboutStep } from "@/components/company/steps/about-step";
import { EmployeeExperienceStep } from "@/components/company/steps/employee-experience-step";
import { HiringProfileStep } from "@/components/company/steps/hiring-profile-step";
import { IdentityStep } from "@/components/company/steps/identity-step";
import { MediaStep } from "@/components/company/steps/media-step";
import { CompanyProfilePreview } from "@/components/company/company-profile-preview";
import {
  PassportStepRail,
  type PassportWizardStep,
} from "@/components/candidate/passport-wizard/passport-step-rail";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Spinner } from "@/components/ui/spinner";
import {
  useAdminActivateCompany,
  useAdminCommercialPlans,
  useAdminCompanyProfile,
  useAdminCreateCompany,
  useAdminInviteCompanyUser,
  useAdminUpdateCompanyProfile,
  useAdminUploadCoverImage,
  useAdminUploadLogo,
} from "@/lib/queries/platform-admin-companies";
import type { Company, CompanyProfile, CompanySizeBand, ContentItem, RoleName } from "@/lib/types";

const STEPS: PassportWizardStep[] = [
  { id: "account", label: "Create Account" },
  { id: "identity", label: "Identity" },
  { id: "about", label: "About & Culture" },
  { id: "employee-experience", label: "Employee Experience" },
  { id: "media", label: "Brand Media" },
  { id: "hiring-profile", label: "Hiring Profile" },
  { id: "company-users", label: "Company Users" },
  { id: "identity-protection", label: "Identity Protection" },
  { id: "review", label: "Review & Activate" },
];

// Not part of Company -- CompanyProfile is the shared public/preview shape CompanyProfilePreview
// actually renders. Built here from the admin-scoped Company the wizard already has loaded,
// since there's no /companies/me/preview equivalent an admin (not a company User) can call.
function toCompanyProfile(company: Company): CompanyProfile {
  return {
    name: company.name,
    slug: company.slug,
    description: company.description,
    culture: company.culture,
    benefits: company.benefits,
    size: company.size,
    industry: company.industry,
    logo_url: company.logo_url,
    cover_image_url: company.cover_image_url,
    hiring_process_overview: company.hiring_process_overview,
    tagline: company.tagline,
    website: company.website,
    founded_year: company.founded_year,
    headquarters: company.headquarters,
    is_verified_employer: company.is_verified_employer,
    values: company.values,
    looking_for: company.looking_for,
    hiring_highlights: company.hiring_highlights,
  };
}

function CreateAccountStep({
  isCreated,
  companyName,
  onCompanyNameChange,
  ownerFullName,
  onOwnerFullNameChange,
  ownerEmail,
  onOwnerEmailChange,
  commercialPlanCode,
  onCommercialPlanCodeChange,
}: {
  isCreated: boolean;
  companyName: string;
  onCompanyNameChange: (value: string) => void;
  ownerFullName: string;
  onOwnerFullNameChange: (value: string) => void;
  ownerEmail: string;
  onOwnerEmailChange: (value: string) => void;
  commercialPlanCode: string | null;
  onCommercialPlanCodeChange: (value: string) => void;
}) {
  const { data: plans } = useAdminCommercialPlans();

  if (isCreated) {
    return (
      <div className="flex flex-col gap-4">
        <p className="text-sm text-muted-foreground">
          Account created — these details are fixed. Everything below is still editable before
          activation.
        </p>
        <Field label="Company name">
          <Input value={companyName} disabled />
        </Field>
        <Field label="Owner">
          <Input value={`${ownerFullName} — ${ownerEmail}`} disabled />
        </Field>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Field label="Company name" htmlFor="admin-company-name">
        <Input
          id="admin-company-name"
          value={companyName}
          onChange={(e) => onCompanyNameChange(e.target.value)}
          placeholder="Acme Inc."
        />
      </Field>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Owner full name" htmlFor="admin-owner-full-name">
          <Input
            id="admin-owner-full-name"
            value={ownerFullName}
            onChange={(e) => onOwnerFullNameChange(e.target.value)}
          />
        </Field>
        <Field label="Owner work email" htmlFor="admin-owner-email">
          <Input
            id="admin-owner-email"
            type="email"
            value={ownerEmail}
            onChange={(e) => onOwnerEmailChange(e.target.value)}
          />
        </Field>
      </div>
      {plans && plans.length > 0 && (
        <Field label="Commercial plan">
          <PillToggleGroup
            options={plans.map((plan) => ({ value: plan.code as string, label: plan.name }))}
            value={commercialPlanCode}
            onChange={onCommercialPlanCodeChange}
          />
        </Field>
      )}
      <p className="text-xs text-muted-foreground">
        The owner gets an email to set their own password and activate their account — you never
        see or set it here.
      </p>
    </div>
  );
}

const COMPANY_USER_ROLE_OPTIONS: { value: RoleName; label: string }[] = [
  { value: "Recruiter", label: "Recruiter" },
  { value: "Hiring Manager", label: "Hiring Manager" },
  { value: "Interviewer", label: "Interviewer" },
  { value: "TA Admin", label: "TA Admin" },
];

function CompanyUsersStep({ companyId }: { companyId: string }) {
  const invite = useAdminInviteCompanyUser(companyId);
  const [email, setEmail] = React.useState("");
  const [fullName, setFullName] = React.useState("");
  const [role, setRole] = React.useState<RoleName>("Recruiter");
  const [invited, setInvited] = React.useState<{ email: string; role: RoleName }[]>([]);

  const handleInvite = async () => {
    if (!email || !fullName) return;
    await invite.mutateAsync({ email, fullName, roleName: role });
    setInvited((prev) => [...prev, { email, role }]);
    setEmail("");
    setFullName("");
  };

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-muted-foreground">
        The Owner was already invited in the Create Account step. Invite any other initial
        teammates here — each gets an email to set their own password. This is optional; more
        people can be added later once the company is live.
      </p>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Full name" htmlFor="invite-full-name">
          <Input
            id="invite-full-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </Field>
        <Field label="Email" htmlFor="invite-email">
          <Input
            id="invite-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
      </div>
      <Field label="Role">
        <PillToggleGroup options={COMPANY_USER_ROLE_OPTIONS} value={role} onChange={setRole} />
      </Field>
      {invite.isError && (
        <p className="text-sm font-medium text-danger">
          Couldn&apos;t send that invite. Check the email and try again.
        </p>
      )}
      <Button
        type="button"
        variant="secondary"
        onClick={handleInvite}
        disabled={invite.isPending || !email || !fullName}
      >
        {invite.isPending ? "Inviting…" : "Invite"}
      </Button>
      {invited.length > 0 && (
        <div className="flex flex-col gap-1.5 rounded-xl border border-border bg-secondary/20 p-4">
          <p className="text-xs font-medium text-muted-foreground">Invited so far</p>
          {invited.map((u, index) => (
            <p key={`${u.email}-${index}`} className="text-sm text-foreground">
              {u.email} — {u.role}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

// Not a settings form -- see Company Onboarding Phase 1's plan: research confirmed there is no
// per-company knob anywhere in this mechanism (reveal requests, Passport visibility, the Shadow
// application freeze) to actually toggle. Showing a fake control here would repeat the exact
// fabricated-setting mistake this codebase has already caught and fixed twice before.
function IdentityProtectionStep({ companyName }: { companyName: string }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        This isn&apos;t a setting to configure — it&apos;s the same fixed mechanism for every
        company on Phantom, shown here so it&apos;s clear before activation.
      </p>
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-secondary/20 p-4">
        <h3 className="text-sm font-semibold text-foreground">
          How candidate identity stays protected
        </h3>
        <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
          <li>
            Candidates apply under an anonymous callsign — never a real name, email, or phone
            number.
          </li>
          <li>
            {companyName || "This company"}&apos;s team only ever sees a candidate&apos;s real
            identity once the candidate explicitly approves a Reveal Request.
          </li>
          <li>
            A candidate chooses exactly what to disclose when responding — Basic, Contact, Full,
            or a custom selection — their decision alone.
          </li>
          <li>
            This applies identically to every company and every plan; there is no setting that
            changes it.
          </li>
        </ul>
      </div>
    </div>
  );
}

function ReviewActivateStep({ company }: { company: Company }) {
  const activate = useAdminActivateCompany(company.id);
  const isLive = company.profile_status === "live";

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-muted-foreground">
        This is exactly what candidates will see once activated.
      </p>
      <CompanyProfilePreview company={toCompanyProfile(company)} />
      {isLive ? (
        <p className="text-sm font-medium text-success">This company&apos;s profile is live.</p>
      ) : (
        <>
          {activate.isError && (
            <p className="text-sm font-medium text-danger">Couldn&apos;t activate. Try again.</p>
          )}
          <Button
            type="button"
            variant="brand"
            onClick={() => activate.mutate()}
            disabled={activate.isPending}
          >
            {activate.isPending ? "Activating…" : "Activate company"}
          </Button>
        </>
      )}
    </div>
  );
}

export function CompanyOnboardingWizard() {
  const router = useRouter();
  const [activeStep, setActiveStep] = React.useState(0);
  const [companyId, setCompanyId] = React.useState<string | null>(null);

  const [companyName, setCompanyName] = React.useState("");
  const [ownerFullName, setOwnerFullName] = React.useState("");
  const [ownerEmail, setOwnerEmail] = React.useState("");
  const [commercialPlanCode, setCommercialPlanCode] = React.useState<string | null>("core");

  const [description, setDescription] = React.useState("");
  const [culture, setCulture] = React.useState("");
  const [benefits, setBenefits] = React.useState<string[]>([]);
  const [size, setSize] = React.useState<CompanySizeBand | null>(null);
  const [industry, setIndustry] = React.useState<string[]>([]);
  const [hiringProcessOverview, setHiringProcessOverview] = React.useState("");
  const [tagline, setTagline] = React.useState("");
  const [website, setWebsite] = React.useState("");
  const [foundedYear, setFoundedYear] = React.useState("");
  const [headquarters, setHeadquarters] = React.useState("");
  const [employeeCount, setEmployeeCount] = React.useState("");
  const [values, setValues] = React.useState<ContentItem[]>([]);
  const [lookingFor, setLookingFor] = React.useState<string[]>([]);
  const [hiringHighlights, setHiringHighlights] = React.useState<ContentItem[]>([]);
  const [loadedOnce, setLoadedOnce] = React.useState(false);

  const createCompany = useAdminCreateCompany();
  const { data: company } = useAdminCompanyProfile(companyId ?? undefined);
  const updateProfile = useAdminUpdateCompanyProfile(companyId ?? undefined);
  const uploadLogo = useAdminUploadLogo(companyId ?? undefined);
  const uploadCoverImage = useAdminUploadCoverImage(companyId ?? undefined);

  React.useEffect(() => {
    if (!company || loadedOnce) return;
    setDescription(company.description ?? "");
    setCulture(company.culture ?? "");
    setBenefits(company.benefits);
    setSize(company.size);
    setIndustry(company.industry);
    setHiringProcessOverview(company.hiring_process_overview ?? "");
    setTagline(company.tagline ?? "");
    setWebsite(company.website ?? "");
    setFoundedYear(company.founded_year !== null ? String(company.founded_year) : "");
    setHeadquarters(company.headquarters ?? "");
    setEmployeeCount(company.employee_count !== null ? String(company.employee_count) : "");
    setValues(company.values);
    setLookingFor(company.looking_for);
    setHiringHighlights(company.hiring_highlights);
    setLoadedOnce(true);
  }, [company, loadedOnce]);

  const goToStep = (index: number) => {
    setActiveStep(Math.max(0, Math.min(STEPS.length - 1, index)));
  };

  const handleCreateAccount = async (): Promise<boolean> => {
    if (companyId) return true;
    if (!companyName || !ownerFullName || !ownerEmail) return false;
    try {
      const created = await createCompany.mutateAsync({
        companyName,
        ownerFullName,
        ownerEmail,
        commercialPlanCode,
      });
      setCompanyId(created.id);
      return true;
    } catch {
      return false;
    }
  };

  const handleSaveProfile = async (): Promise<boolean> => {
    try {
      await updateProfile.mutateAsync({
        description: description || null,
        culture: culture || null,
        benefits,
        size,
        industry,
        hiring_process_overview: hiringProcessOverview || null,
        tagline: tagline || null,
        website: website || null,
        founded_year: foundedYear ? Number(foundedYear) : null,
        headquarters: headquarters || null,
        employee_count: employeeCount ? Number(employeeCount) : null,
        values,
        looking_for: lookingFor,
        hiring_highlights: hiringHighlights,
      });
      return true;
    } catch {
      return false;
    }
  };

  const handleContinue = async () => {
    let ok = true;
    if (activeStep === 0) ok = await handleCreateAccount();
    else if (activeStep >= 1 && activeStep <= 5) ok = await handleSaveProfile();
    if (!ok) return;
    goToStep(activeStep + 1);
  };

  const completedIndices = new Set<number>();
  if (companyId) completedIndices.add(0);
  if (company && (company.logo_url || size || industry.length > 0 || tagline)) {
    completedIndices.add(1);
  }
  if (description || culture) completedIndices.add(2);
  if (benefits.length > 0 || values.length > 0 || lookingFor.length > 0) completedIndices.add(3);
  if (company?.cover_image_url) completedIndices.add(4);
  if (hiringProcessOverview || hiringHighlights.length > 0) completedIndices.add(5);

  const isSaving = createCompany.isPending || updateProfile.isPending;
  const isLastStep = activeStep === STEPS.length - 1;
  const needsCompany = activeStep > 0 && !companyId;

  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border bg-background p-6 shadow-xl shadow-slate-900/5 sm:p-10">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          New Company Onboarding
        </h1>
        <p className="text-sm text-muted-foreground">
          Set up a company&apos;s account, plan, and initial Shadow profile before activating it.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[260px_1fr] md:items-start">
        <div className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-5 md:sticky md:top-24">
          <PassportStepRail
            steps={STEPS}
            activeIndex={activeStep}
            completedIndices={completedIndices}
            onStepClick={goToStep}
          />
        </div>

        <div className="flex flex-col gap-6">
          <div>
            {needsCompany || (activeStep > 0 && !loadedOnce && !company) ? (
              <div className="flex justify-center py-16">
                <Spinner className="h-6 w-6 text-muted-foreground" />
              </div>
            ) : (
              <>
                {activeStep === 0 && (
                  <CreateAccountStep
                    isCreated={!!companyId}
                    companyName={companyName}
                    onCompanyNameChange={setCompanyName}
                    ownerFullName={ownerFullName}
                    onOwnerFullNameChange={setOwnerFullName}
                    ownerEmail={ownerEmail}
                    onOwnerEmailChange={setOwnerEmail}
                    commercialPlanCode={commercialPlanCode}
                    onCommercialPlanCodeChange={setCommercialPlanCode}
                  />
                )}
                {activeStep === 1 && company && (
                  <IdentityStep
                    logoUrl={company.logo_url}
                    onUploadLogo={(file) => uploadLogo.mutate(file)}
                    isUploadingLogo={uploadLogo.isPending}
                    tagline={tagline}
                    onTaglineChange={setTagline}
                    website={website}
                    onWebsiteChange={setWebsite}
                    foundedYear={foundedYear}
                    onFoundedYearChange={setFoundedYear}
                    headquarters={headquarters}
                    onHeadquartersChange={setHeadquarters}
                    employeeCount={employeeCount}
                    onEmployeeCountChange={setEmployeeCount}
                    size={size}
                    onSizeChange={setSize}
                    industry={industry}
                    onIndustryChange={setIndustry}
                  />
                )}
                {activeStep === 2 && (
                  <AboutStep
                    description={description}
                    onDescriptionChange={setDescription}
                    culture={culture}
                    onCultureChange={setCulture}
                  />
                )}
                {activeStep === 3 && (
                  <EmployeeExperienceStep
                    values={values}
                    onValuesChange={setValues}
                    lookingFor={lookingFor}
                    onLookingForChange={setLookingFor}
                    benefits={benefits}
                    onBenefitsChange={setBenefits}
                  />
                )}
                {activeStep === 4 && company && (
                  <MediaStep
                    coverImageUrl={company.cover_image_url}
                    onUploadCoverImage={(file) => uploadCoverImage.mutate(file)}
                    isUploadingCoverImage={uploadCoverImage.isPending}
                  />
                )}
                {activeStep === 5 && (
                  <HiringProfileStep
                    hiringProcessOverview={hiringProcessOverview}
                    onHiringProcessOverviewChange={setHiringProcessOverview}
                    hiringHighlights={hiringHighlights}
                    onHiringHighlightsChange={setHiringHighlights}
                  />
                )}
                {activeStep === 6 && companyId && <CompanyUsersStep companyId={companyId} />}
                {activeStep === 7 && <IdentityProtectionStep companyName={companyName} />}
                {activeStep === 8 && company && <ReviewActivateStep company={company} />}
              </>
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
            {!isLastStep ? (
              <Button type="button" variant="brand" onClick={handleContinue} disabled={isSaving}>
                {isSaving ? "Saving…" : "Continue"} <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                type="button"
                variant="secondary"
                onClick={() => router.push("/platform-admin/companies")}
              >
                Done — back to Companies
              </Button>
            )}
          </div>
          {(createCompany.isError || updateProfile.isError) && (
            <p className="text-sm font-medium text-danger">
              Couldn&apos;t save. Check the details and try again.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
