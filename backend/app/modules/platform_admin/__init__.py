"""Phantom internal staff — a third, wholly separate principal from company Users and
candidates. auth.models.User.company_id is NOT nullable, so a Phantom staff member structurally
cannot be represented as a User row: a platform admin belongs to no tenant at all. This module
mirrors the exact candidate_users/users split already established for the candidate principal
type (its own table, its own token scope, its own login route, its own dependency), applied here
for the same reason.

No RLS on platform_admins -- it isn't tenant-owned data, same reasoning as saved_shadow_jobs/
job_alerts. Runs on the existing get_db (app_auth, no-RLS) connection.

Phase 1 scope only: login + /me. No self-service password change, no MFA, no refresh tokens --
an expired session just means logging in again. A real, stated limitation, not an oversight; the
bootstrap credential seeded by migration 0040 should be rotated once proper account management
exists (a later phase)."""
