# Security: Threat Model & Production Checklist

This document covers what's actually implemented on `security/zero-trust-overhaul`, why, and
what's still open before a real production launch. It's written from the code, not from intent —
every claim below has a file reference. Where something is a deliberate design tradeoff rather
than a gap, it's called out as such; don't "fix" those without reading the reasoning first.

Two principals exist and are kept fully separate throughout: **company Users** (recruiters/admins,
tenant-scoped) and **CandidateUsers** (job seekers, never tenant-scoped). Most sections below cover
both.

---

## 1. Assets & trust boundaries

**What we're protecting:**
- Candidate PII (name, email, phone, employer, salary, LinkedIn) — encrypted at rest, disclosed
  only through audited reveal flows.
- Resumes/CVs — encrypted at rest, contain the same PII plus work history.
- Company tenant data (projects, hiring pipelines, AI-generated assessments) — must never leak
  across companies.
- Credentials (passwords, MFA secrets, WebAuthn credentials, session tokens).
- Audit trail integrity — the record of who saw what, when.

**Trust boundaries:**
- Browser ↔ API (untrusted network, untrusted client — the browser is assumed hostile).
- Company A ↔ Company B (tenant isolation — the core multi-tenant guarantee).
- Company recruiter ↔ candidate PII (a recruiter's default view is de-identified; seeing real PII
  is a deliberate, audited action, not the default read path).
- `app_auth` DB role (pre-authentication flows) ↔ `app_runtime` DB role (authenticated, tenant-set
  queries) — separated at the database grant level, not just in application code.

---

## 2. Tenant isolation

Three independent layers protect `candidates` and `projects`, deliberately redundant:

1. **No DB grant.** The `app_auth` Postgres role (used only for login/signup/refresh/reset, before
   a tenant is known) has zero `SELECT`/`INSERT`/etc. privileges on `candidates` — not merely RLS,
   an outright missing grant (`backend/alembic/versions/0003_candidates.py`). Confirmed by
   `test_app_auth_role_has_no_grants_on_candidates`.
