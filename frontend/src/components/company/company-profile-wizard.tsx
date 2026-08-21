"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { AboutStep } from "@/components/company/steps/about-step";
import { EmployeeExperienceStep } from "@/components/company/steps/employee-experience-step";
import { HiringProfileStep } from "@/components/company/steps/hiring-profile-step";
import { IdentityStep } from "@/components/company/steps/identity-step";
import { MediaStep } from "@/components/company/steps/media-step";
import { ReviewStep } from "@/components/company/steps/review-step";
import {
  PassportStepRail,
  type PassportWizardStep,
} from "@/components/candidate/passport-wizard/passport-step-rail";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  useMyCompany,
  useUpdateCompany,
  useUploadCoverImage,
  useUploadLogo,
} from "@/lib/queries/company";
import type { CompanySizeBand } from "@/lib/types";

const STEPS: PassportWizardStep[] = [
  { id: "identity", label: "Identity" },
  { id: "about", label: "About & Culture" },
  { id: "employee-experience", label: "Employee Experience" },
  { id: "media", label: "Brand Media" },
  { id: "hiring-profile", label: "Hiring Profile" },
  { id: "review", label: "Review & Submit" },
];

export function CompanyProfileWizard() {
  const { data: company, isLoading } = useMyCompany();
  const updateCompany = useUpdateCompany();
  const uploadLogo = useUploadLogo();
  const uploadCoverImage = useUploadCoverImage();

  const [activeStep, setActiveStep] = React.useState(0);
  const [loadedOnce, setLoadedOnce] = React.useState(false);

  const [description, setDescription] = React.useState("");
  const [culture, setCulture] = React.useState("");
  const [benefits, setBenefits] = React.useState<string[]>([]);
  const [size, setSize] = React.useState<CompanySizeBand | null>(null);
  const [industry, setIndustry] = React.useState<string[]>([]);
  const [hiringProcessOverview, setHiringProcessOverview] = React.useState("");

  React.useEffect(() => {
    if (!company || loadedOnce) return;
    setDescription(company.description ?? "");
    setCulture(company.culture ?? "");
    setBenefits(company.benefits);
    setSize(company.size);
    setIndustry(company.industry);
    setHiringProcessOverview(company.hiring_process_overview ?? "");
    setLoadedOnce(true);
  }, [company, loadedOnce]);

  const goToStep = (index: number) => {
    setActiveStep(Math.max(0, Math.min(STEPS.length - 1, index)));
  };

  const handleSave = async (): Promise<boolean> => {
    try {
      await updateCompany.mutateAsync({
        description: description || null,
        culture: culture || null,
        benefits,
        size,
        industry,
        hiring_process_overview: hiringProcessOverview || null,
      });
      return true;
    } catch {
      return false;
    }
  };

  const handleContinue = async () => {
    const ok = await handleSave();
    if (!ok) return;
    goToStep(activeStep + 1);
  };

  if (isLoading || !loadedOnce || !company) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const completedIndices = new Set<number>();
  if (company.logo_url || size || industry.length > 0) completedIndices.add(0);
  if (description || culture) completedIndices.add(1);
  if (benefits.length > 0) completedIndices.add(2);
  if (company.cover_image_url) completedIndices.add(3);
  if (hiringProcessOverview) completedIndices.add(4);

  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border bg-background p-6 shadow-xl shadow-slate-900/5 sm:p-10">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Company Profile
        </h1>
        <p className="text-sm text-muted-foreground">
          Build the profile candidates see once it&apos;s approved and live.
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
            {activeStep === 0 && (
              <IdentityStep
                logoUrl={company.logo_url}
                onUploadLogo={(file) => uploadLogo.mutate(file)}
                isUploadingLogo={uploadLogo.isPending}
                size={size}
                onSizeChange={setSize}
                industry={industry}
                onIndustryChange={setIndustry}
              />
            )}
            {activeStep === 1 && (
              <AboutStep
                description={description}
                onDescriptionChange={setDescription}
                culture={culture}
                onCultureChange={setCulture}
              />
            )}
            {activeStep === 2 && (
              <EmployeeExperienceStep benefits={benefits} onBenefitsChange={setBenefits} />
            )}
            {activeStep === 3 && (
              <MediaStep
                coverImageUrl={company.cover_image_url}
                onUploadCoverImage={(file) => uploadCoverImage.mutate(file)}
                isUploadingCoverImage={uploadCoverImage.isPending}
              />
            )}
            {activeStep === 4 && (
              <HiringProfileStep
                hiringProcessOverview={hiringProcessOverview}
                onHiringProcessOverviewChange={setHiringProcessOverview}
              />
            )}
            {activeStep === 5 && <ReviewStep profileStatus={company.profile_status} />}
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
            {activeStep < STEPS.length - 1 ? (
              <Button
                type="button"
                variant="brand"
                onClick={handleContinue}
                disabled={updateCompany.isPending}
              >
                {updateCompany.isPending ? "Saving…" : "Continue"}{" "}
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <div />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
