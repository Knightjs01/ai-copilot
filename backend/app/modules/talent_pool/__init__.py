"""Talent Memory Phase 1: the permissioned Candidate <-> Company relationship. A company can ask
a Shadow Jobs applicant whether they may be kept on file for future roles once the current
process has run its course; the candidate can grant (choosing how broadly), decline, or later
withdraw that permission. This is structurally shadow_reveal with a different question ("may we
keep you on file" instead of "may we see your identity") and a different payload on approval (the
stable Passport callsign, not PII) — every pattern here mirrors that module.

Scoped to Shadow Jobs applicants only (real CandidateUser/PhantomPassport accounts) — the ATS
side's own Candidate model has no account and nobody to ask, same boundary Reveal Requests and
Messages already draw.

One row per request cycle (mirrors ShadowRevealRequest's append-only shape), not one mutable row
reused across withdraw/re-request — withdrawal and re-request are distinct audit events with
their own timestamps and possibly different source applications. A partial unique index (see
migration 0046) allows a fresh request after a decline or withdrawal, while blocking a duplicate
request while one is already requested/granted for the same (candidate, company) pair.

PhantomPassport.callsign is documented elsewhere as "never added to any company-facing schema" —
this module is the one, narrow, explicitly-consented exception: once a candidate has granted a
specific company an active grant, that same stable callsign is surfaced to that one company, and
only for a row whose status is currently "granted" (see TalentPoolService.list_company_talent_pool
and TalentPoolGrantRead). No third identifier system is introduced.

Not wired into project_deletion's purge cascade — a grant is scoped to (candidate, company), not
to a project, and must survive a project burn (matching how CandidateUser/PhantomPassport already
survive it). source_shadow_application_id is ON DELETE SET NULL instead; source_role_title is a
denormalized snapshot captured at request time so the human-readable context survives even after
the source application is purged.
"""