2. **Row-Level Security.** Every tenant-owned table (`users`, `projects`, `candidates`, `roles`,
   `audit_logs`, `role_permissions`/`user_roles` via subquery, `mfa_backup_codes`,
   `webauthn_credentials`) has `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` + a policy
   scoped to `current_setting('app.current_company_id', true)::uuid`. The global `permissions`
   catalog table is intentionally excluded (it's not tenant data). `SET LOCAL app.current_company_id`
   runs once per request in `auth/dependencies.py:get_tenant_db`, after validating the claim parses
   as a UUID (so it's safe to interpolate into the literal `SET LOCAL` statement — Postgres doesn't
   accept bind params there).
3. **Application-layer re-check.** `CandidateService.get_candidate` and `ProjectService.get_project`
   independently compare `row.company_id != company_id` and raise not-found, regardless of what RLS
   already did.

`refresh_tokens` is the one notable exception: **no RLS, no `company_id` column at all.** Isolation
between two users at the same company relies entirely on `AuthService.revoke_session` filtering by
`user_id` — confirmed by `test_company_user_cannot_revoke_a_same_company_colleagues_session`. This
is a real single-layer dependency, not redundant like the rest of the schema; keep it in mind if
that filter is ever refactored.

---

## 3. Authentication & session lifecycle

- **JWT:** HS256, one shared `SECRET_KEY`. Company access tokens carry `sub`, `company_id`, `jti`;
  candidate access tokens carry `sub`, `scope: "candidate"` (no `company_id` — `get_tenant_db`
  rejects any token missing it, so a candidate token can never reach a company route). Both expire
  in **15 minutes**.
- **Refresh tokens:** opaque (`secrets.token_urlsafe(48)`), stored only as a SHA-256 hash, 30-day
  lifetime, rotated on every use. **Reuse of an already-rotated token is treated as theft** — it
  revokes every refresh token for that user, including the legitimate client's already-rotated-forward
  session (`AuthService.refresh`, `test_reused_refresh_token_revokes_the_legitimately_rotated_session_too`).
  The revocation commits immediately, before the `InvalidOrExpiredTokenError` is raised, so it can't
  be lost to a rolled-back transaction.
- **Refresh cookie:** `httponly`, `secure` when `COOKIE_SECURE=true`, scoped to `/api/v1/auth`.
- **Access tokens are not revocable before natural expiry — by design, not a gap.** Logout, a
  specific-session revoke, and password reset all kill the *refresh* token; the access token already
  issued keeps working for up to 15 more minutes regardless. This is deliberately pinned by
  `tests/integration/test_access_token_revocation_semantics.py` so it isn't accidentally "fixed"
  later without a conscious decision (adding a blacklist means a DB/Redis lookup on every request —
  a real tradeoff, not an oversight).

---

## 4. MFA & step-up

- **Mandatory MFA with a 7-day grace period** (`settings.mfa_grace_period_days`), enforced via
  `require_mfa_enrolled` at router level on nearly every business route — deliberately *not*
  applied to `/auth/me` or `/auth/mfa/*`, so an expired-grace account can't be locked out of the
  one path that clears the gate. A registered WebAuthn credential also satisfies the requirement
  on its own (possession + biometric/PIN is treated as inherently two-factor).
- **TOTP + 10 single-use backup codes** per account, codes formatted `XXXXX-XXXXX` from an
  ambiguity-free alphabet, stored as SHA-256 hashes, shown in plaintext exactly once at generation.
  Full parity on the candidate side (`CandidateMfaBackupCode`, same mechanism, no RLS since
  candidates aren't tenant-scoped).
- **Step-up (`require_step_up`)** — a separate 5-minute-lived, single-purpose token (`scope:
  "step_up"`, sent via `X-Step-Up-Token`, not `Authorization`) proving a fresh password + MFA
  re-check. Currently gates:
  - `POST /auth/invite`
  - `POST /identity-vault/candidates/{id}/reveal`
  - `POST /projects/{id}/burn`
  - `GET /shadow-reveal/mine/{job}/applicants/{app}` (reading a revealed identity)

  **`remove_user` and `change_user_role` are only `require_mfa_enrolled`-gated, not step-up.**
  That's an asymmetry against the other high-risk actions above — worth a deliberate decision
  before launch (see checklist).
- **WebAuthn/passkeys:** fully implemented on the backend for both principals (registration,
  credential list/delete, authentication ceremonies) — `backend/app/core/webauthn.py` +
  per-principal endpoints. **There is no frontend UI for it anywhere** — a real gap between what
  the API supports and what a user can actually do today.

---

## 5. Rate limiting & brute force

- **Per-IP (slowapi + Redis):** `5/minute` on login/signup-shaped endpoints, `10/minute` on most
  auth actions, `30/minute` on read endpoints like `/auth/me`. Globally disabled when
  `ENVIRONMENT=test`.
- **Per-account (`LoginAttemptTracker`):** keyed by SHA-256 of the lowercased email, not IP —
  specifically to catch credential stuffing spread across many source addresses. 15 failures in a
  rolling 15-minute Redis-expiring window; **deliberately not a hard/permanent lock**, because a
  permanent lock triggered by failed attempts is itself a denial-of-service vector against a known
  victim email. A throttled response is indistinguishable from an ordinary wrong-password response.
  Company and candidate realms are tracked separately even for the same email string.

---

## 6. Encryption at rest

- **Fernet** (AES-128-CBC + HMAC-SHA256), one key, sourced from the `ENCRYPTION_KEY` env var via
  `StaticEnvKeyProvider`.
- Encrypts: MFA TOTP secrets, every Identity Vault PII field (name/email/phone/location/
  employer/title/LinkedIn), and resume/CV file bytes (`EncryptingFileStorage` wraps whatever
  `FileStorage` backend is configured — currently local-filesystem only).
- **`KeyProvider` is an intentional stub, not a KMS integration.** One static key, no rotation, no
  envelope encryption. The interface (`current_key_id()`/`get_key()`) is shaped for a future real
  KMS provider, but none is wired up. Do not treat this as "encryption is handled" in a production
  risk assessment — it's encryption without key rotation or a hardware-backed root of trust.
- **Local-filesystem storage is explicitly not fit for horizontal scaling** — a Railway Volume (or
  equivalent) is required per the deployment doc; swap for S3 before running more than one backend
  instance.

---

## 7. Audit logging

- Append-only `audit_logs` table: `company_id`, `actor_user_id`, `action`, `target_type`,
  `target_id`, `extra_data` (JSONB), `created_at`. Dozens of call sites across every module —
  login (including which MFA method), password/MFA changes, step-up verification, WebAuthn
  changes, session revocation, identity reveals, project purges.
- **Tamper resistance is enforced at the database grant level, not by hash-chaining or signing.**
  `UPDATE`/`DELETE` on `audit_logs` are revoked from both `app_runtime` and `app_auth` — even a
  fully compromised application connection can only `INSERT`/`SELECT`. Confirmed by
  `test_audit_logs_are_append_only_at_the_db_level`, which attempts a raw `UPDATE` and expects it
  to fail at the database. There is no cryptographic hash chain and no external WORM store — if a
  compliance requirement later demands tamper-evidence independent of database privileges (e.g. for
  a regulator who doesn't trust "we revoked the GRANT"), that's additional work, not already done.

---

## 8. Identity disclosure (Identity Vault & Shadow reveal)

A shared `DisclosureLevel` enum (`BASIC` → `CONTACT` → `FULL`, each a strict superset) gates two
different reveal flows:

- **Identity Vault** (company-Owner-initiated): `require_step_up` + `IDENTITY_VAULT_REVEAL`
  permission. Every reveal writes both an `IdentityRevealEvent` row (reason, disclosure level, IP,
  duration) and an `audit_logs` entry, synchronously, before returning any decrypted data.
- **Shadow reveal** (candidate-consented, for Shadow Jobs applicants): two-sided — the company
  *requests* disclosure (MFA-gated only), the candidate *approves or declines* it (candidate-side
  MFA-gated), and only the subsequent *read* of the approved data is step-up gated. The request step
  itself isn't step-up gated — worth confirming that's intentional (a request alone reveals nothing,
  so it's lower-risk than the read, but it does notify/prompt a candidate).

---

## 9. Data retention & purge ("burn")

`ProjectDeletionService.burn_project` is a real hard delete, distinct from the soft-delete used
elsewhere. Cascade order: storage files → sanitized profiles → intelligence packs → prescreen
assessments → identity vault + reveal events → candidates → blueprint/alignment/membership →
(if linked) Shadow reveal requests → Shadow applications → Shadow job → an audit entry (written
before the project row dies, with no FK on `target_id` so it survives regardless) → a durable
`historic_vault` record → the project row itself, last.

**`PurgeCertificate` is a plain structured record, not a cryptographic proof.** No signature, hash,
or external attestation — it's a Pydantic model returned once at burn time, with an equally
unsigned durable copy in `historic_vault`. If "certificate" needs to mean something a third party
can verify independently later (e.g. for a data-subject deletion request audit), that's future work.

Gated by `require_mfa_enrolled` + `require_step_up` + `PROJECTS_DELETE` permission.

---

## 10. Transport & headers

- **Security headers** (`SecurityHeadersMiddleware`, applied first): `X-Content-Type-Options:
  nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`,
  `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`,
  `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'` (exempted
  on `/api/docs`, `/api/openapi.json`, `/api/redoc` so Swagger's CDN assets still load).
  `Strict-Transport-Security` (`max-age=63072000; includeSubDomains; preload`) is gated on the same
  `COOKIE_SECURE` flag as the cookie's own `Secure` attribute — off in local HTTP dev, on once
  actually served over HTTPS. **Confirm `COOKIE_SECURE=true` is set in production** — if it's
  forgotten, both the cookie and HSTS silently stay in their permissive dev state.
- **CORS:** explicit origin allowlist from `CORS_ORIGINS`, `allow_credentials=True`, explicit method
  and header allowlists (no wildcards).

---

## 11. Known accepted risks (do not "fix" without a deliberate decision)

| # | Risk | Why it's accepted |
|---|---|---|
| 1 | Access tokens usable up to 15 min after logout/revoke/password-reset | Stateless JWT tradeoff; a blacklist means a lookup on every request. Pinned by tests. |
| 2 | Login throttle is a rolling window, not a permanent lock | A permanent lock is itself a DoS vector against a known victim email. |
| 3 | `refresh_tokens` has no RLS/DB-level isolation | Single application-layer filter (`user_id`) is the only backstop — real, not redundant. |
| 4 | `KeyProvider` is one static key, no rotation, no KMS | No KMS provisioned yet; interface is shaped for one but nothing is wired up. |
| 5 | File storage is local-filesystem only | Fine for one instance; not for horizontal scaling. |
| 6 | `PurgeCertificate` isn't cryptographically verifiable | Plain record today; no external attestation. |

## 12. Real gaps (not accepted risks — just not done yet)

- **No WebAuthn/passkey UI on the frontend**, despite full backend support for both principals.
- **`remove_user`/`change_user_role` aren't step-up gated**, unlike invite/reveal/purge — decide
  deliberately whether that's intentional before launch.
- **Shadow reveal's *request* step isn't step-up gated** (only the later read of an approved
  disclosure is) — confirm that's the intended risk level.
- No external-facing threat modeling for the AI/LLM surface itself (prompt injection via uploaded
  resumes/JDs into the intelligence/hiring-blueprint/prescreen modules) — out of scope for this
  pass, worth a dedicated review before relying on AI-generated content for hiring decisions.

---

## 13. Production launch checklist

Environment/secrets (see `DEPLOYMENT.md` for the full walkthrough):
- [ ] Fresh `SECRET_KEY`, `ENCRYPTION_KEY`, DB passwords generated for production — never reused
      from local `.env`.
- [ ] `ENVIRONMENT=production` (not `test` — this is what re-enables both rate limiters).
- [ ] `COOKIE_SECURE=true` (this also turns on HSTS — see §10).
- [ ] `CORS_ORIGINS` set to the real production frontend origin(s) only.
- [ ] A persistent volume mounted for resume/CV storage, or migrate to S3-backed storage first.
- [ ] Redis reachable and persistent (both rate limiters and login throttling depend on it — if
      Redis is unavailable at boot, confirm the failure mode is fail-closed, not silently disabled).

Decisions to make deliberately, not by default:
- [ ] Decide whether `remove_user`/`change_user_role` should be step-up gated (§4).
- [ ] Decide whether Shadow reveal's request step needs step-up (§8).
- [ ] Decide whether a real KMS (envelope encryption, key rotation) is needed before handling real
      candidate PII at scale, or whether the static-key Fernet setup is an accepted interim risk
      with a tracked follow-up (§6, §11.4).
- [ ] Decide whether `PurgeCertificate` needs to become independently verifiable for compliance
      purposes (§9, §11.6).
- [ ] Decide whether WebAuthn/passkeys ship in the UI before launch or stay backend-only for now
      (§4, §12).

Verification before go-live:
- [ ] Run the full adversarial test suite (`backend/tests/integration/test_token_forgery.py`,
      `test_shadow_cross_principal_confusion.py`, `test_tenant_boundary_defense_in_depth.py`,
      `test_refresh_token_security.py`, `test_storage_encryption_coverage.py`,
      `test_access_token_revocation_semantics.py`) against the production-shaped environment
      (real Postgres/Redis, `ENVIRONMENT` unset from `test`) — not just against local dev.
  - [ ] Confirm HSTS and CSP headers are actually present on a live HTTPS response (not just in
      code) — `curl -D -` the deployed origin.
  - [ ] Confirm `app_auth` genuinely cannot read `candidates`/`projects` against the production
      database (the grants are set by migration, but production DB provisioning can drift from
      what a migration assumes — verify directly).
  - [ ] Rotate `SECRET_KEY`/`ENCRYPTION_KEY` if either was ever committed, logged, or shared over
      an insecure channel during development.
