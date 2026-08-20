"""Candidate <-> company messaging, scoped to a single Shadow job application. A thread is
created implicitly on whichever side sends first (`MessageThread`, unique per
`shadow_application_id`); `Message` rows are immutable, append-only.

"Company read" is shared team-wide (one `company_last_read_at` timestamp per thread, not one
per company User) -- no per-team-member read-state table exists anywhere else in this codebase
either, so this matches the rest of the Shadow applicant-visibility model rather than inventing
per-user state.

Structurally dual-audience like `shadow_jobs`/`shadow_reveal`/`passport_matching`: `MessageThread`
carries a denormalized `company_id` for RLS on the company path, while the candidate path always
goes through `get_db` (bypasses RLS via `app_auth`) and is filtered explicitly by
`candidate_user_id` in the repository.
"""
