from httpx import AsyncClient
from sqlalchemy import text

from tests.integration.helpers import auth_headers, signup


async def test_rls_blocks_cross_tenant_reads_even_without_app_level_filter(
    client: AsyncClient,
) -> None:
    """The `users` list endpoint already filters by company_id in its own query, so it alone
    wouldn't prove RLS is doing anything. This test deliberately bypasses that filter — querying
    with no company predicate at all, and even explicitly asking for the other company's id — to
    prove the database itself, not just app code, is what blocks cross-tenant access."""

    from app.db.base import engine

    company_a = await signup(client, email="a-owner@rls.com", company_name="RLS Co A")
    company_b = await signup(client, email="b-owner@rls.com", company_name="RLS Co B")

    me_a = await client.get("/api/v1/auth/me", headers=auth_headers(company_a["access_token"]))
    me_b = await client.get("/api/v1/auth/me", headers=auth_headers(company_b["access_token"]))
    company_a_id = me_a.json()["company_id"]
    company_b_id = me_b.json()["company_id"]

    async with engine.connect() as conn:
        async with conn.begin():
            # SET LOCAL doesn't accept bind parameters — see the same note in
            # app/modules/auth/dependencies.py. company_a_id came from our own /auth/me JSON, but
            # validate as a UUID anyway before interpolating, same reasoning as that code.
            import uuid as uuid_module

            await conn.execute(
                text(f"SET LOCAL app.current_company_id = '{uuid_module.UUID(company_a_id)}'")
            )

            all_visible = await conn.execute(text("SELECT company_id FROM users"))
            visible_company_ids = [str(row[0]) for row in all_visible.fetchall()]
            assert visible_company_ids, "sanity check: company A should see its own user"
            assert all(cid == company_a_id for cid in visible_company_ids)

            explicit_cross_tenant_query = await conn.execute(
                text("SELECT id FROM users WHERE company_id = :cid"), {"cid": company_b_id}
            )
            assert explicit_cross_tenant_query.fetchall() == []


async def test_rls_fails_closed_when_no_tenant_context_is_set(client: AsyncClient) -> None:
    from app.db.base import engine

    await signup(client, email="fail-closed@rls.com")

    async with engine.connect() as conn:
        async with conn.begin():
            # No SET LOCAL app.current_company_id at all — should see nothing, not everything.
            result = await conn.execute(text("SELECT id FROM users"))
            assert result.fetchall() == []
