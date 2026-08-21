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
  const [seniority, setSeniority] = React.useState(project.seniority ?? "");
  const [location, setLocation] = React.useState(project.location ?? "");
  const [salaryMin, setSalaryMin] = React.useState(project.salary_min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = React.useState(project.salary_max?.toString() ?? "");
  const updateProject = useUpdateProject(project.id);
  const { data: team } = useTeam();

  React.useEffect(() => {
    if (!open) return;
    setTitle(project.title);
    setDepartment(project.department ?? "");
    setStatus(project.status);
    setHiringManagerId(project.hiring_manager_id ?? "");
    setSeniority(project.seniority ?? "");
    setLocation(project.location ?? "");
    setSalaryMin(project.salary_min?.toString() ?? "");
    setSalaryMax(project.salary_max?.toString() ?? "");
  }, [open, project]);

  const handleSave = () => {
    updateProject.mutate(
      {
        title,
        department: department || undefined,
        status,
        hiring_manager_id: hiringManagerId || null,
        seniority: seniority.trim() || null,
        location: location.trim() || null,
        salary_min: salaryMin.trim() ? Number(salaryMin) : null,
        salary_max: salaryMax.trim() ? Number(salaryMax) : null,
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
          <div className="grid grid-cols-2 gap-4">
            <Field label="Seniority" htmlFor="projectSeniority">
              <Input
                id="projectSeniority"
                placeholder="Senior"
                value={seniority}
                onChange={(e) => setSeniority(e.target.value)}
              />
            </Field>
            <Field label="Location" htmlFor="projectLocation">
              <Input
                id="projectLocation"
                placeholder="Remote (UK)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Salary min" htmlFor="projectSalaryMin">
              <Input
                id="projectSalaryMin"
                type="number"
                placeholder="90000"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value)}
              />
            </Field>
            <Field label="Salary max" htmlFor="projectSalaryMax">
              <Input
                id="projectSalaryMax"
                type="number"
                placeholder="110000"
                value={salaryMax}
                onChange={(e) => setSalaryMax(e.target.value)}
              />
            </Field>
          </div>
          <Field label="Hiring manager" htmlFor="hiringManager">
            <select
              id="hiringManager"
              value={hiringManagerId}
              onChange={(e) => setHiringManagerId(e.target.value)}
              className="flex h-10 w-full rounded-xl border border-border bg-card px-3.5 text-sm text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
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
