"""Private, recruiter-team-only notes on a Shadow applicant. `ApplicantNote` rows are
company-scoped and immutable (append-only, no edit/delete) -- same convention as `Message`.

Deliberately company-only, unlike `messages`/`interviews`: a candidate never sees these, so
there is no candidate-path grant and no candidate-facing route at all, mirroring
`project_members`'/`interview_participants`' company-only shape rather than the dual-audience
pattern used by modules a candidate can also read from.
"""
