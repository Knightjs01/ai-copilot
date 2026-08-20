"use client";

import * as React from "react";
import { ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Spinner } from "@/components/ui/spinner";
import { TagInput } from "@/components/ui/tag-input";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth-context";
import { useMyCompany, useUpdateCompany } from "@/lib/queries/company";
import { COMPANY_SIZE_LABEL } from "@/lib/status-display";
import { useToast } from "@/lib/toast-context";
import type { CompanySizeBand } from "@/lib/types";

const SIZE_OPTIONS = (Object.keys(COMPANY_SIZE_LABEL) as CompanySizeBand[]).map((value) => ({
  value,
  label: COMPANY_SIZE_LABEL[value],
}));

export default function CompanyProfilePage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("company.manage_settings");
  const { data: company, isLoading } = useMyCompany();
  const updateCompany = useUpdateCompany();
  const toast = useToast();

  const [description, setDescription] = React.useState("");
  const [culture, setCulture] = React.useState("");
  const [benefits, setBenefits] = React.useState<string[]>([]);
  const [industry, setIndustry] = React.useState<string[]>([]);
  const [size, setSize] = React.useState<CompanySizeBand | null>(null);
  const [isPublic, setIsPublic] = React.useState(false);
  const [isDirty, setIsDirty] = React.useState(false);

  React.useEffect(() => {
    if (isDirty || !company) return;
    setDescription(company.description ?? "");
    setCulture(company.culture ?? "");
    setBenefits(company.benefits);
    setIndustry(company.industry);
    setSize(company.size);
    setIsPublic(company.is_profile_public);
  }, [company, isDirty]);

  if (!canManage) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">
          Company Profile isn&apos;t available on your role
        </p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or Admin on your team for access.
        </p>
      </div>
    );
  }

  if (isLoading || !company) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const handleSave = () => {
    updateCompany.mutate(
      {
        description: description || null,
        culture: culture || null,
        benefits,
        industry,
        size,
        is_profile_public: isPublic,
      },
      {
        onSuccess: () => {
          setIsDirty(false);
          toast({ title: "Company profile saved", variant: "success" });
        },
      }
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Company Profile</h1>
        <p className="text-sm text-muted-foreground">
          Tell candidates about {company.name}. Publish a public profile page they can view from
          your job listings.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Field label="Description" htmlFor="description">
            <Textarea
              id="description"
              rows={4}
              placeholder="What does your company do?"
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>

          <Field label="Culture" htmlFor="culture">
            <Textarea
              id="culture"
              rows={4}
              placeholder="What's it like to work there?"
              value={culture}
              onChange={(e) => {
                setCulture(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>

          <Field label="Benefits">
            <TagInput
              values={benefits}
              onValuesChange={(values) => {
                setBenefits(values);
                setIsDirty(true);
              }}
              placeholder="Add a benefit and press Enter"
            />
          </Field>

          <Field label="Industry">
            <TagInput
              values={industry}
              onValuesChange={(values) => {
                setIndustry(values);
                setIsDirty(true);
              }}
              placeholder="Add an industry and press Enter"
            />
          </Field>

          <Field label="Company size">
            <PillToggleGroup
              options={SIZE_OPTIONS}
              value={size}
              onChange={(value) => {
                setSize(value);
                setIsDirty(true);
              }}
            />
          </Field>

          <label className="flex items-start gap-2.5 rounded-xl border border-border bg-secondary/40 p-3.5">
            <input
              type="checkbox"
              className="mt-0.5 accent-brand"
              checked={isPublic}
              onChange={(e) => {
                setIsPublic(e.target.checked);
                setIsDirty(true);
              }}
            />
            <span className="flex flex-col gap-0.5">
              <span className="text-sm font-medium text-foreground">
                Publish a public profile page
              </span>
              <span className="text-xs text-muted-foreground">
                Candidates browsing your job listings can view this page. Your company name
                already appears on every listing regardless of this setting.
              </span>
            </span>
          </label>

          {updateCompany.isError && (
            <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
          )}

          <div className="flex justify-end">
            <Button size="sm" onClick={handleSave} disabled={!isDirty || updateCompany.isPending}>
              {updateCompany.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
