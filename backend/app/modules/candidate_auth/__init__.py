# Candidate identity — a principal deliberately separate from company Users (app.modules.auth).
#
# A company User belongs to exactly one company (company_id, RLS-enforced). A candidate belongs
# to no company at all: their Phantom Passport is theirs, built once, and applied across many
# companies' hiring projects — the opposite shape of multi-tenancy from everything else in this
# app. Giving candidates their own login here, rather than reusing auth.User, keeps that
# distinction structural instead of just conventional (no company_id column to accidentally
# leave null, no RLS policy that would need a company_id to compare against).
#
# Access tokens are minted by auth.security.create_candidate_access_token — same JWT/Fernet
# infrastructure as company auth, just a different payload shape (scope="candidate", no
# company_id). candidate_auth.dependencies.get_current_candidate checks that scope, so a company
# User's token can never be replayed against a candidate route and vice versa.
