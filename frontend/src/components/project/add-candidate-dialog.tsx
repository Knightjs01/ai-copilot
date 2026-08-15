"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Dropzone } from "@/components/ui/dropzone";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";
import { useCreateCandidate } from "@/lib/queries/candidates";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";
import type { Candidate } from "@/lib/types";

const schema = z.object({
  fullName: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email").optional().or(z.literal("")),
  phone: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function AddCandidateDialog({ projectId }: { projectId: string }) {
  const [open, setOpen] = React.useState(false);
  const [resumeFile, setResumeFile] = React.useState<File | null>(null);
  const [isUploadingResume, setIsUploadingResume] = React.useState(false);
  const createCandidate = useCreateCandidate(projectId);
  const queryClient = useQueryClient();
  const themeScopeContainer = useThemeScopeContainer();
  const toast = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    const candidate = await createCandidate.mutateAsync({
      project_id: projectId,
      full_name: values.fullName,
      email: values.email || undefined,
      phone: values.phone || undefined,
    });
    // The candidate ID only exists once creation resolves, so this upload can't go through a
    // useUploadResume(candidateId) hook (which needs the ID up front) — call the client directly.
    if (resumeFile) {
      setIsUploadingResume(true);
      try {
        const formData = new FormData();
        formData.append("file", resumeFile);
        await apiClient.postForm<Candidate>(`/candidates/${candidate.id}/resume`, formData);
        void queryClient.invalidateQueries({ queryKey: ["candidates", { projectId }] });
      } finally {
        setIsUploadingResume(false);
      }
    }
    reset();
    setResumeFile(null);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-3.5 w-3.5" />
          Add candidate
        </Button>
      </DialogTrigger>
      <DialogContent container={themeScopeContainer}>
        <DialogHeader>
          <DialogTitle>Add a candidate</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <Field label="Full name" htmlFor="fullName" error={errors.fullName?.message}>
            <Input id="fullName" {...register("fullName")} />
          </Field>
          <Field label="Email" htmlFor="email" error={errors.email?.message}>
            <Input id="email" type="email" {...register("email")} />
          </Field>
          <Field label="Phone" htmlFor="phone">
            <Input id="phone" {...register("phone")} />
          </Field>
          <Field label="Resume (optional)">
            <Dropzone
              label="Drop a resume here"
              hint="PDF, DOC, or DOCX"
              currentFileName={resumeFile?.name}
              onFileSelected={setResumeFile}
            />
          </Field>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setOpen(false)}
              disabled={createCandidate.isPending || isUploadingResume}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createCandidate.isPending || isUploadingResume}>
              {createCandidate.isPending || isUploadingResume ? "Adding…" : "Add candidate"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
