"""Adversarial: cross-tenant IDOR checks for candidates/projects (task #211).

The plan for this file originally called for a defense-in-depth test that would strip away RLS
entirely (connect with no tenant context on a role that bypasses row security) and prove the
app-layer `CandidateService.get_candidate`/`ProjectService.get_project` `.company_id != company_id`
check alone still catches a cross-tenant read, independent of RLS.

That turned out not to be constructible for these two tables specifically, and the reason why is
itself a useful finding (write up for #212 rather than re-litigated here):
  - app_auth (the app's only BYPASSRLS role) has zero GRANTs on `candidates`/`projects` at all —
    deliberately never granted, see alembic/versions/0003_candidates.py and
    test_app_auth_role_has_no_grants_on_candidates in test_tenant_isolation.py. That's a stronger
    guarantee than RLS, but it means this role can't reach the app-layer check either — it's
    stopped a layer earlier, before RLS is even relevant.
  - Both tables also carry FORCE ROW LEVEL SECURITY (0001, 0003), which blocks even the
    table-owning migration role. The only connection Postgres still exempts unconditionally is a
    genuine superuser — deliberately not used here even for testing purposes, since minting a
    superuser-bypass code path is a meaningfully different risk than the property being tested.

Net effect: candidates/projects tenant isolation is defended by three independent layers (no
app_auth grant, FORCE RLS, and the app-layer check), and the first two are already strong enough
that the third is unreachable to exercise in isolation without a bypass this suite deliberately
declines to construct. What's left below is the API-level cross-tenant check, which *is*
meaningful — it's the one path a real attacker could actually attempt.
"""

from httpx import AsyncClient

from tests.integration.helpers import auth_headers, create_project, signup


async def test_cross_tenant_candidate_read_via_real_api_is_not_found(client: AsyncClient) -> None:
    owner_a = await signup(client, email="tenant-depth-api-a@acme.com")
    owner_b = await signup(client, email="tenant-depth-api-b@acme-b.com")

    project_b = await create_project(client, headers=auth_headers(owner_b["access_token"]))
    create_response = await client.post(
        "/api/v1/candidates",
        json={"project_id": project_b["id"], "full_name": "Company B Candidate"},
        headers=auth_headers(owner_b["access_token"]),
    )
    candidate_b_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/candidates/{candidate_b_id}", headers=auth_headers(owner_a["access_token"])
    )
    assert response.status_code == 404


async def test_cross_tenant_project_read_via_real_api_is_not_found(client: AsyncClient) -> None:
    owner_a = await signup(client, email="tenant-depth-api-proj-a@acme.com")
    owner_b = await signup(client, email="tenant-depth-api-proj-b@acme-b.com")

    project_b = await create_project(client, headers=auth_headers(owner_b["access_token"]))

    response = await client.get(
        f"/api/v1/projects/{project_b['id']}", headers=auth_headers(owner_a["access_token"])
    )
    assert response.status_code == 404
