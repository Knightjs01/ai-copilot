"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateProject, useUploadJd } from "@/lib/queries/projects";
import type { Project } from "@/lib/types";

export function RoleInfoCard({ project }: { project: Project }) {
  const [draft, setDraft] = React.useState(project.role_brief ?? "");
  const [isDirty, setIsDirty] = React.useState(false);

  const uploadJd = useUploadJd(project.id);
  const updateProject = useUpdateProject(project.id);

  React.useEffect(() => {
    if (!isDirty) setDraft(project.role_brief ?? "");
  }, [project.role_brief, isDirty]);

  const handleFile = (file: File) => {
    uploadJd.mutate(file, {
      onSuccess: (updated) => {
        setDraft(updated.role_brief ?? "");
        setIsDirty(false);
      },
    });
  };

  const handleSave = () => {
    updateProject.mutate(
      { role_brief: draft },
      { onSuccess: () => setIsDirty(false) }
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
          hint="PDF or DOCX — we'll pull the role details out automatically"
          accept=".pdf,.doc,.docx"
          isUploading={uploadJd.isPending}
          onFileSelected={handleFile}
        />
        {uploadJd.isError && (
          <p className="text-sm font-medium text-danger">
            Couldn&apos;t read that file — try a PDF or DOCX.
          </p>
        )}
        <Textarea
          placeholder="Paste or edit the role brief here…"
          rows={8}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            setIsDirty(true);
          }}
        />
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
