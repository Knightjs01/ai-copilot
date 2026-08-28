"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

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
import { useCreateProject } from "@/lib/queries/projects";

const schema = z.object({
  title: z.string().min(1, "Title is required"),
  department: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function NewProjectDialog({
  open: openProp,
  onOpenChange,
  hideTrigger,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  hideTrigger?: boolean;
} = {}) {
  const router = useRouter();
  const [internalOpen, setInternalOpen] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const open = openProp ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;
  const createProject = useCreateProject();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setFormError(null);
    try {
      const project = await createProject.mutateAsync({
        title: values.title,
        department: values.department || undefined,
      });
      reset();
      setOpen(false);
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Couldn't create that project.");
    }
  };

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) setFormError(null);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      {!hideTrigger && (
        <DialogTrigger asChild>
          <Button>
            <Plus className="h-4 w-4" />
            New project
          </Button>
        </DialogTrigger>
      )}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New hiring project</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <Field label="Role title" htmlFor="title" error={errors.title?.message}>
            <Input id="title" placeholder="Senior Backend Engineer" {...register("title")} />
          </Field>
          <Field label="Department" htmlFor="department">
            <Input id="department" placeholder="Engineering" {...register("department")} />
          </Field>
          {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleOpenChange(false)}
              disabled={createProject.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? "Creating…" : "Create project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
