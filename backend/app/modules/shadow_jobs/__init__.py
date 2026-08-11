"""Shadow: the anonymous job board. Two audiences share this module:

- Companies post/manage ShadowJob listings and review applicants, always through the
  RLS-enforced app_runtime connection (get_tenant_db) — identical tenant isolation to every
  other company-owned resource in this codebase.
- Candidates browse the public board and apply with their Phantom Passport through the
  app_auth connection (get_db), same as every other candidate_auth/phantom_passport route.
  ShadowJob and ShadowApplication both carry company_id and an RLS policy for the company
  side, but app_auth is BYPASSRLS — candidate-facing queries in this module never rely on
  that policy for correctness, they filter explicitly by candidate_user_id from the JWT.

The applicant-facing "Shadow Profile" returned to a company (see schemas.ShadowProfile) is
built by reusing phantom_passport's PhantomPassportRepository and PassportCareerEntryRepository
directly — this module never imports PassportPersonalInfoRepository or PassportPersonalInfo at
all, so it is structurally incapable of leaking a candidate's legal name, phone, or address into
a recruiter-facing response, the same schema-level guarantee phantom_passport itself relies on.

Deferred, not built here: Reveal Request workflow (an application's status can reach
"reveal_requested" but nothing yet transitions it to "revealed" or lets a candidate decline),
AI matching/ranking, recruiter AI copilot, and Employer Protection blocklists. ShadowApplication
status is a plain string column so those can layer on without a schema change.
"""
