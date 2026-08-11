"use client";

import * as React from "react";
import { Pencil } from "lucide-react";

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
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { useUpdateProject } from "@/lib/queries/projects";
import { useTeam } from "@/lib/queries/team";
import { PROJECT_STATUS_LABEL } from "@/lib/status-display";
import type { Project, ProjectStatus } from "@/lib/types";

const STATUS_OPTIONS = (Object.keys(PROJECT_STATUS_LABEL) as ProjectStatus[]).map((value) => ({
  value,
  label: PROJECT_STATUS_LABEL[value],
}));

export function EditProjectDialog({ project }: { project: Project }) {
  const [open, setOpen] = React.useState(false);
  const [title, setTitle] = React.useState(project.title);
  const [department, setDepartment] = React.useState(project.department ?? "");
  const [status, setStatus] = React.useState<ProjectStatus>(project.status);
  const [hiringManagerId, setHiringManagerId] = React.useState(project.hiring_manager_id ?? "");
  const updateProject = useUpdateProject(project.id);
  const { data: team } = useTeam();

  React.useEffect(() => {
    if (!open) return;
    setTitle(project.title);
    setDepartment(project.department ?? "");
    setStatus(project.status);
    setHiringManagerId(project.hiring_manager_id ?? "");
  }, [open, project]);

  const handleSave = () => {
    updateProject.mutate(
      {
        title,
        department: department || undefined,
        status,
        hiring_manager_id: hiringManagerId || null,
      },
      { onSuccess: () => setOpen(false) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="secondary" size="sm">
          <Pencil className="h-3.5 w-3.5" />
          Edit
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit project</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <Field label="Project name" htmlFor="projectTitle">
            <Input
              id="projectTitle"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </Field>
          <Field label="Department" htmlFor="projectDepartment">
            <Input
              id="projectDepartment"
              placeholder="e.g. Engineering"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            />
          </Field>
          <Field label="Status">
            <PillToggleGroup options={STATUS_OPTIONS} value={status} onChange={setStatus} />
          </Field>
          <Field label="Hiring manager" htmlFor="hiringManager">
            <select
              id="hiringManager"
              value={hiringManagerId}
              onChange={(e) => setHiringManagerId(e.target.value)}
              className="flex h-10 w-full rounded-xl border border-border bg-white px-3.5 text-sm text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
            >
              <option value="">Unassigned</option>
              {team?.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.full_name}
                </option>
              ))}
            </select>
          </Field>
          {updateProject.isError && (
            <p className="text-sm font-medium text-danger">
              Couldn&apos;t save. Try again.
            </p>
          )}
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
            disabled={updateProject.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSave}
            disabled={!title.trim() || updateProject.isPending}
          >
            {updateProject.isPending ? "Saving…" : "Save changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
