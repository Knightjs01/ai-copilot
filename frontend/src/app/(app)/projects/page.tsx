"use client";

import Link from "next/link";
import { Briefcase } from "lucide-react";

import { NewProjectDialog } from "@/components/new-project-dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useProjects } from "@/lib/queries/projects";

export default function ProjectsPage() {
  const { data: projects, isLoading } = useProjects();

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Hiring projects
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage pre-screen for every open role.
          </p>
        </div>
        <NewProjectDialog />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      ) : projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md hover:shadow-slate-900/[0.06]">
                <CardHeader>
                  <CardTitle>{project.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {project.department || "No department set"}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
          <Briefcase className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">No hiring projects yet</p>
          <p className="max-w-xs text-sm text-muted-foreground">
            Create your first project to start screening candidates.
          </p>
        </div>
      )}
    </div>
  );
}
