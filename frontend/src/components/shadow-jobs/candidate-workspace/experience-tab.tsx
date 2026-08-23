import { Briefcase } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { RevealedIdentity, ShadowProfile } from "@/lib/types";

export function ExperienceTab({
  profile,
  identity,
}: {
  profile: ShadowProfile;
  identity?: RevealedIdentity | null;
}) {
  const isRevealed = identity != null;
  const careerEntries = isRevealed
    ? identity.career_entries.map((entry) => ({
        title: entry.title,
        company: entry.company_name,
        isCurrent: entry.is_current,
      }))
    : profile.career_entries.map((entry) => ({
        title: entry.title,
        company: entry.company_name_anonymized,
        isCurrent: entry.is_current,
      }));

  return (
    <div className="flex flex-col gap-6">
      {(profile.headline || profile.seniority || profile.years_experience != null) && (
        <div className="flex flex-col gap-1">
          {profile.headline && (
            <p className="text-base font-medium text-foreground">{profile.headline}</p>
          )}
          <p className="text-sm text-muted-foreground">
            {[
              profile.seniority,
              profile.years_experience != null ? `${profile.years_experience} years experience` : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
      )}

      {profile.industries.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {profile.industries.map((industry) => (
            <Badge key={industry} variant="outline">
              {industry}
            </Badge>
          ))}
        </div>
      )}

      {profile.skills.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-foreground">Skills</h3>
          <div className="flex flex-wrap gap-1.5">
            {profile.skills.map((skill) => (
              <Badge key={skill} variant="neutral">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-medium text-foreground">Career history</h3>
        {careerEntries.length > 0 ? (
          <div className="flex flex-col gap-3 border-l border-border pl-4">
            {careerEntries.map((entry, i) => (
              <div key={i} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-brand" />
                <p className="text-sm font-medium text-foreground">{entry.title}</p>
                <p className="text-xs text-muted-foreground">
                  {entry.company}
                  {entry.isCurrent && (
                    <Badge variant="success" className="ml-1.5">
                      Current
                    </Badge>
                  )}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <Briefcase className="h-4 w-4" />
            No career history on this application.
          </div>
        )}
        <p className="text-xs text-muted-foreground">
          {isRevealed
            ? "This candidate approved your Reveal Request — real employer names are shown above."
            : "Employer names are anonymized until this candidate's identity is revealed."}
        </p>
      </div>
    </div>
  );
}
