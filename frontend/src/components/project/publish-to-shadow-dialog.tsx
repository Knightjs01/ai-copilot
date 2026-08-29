"use client";

import * as React from "react";
import { Rocket } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useHiringBlueprint } from "@/lib/queries/hiring-blueprint";
import { usePublishProjectToShadow } from "@/lib/queries/shadow-jobs";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type {
  EmploymentType,
  Project,
  RemotePreference,
  ShadowJob,
  ShadowJobCreateInput,
} from "@/lib/types";

const EMPLOYMENT_OPTIONS = Object.keys(EMPLOYMENT_TYPE_LABEL) as EmploymentType[];
const REMOTE_OPTIONS = Object.keys(REMOTE_PREFERENCE_LABEL) as RemotePreference[];

// One-time snapshot, per the rebuild's explicit decision: every open of this dialog re-derives
// its starting values from the CURRENT project/blueprint, never from the previously-published
// ShadowJob -- publishing (first time or a refresh) always means "copy what's true right now".
export function PublishToShadowDialog({
  project,
  existingShadowJob,
}: {
  project: Project;
  existingShadowJob: ShadowJob | null | undefined;
}) {
  const [open, setOpen] = React.useState(false);
  const { data: blueprint } = useHiringBlueprint(project.id);
  const publish = usePublishProjectToShadow(project.id);
  const container = useThemeScopeContainer();

  const [title, setTitle] = React.useState(project.title);
  const [department, setDepartment] = React.useState(project.department ?? "");
  const [seniority, setSeniority] = React.useState(project.seniority ?? "");
  const [location, setLocation] = React.useState(project.location ?? "");
  const [salaryMin, setSalaryMin] = React.useState(project.salary_min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = React.useState(project.salary_max?.toString() ?? "");
  const [employmentType, setEmploymentType] = React.useState<EmploymentType>("full_time");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | "none">(
    "none"
  );
  const [summary, setSummary] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [requirements, setRequirements] = React.useState("");

  React.useEffect(() => {
    if (!open) return;
    setTitle(project.title);
    setDepartment(project.department ?? "");
    setSeniority(project.seniority ?? "");
    setLocation(project.location ?? "");
    setSalaryMin(project.salary_min?.toString() ?? "");
    setSalaryMax(project.salary_max?.toString() ?? "");
    setEmploymentType("full_time");
    setRemotePreference("none");
    setSummary(blueprint?.role_summary ?? "");
    setDescription(project.role_brief ?? blueprint?.key_responsibilities.join("\n") ?? "");
    setRequirements(blueprint?.must_have_qualifications.join("\n") ?? "");
    // Deliberately re-runs whenever the dialog opens, not just when project/blueprint identity
    // changes -- re-opening to re-publish should always re-derive from current data.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const canPublish = title.trim() !== "" && summary.trim() !== "" && description.trim() !== "";

  const handlePublish = () => {
    const body: ShadowJobCreateInput = {
      title: title.trim(),
      department: department.trim() || null,
      seniority: seniority.trim() || null,
      employment_type: employmentType,
      location: location.trim() || null,
      remote_preference: remotePreference === "none" ? null : remotePreference,
      salary_min: salaryMin.trim() ? Number(salaryMin) : null,
      salary_max: salaryMax.trim() ? Number(salaryMax) : null,
      summary: summary.trim(),
      description: description.trim(),
      requirements: requirements
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
    };
    publish.mutate(body, { onSuccess: () => setOpen(false) });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="secondary" size="sm">
          <Rocket className="h-3.5 w-3.5" />
          {existingShadowJob ? "Resubmit for review" : "Submit for review"}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {existingShadowJob ? "Resubmit for review" : "Submit for review"}
          </DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            This copies a snapshot of the role and sends it to a Phantom admin for review. It
            won&apos;t appear on Shadow until approved — re-open this
            dialog any time to submit a fresh snapshot.
          </p>

          <Field label="Job title" htmlFor="shadowTitle">
            <Input id="shadowTitle" value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Department" htmlFor="shadowDepartment">
              <Input
                id="shadowDepartment"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              />
            </Field>
            <Field label="Seniority" htmlFor="shadowSeniority">
              <Input
                id="shadowSeniority"
                value={seniority}
                onChange={(e) => setSeniority(e.target.value)}
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Employment type">
              <Select
                value={employmentType}
                onValueChange={(value) => setEmploymentType(value as EmploymentType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent container={container}>
                  {EMPLOYMENT_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {EMPLOYMENT_TYPE_LABEL[option]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Remote preference">
              <Select
                value={remotePreference}
                onValueChange={(value) => setRemotePreference(value as RemotePreference | "none")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent container={container}>
                  <SelectItem value="none">Not specified</SelectItem>
                  {REMOTE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {REMOTE_PREFERENCE_LABEL[option]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Salary min" htmlFor="shadowSalaryMin">
              <Input
                id="shadowSalaryMin"
                type="number"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
              />
            </Field>
            <Field label="Salary max" htmlFor="shadowSalaryMax">
              <Input
                id="shadowSalaryMax"
                type="number"
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
              />
            </Field>
          </div>

          <Field label="Summary" htmlFor="shadowSummary">
            <Textarea
              id="shadowSummary"
              rows={2}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder={
                blueprint
                  ? undefined
                  : "No Hiring Blueprint generated yet — write a one-line summary for the board."
              }
            />
          </Field>

          <Field label="Description" htmlFor="shadowDescription">
            <Textarea
              id="shadowDescription"
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={
                project.role_brief || blueprint
                  ? undefined
                  : "No role brief or Hiring Blueprint yet — write a short description for candidates."
              }
            />
          </Field>

          <Field label="Requirements (one per line)" htmlFor="shadowRequirements">
            <Textarea
              id="shadowRequirements"
              rows={4}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
            />
          </Field>

          {!canPublish && (
            <p className="text-sm text-warning-foreground">
              A summary and description are required before publishing.
            </p>
          )}
          {publish.isError && (
            <p className="text-sm font-medium text-danger">Couldn&apos;t submit. Try again.</p>
          )}
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
            disabled={publish.isPending}
          >
            Cancel
          </Button>
          <Button type="button" onClick={handlePublish} disabled={!canPublish || publish.isPending}>
            {publish.isPending
              ? "Submitting…"
              : existingShadowJob
                ? "Resubmit for review"
                : "Submit for review"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
