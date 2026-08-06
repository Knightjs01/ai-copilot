# The Candidate Identity Vault — the only place candidate PII (name, email, phone, location,
# current employer/title, LinkedIn) is ever stored. Everything outside this module (the Hiring
# Workspace: kanban, candidate detail page, analytics) works purely off a candidate's Callsign
# and Candidate ID. PII only ever leaves this module through reveal_identity(), which is
# permission-gated to Owner, requires a reason, and is audited via both an IdentityRevealEvent
# row and the shared AuditService.
#
# Export-to-ATS extension point (not implemented, deferred per product decision): when built, the
# mapping rule is candidate.callsign / candidate.candidate_ref -> CandidateIdentityVault's
# decrypted full_name, looked up by candidate_id, gated behind Permissions.IDENTITY_VAULT_REVEAL
# the same way reveal_identity() is. No export code should ever read raw vault ciphertext, or any
# vault field, outside this module.
