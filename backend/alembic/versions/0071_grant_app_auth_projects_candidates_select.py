"""Grant app_auth read access to projects and candidates.

Phantom Command 2.0 Phase 2 (Company Command Profile) calls CompanyService.get_profile_stats
from a platform-admin route for the first time -- that method reads ProjectRepository/
CandidateRepository counts, and both tables were only ever granted to app_runtime (the
RLS-scoped tenant runtime role), never to app_auth (the BYPASSRLS role platform-admin routes
use for cross-tenant reads, already granted full access to companies/shadow_jobs/etc. for
exactly this kind of admin lookup -- see migration 0017's own reasoning). SELECT-only, not the
full CRUD grant those other tables carry: no admin write path onto projects/candidates exists
today, and least-privilege is the safer default for a newly-added grant.

Revision ID: 0071
Revises: 0070
Create Date: 2026-09-03

"""

from alembic import op

revision: str = "0071"
down_revision: str | None = "0070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("GRANT SELECT ON projects TO app_auth")
    op.execute("GRANT SELECT ON candidates TO app_auth")


def downgrade() -> None:
    op.execute("REVOKE SELECT ON candidates FROM app_auth")
    op.execute("REVOKE SELECT ON projects FROM app_auth")
