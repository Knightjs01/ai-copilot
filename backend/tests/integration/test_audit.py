import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.helpers import auth_headers, signup


async def _fetch_one_audit_log_id(
    conn_engine: AsyncEngine, *, company_id: uuid.UUID, rls_subject: bool
) -> uuid.UUID:
    async with conn_engine.connect() as conn:
        async with conn.begin():
            if rls_subject:
                await conn.execute(text(f"SET LOCAL app.current_company_id = '{company_id}'"))
            row = await conn.execute(
                text("SELECT id FROM audit_logs WHERE company_id = :cid LIMIT 1"),
                {"cid": company_id},
            )
            return row.scalar_one()


async def _assert_mutation_rejected(
    conn_engine: AsyncEngine,
    *,
    sql: str,
    audit_log_id: uuid.UUID,
    company_id: uuid.UUID,
    rls_subject: bool,
    label: str,
) -> None:
    """Opens a brand-new connection per attempt — reusing one connection across a
    failed-then-retried transaction is its own SQLAlchemy async footgun unrelated to what this
    test is actually proving."""

    raised = False
    try:
        async with conn_engine.connect() as conn:
            async with conn.begin():
                if rls_subject:
                    await conn.execute(text(f"SET LOCAL app.current_company_id = '{company_id}'"))
                await conn.execute(text(sql), {"id": audit_log_id})
    except DBAPIError:
        raised = True
    assert raised, f"{label} should not be able to run: {sql}"


async def test_audit_logs_are_append_only_at_the_db_level(client: AsyncClient) -> None:
    """Proves audit_logs tamper-resistance is a real Postgres privilege, not just a code
    convention: even app_runtime — the role every authenticated request runs as — cannot UPDATE
    or DELETE an existing entry, only INSERT new ones and SELECT."""

    from app.db.base import auth_engine, engine

    owner = await signup(client, email="owner@audittamper.com", company_name="AuditTamper Co")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = uuid.UUID(me.json()["company_id"])

    for conn_engine, rls_subject, label in (
        (engine, True, "app_runtime"),
        (auth_engine, False, "app_auth"),
    ):
        audit_log_id = await _fetch_one_audit_log_id(
            conn_engine, company_id=company_id, rls_subject=rls_subject
        )
        await _assert_mutation_rejected(
            conn_engine,
            sql="UPDATE audit_logs SET action = 'tampered' WHERE id = :id",
            audit_log_id=audit_log_id,
            company_id=company_id,
            rls_subject=rls_subject,
            label=label,
        )
        await _assert_mutation_rejected(
            conn_engine,
            sql="DELETE FROM audit_logs WHERE id = :id",
            audit_log_id=audit_log_id,
            company_id=company_id,
            rls_subject=rls_subject,
            label=label,
        )
