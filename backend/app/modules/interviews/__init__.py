"""Interview scheduling, scoped to a single Shadow job application. A company schedules an
`Interview` against a `shadow_application_id`; the candidate sees it from their own "My
Interviews" list. An application can have multiple interviews (rounds) — no unique constraint.

Deliberately does NOT touch `Candidate.interview_scheduled_at` (the ATS pipeline's own bare
timestamp field) — `Candidate` (project-scoped) and `ShadowApplication`/`CandidateUser` (Shadow)
have no FK link anywhere in this codebase, so there is no way for a Shadow candidate to see
anything scheduled against an ATS `Candidate` row. This module is entirely new, keyed on
`shadow_application_id`, the only entity with both a company path and a candidate path in one
row — same reasoning as `messages`.

Structurally dual-audience like `messages`/`shadow_jobs`/`shadow_reveal`/`passport_matching`:
`Interview` carries a denormalized `company_id` for RLS on the company path, while the candidate
path always goes through `get_db` (bypasses RLS via `app_auth`) and is filtered explicitly by
`candidate_user_id` in the repository.

Candidate side is view-only this phase — the company always drives scheduling, same as it always
drives Reveal Requests.
"""
