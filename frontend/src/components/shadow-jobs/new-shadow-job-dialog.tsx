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
import { Textarea } from "@/components/ui/textarea";
import { useCreateShadowJob } from "@/lib/queries/shadow-jobs";

const schema = z.object({
  title: z.string().min(1, "Role title is required"),
  department: z.string().optional(),
  seniority: z.string().optional(),
  location: z.string().optional(),
  summary: z.string().min(1, "A short summary is required"),
  description: z.string().min(1, "A full description is required"),
});

type FormValues = z.infer<typeof schema>;

export function NewShadowJobDialog() {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const createJob = useCreateShadowJob();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    const job = await createJob.mutateAsync({
      title: values.title,
      department: values.department || undefined,
      seniority: values.seniority || undefined,
      location: values.location || undefined,
      summary: values.summary,
      description: values.description,
    });
    reset();
    setOpen(false);
    router.push(`/shadow-jobs/${job.id}`);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          Post a Shadow job
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Shadow job posting</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <Field label="Role title" htmlFor="title" error={errors.title?.message}>
            <Input id="title" placeholder="Staff Product Designer" {...register("title")} />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Department" htmlFor="department">
              <Input id="department" placeholder="Design" {...register("department")} />
            </Field>
            <Field label="Seniority" htmlFor="seniority">
              <Input id="seniority" placeholder="Staff" {...register("seniority")} />
            </Field>
          </div>
          <Field label="Location" htmlFor="location">
            <Input id="location" placeholder="Remote (UK)" {...register("location")} />
          </Field>
          <Field label="Summary" htmlFor="summary" error={errors.summary?.message}>
            <Textarea
              id="summary"
              placeholder="One or two sentences shown on the job board card."
              {...register("summary")}
            />
          </Field>
          <Field label="Full description" htmlFor="description" error={errors.description?.message}>
            <Textarea id="description" {...register("description")} />
          </Field>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setOpen(false)}
              disabled={createJob.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createJob.isPending}>
              {createJob.isPending ? "Creating…" : "Create draft"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
