"use client";

import * as React from "react";
import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateProject, useUploadJd } from "@/lib/queries/projects";
import type { JdUploadResult, Project } from "@/lib/types";

export function RoleInfoCard({ project }: { project: Project }) {
  const [preview, setPreview] = React.useState<JdUploadResult | null>(null);
  const [roleBrief, setRoleBrief] = React.useState(project.role_brief ?? "");
  const [seniority, setSeniority] = React.useState(project.seniority ?? "");
  const [location, setLocation] = React.useState(project.location ?? "");
  const [salaryMin, setSalaryMin] = React.useState(project.salary_min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = React.useState(project.salary_max?.toString() ?? "");
  const [isDirty, setIsDirty] = React.useState(false);

  const uploadJd = useUploadJd(project.id);
  const updateProject = useUpdateProject(project.id);

  // Only re-sync from the saved project when there's no pending, unsaved preview or manual
  // edit — otherwise a background refetch would silently overwrite what the recruiter is still
  // reviewing.
  React.useEffect(() => {
    if (!isDirty && !preview) {
      setRoleBrief(project.role_brief ?? "");
      setSeniority(project.seniority ?? "");
      setLocation(project.location ?? "");
      setSalaryMin(project.salary_min?.toString() ?? "");
      setSalaryMax(project.salary_max?.toString() ?? "");
    }
  }, [project, isDirty, preview]);

  const handleFile = (file: File) => {
    uploadJd.mutate(file, {
      onSuccess: (result) => {
        // Preview only -- nothing saved server-side yet. Populate the draft fields so the
        // recruiter can review/edit before an explicit Save.
        setPreview(result);
        setRoleBrief(result.role_brief);
        setSeniority(result.seniority ?? "");
        setLocation(result.location ?? "");
        setSalaryMin(result.salary_min?.toString() ?? "");
        setSalaryMax(result.salary_max?.toString() ?? "");
        setIsDirty(true);
      },
    });
  };

  const handleSave = () => {
    updateProject.mutate(
      {
        role_brief: roleBrief,
        seniority: seniority.trim() || null,
        location: location.trim() || null,
        salary_min: salaryMin.trim() ? Number(salaryMin) : null,
        salary_max: salaryMax.trim() ? Number(salaryMax) : null,
      },
      {
        onSuccess: () => {
          setIsDirty(false);
          setPreview(null);
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Role information</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Dropzone
          label="Drop the job description here"
          hint="PDF or DOCX — Phantom AI will extract seniority, location, and salary for you to review"
          accept=".pdf,.doc,.docx"
          isUploading={uploadJd.isPending}
          onFileSelected={handleFile}
        />
        {uploadJd.isError && (
          <p className="text-sm font-medium text-danger">
            Couldn&apos;t read that file. Try a PDF or DOCX.
          </p>
        )}
        {preview && (
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <Badge variant="outline">AI-suggested — review before saving</Badge>
          </div>
        )}
        <Textarea
          placeholder="Paste or edit the role brief here…"
          rows={8}
          value={roleBrief}
          onChange={(e) => {
            setRoleBrief(e.target.value);
            setIsDirty(true);
          }}
        />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Seniority" htmlFor="role-seniority">
            <Input
              id="role-seniority"
              placeholder="Senior"
              value={seniority}
              onChange={(e) => {
                setSeniority(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
          <Field label="Location" htmlFor="role-location">
            <Input
              id="role-location"
              placeholder="Remote (UK)"
              value={location}
              onChange={(e) => {
                setLocation(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Salary min" htmlFor="role-salary-min">
            <Input
              id="role-salary-min"
              type="number"
              placeholder="90000"
              value={salaryMin}
              onChange={(e) => {
                setSalaryMin(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
          <Field label="Salary max" htmlFor="role-salary-max">
            <Input
              id="role-salary-max"
              type="number"
              placeholder="110000"
              value={salaryMax}
              onChange={(e) => {
                setSalaryMax(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
        </div>
        <div className="flex justify-end">
          <Button
            size="sm"
            variant="secondary"
            onClick={handleSave}
            disabled={!isDirty || updateProject.isPending}
          >
            {updateProject.isPending ? "Saving…" : "Save role brief"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
