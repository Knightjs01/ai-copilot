# Long-term, Admin+-visible record of what's already permanently gone. Two sources feed it:
#
# 1. PurgedProjectRecord (this module's own table) — a durable copy of each project's
#    PurgeCertificate, written by project_deletion.ProjectDeletionService.burn_project at the
#    moment of burn. The certificate itself (project_deletion.schemas.PurgeCertificate) is
#    otherwise ephemeral — returned once to the caller and never persisted anywhere else.
#
# 2. audit_logs (audit module) — already durable and already survives project/candidate
#    hard-deletes (AuditLog.target_id carries no FK constraint by design). This module is simply
#    the first place in the app that reads it back out; no schema change to the audit module was
#    needed.
#
# Gated to Owner + Admin via Permissions.HISTORIC_VAULT_VIEW — Member does not get read access to
# either purge records or the audit trail.
