"""Job Alerts: a candidate's saved search criteria on the Shadow job board, with an email
notification sent when a newly-published job matches.

Purely candidate-owned data — no company_id column, no RLS (same reasoning as
saved_shadow_jobs/phantom_passports). Every route runs on the app_auth connection (get_db) and
filters explicitly by candidate_user_id from the JWT.

No background/scheduled job runner exists anywhere in this codebase, and this module doesn't
introduce one — matching happens synchronously, in-process, at the one moment it actually
matters: when a company publishes a job (see shadow_jobs/api.py's publish_job route, which calls
JobAlertService.notify_matching_alerts right after ShadowJobService.publish_job succeeds). No
polling, no digest batching, no invented reliability guarantees beyond "if the publish request
succeeded, matching alert owners were emailed as part of that same request."
"""
