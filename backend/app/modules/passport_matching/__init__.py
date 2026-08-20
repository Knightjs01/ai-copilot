"""Phantom AI Matching Engine: forced-tool-call LLM scoring of a candidate's Phantom Passport
against a Shadow Job. Cached per (passport_version_id, shadow_job_id) pair — the passport side
is a true immutable version id, the job side is only as fresh as its own `updated_at`, so a
cached row is treated as stale (and recomputed) whenever the job's `updated_at` no longer
matches the value captured at scoring time.

Matching requires an approved Phantom Passport (`current_version_id` non-null) — there's no
valid cache key before that, so this is a hard precondition, not an edge case to special-case
around.
"""
