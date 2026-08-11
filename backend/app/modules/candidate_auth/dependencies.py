import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth import security
from app.modules.auth.dependencies import get_bearer_token
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import CandidateUserRepository


async def get_candidate_token_payload(
    token: str = Depends(get_bearer_token),
) -> dict[str, Any]:
    try:
        payload = security.decode_access_token(token)
    except security.TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc
    if payload.get("scope") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return payload


async def get_current_candidate(
    payload: dict[str, Any] = Depends(get_candidate_token_payload),
    # Candidates have no company_id, so there's no tenant to scope RLS by — every candidate
    # route runs on the same app_auth (BYPASSRLS) connection as pre-tenant company auth flows,
    # and authorization is enforced purely at the application layer: every query below is
    # explicitly filtered by the candidate's own id from the token, never taken from the URL.
    session: AsyncSession = Depends(get_db),
) -> CandidateUser:
    candidate = await CandidateUserRepository(session).get_by_id(uuid.UUID(payload["sub"]))
    if candidate is None or not candidate.is_active or candidate.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return candidate
