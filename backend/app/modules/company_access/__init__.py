"""Employer access request queue -- the replacement for self-service company signup. A company
Owner account only ever comes into existence via CompanyAccessRequestService.approve_request,
called by a Phantom platform admin (see platform_admin/). There is no public route that creates
a Company directly anymore.

No RLS on company_access_requests -- it's pre-tenant data (no company exists yet when a request
is submitted), same reasoning as saved_shadow_jobs/job_alerts/platform_admins."""
