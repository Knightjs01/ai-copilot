from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.candidate_auth.dependencies import require_candidate_mfa_enrolled
from app.modules.candidate_auth.models import CandidateUser
from app.modules.copilot.dependencies import get_copilot_llm_client
from app.modules.copilot.llm_client import CopilotLLMClient
from app.modules.copilot.schemas import CopilotChatRequest, CopilotChatResponse
from app.modules.copilot.service import CopilotService
from app.modules.passport_matching.dependencies import get_passport_matching_llm_client
from app.modules.passport_matching.llm_client import PassportMatchingLLMClient
from app.modules.phantom_passport.dependencies import (
    get_llm_client as get_phantom_passport_llm_client,
)
from app.modules.phantom_passport.llm_client import LLMClient as PhantomPassportLLMClient

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: CopilotChatRequest,
    candidate: CandidateUser = Depends(require_candidate_mfa_enrolled),
    session: AsyncSession = Depends(get_db),
    copilot_llm_client: CopilotLLMClient = Depends(get_copilot_llm_client),
    passport_matching_llm_client: PassportMatchingLLMClient = Depends(
        get_passport_matching_llm_client
    ),
    phantom_passport_llm_client: PhantomPassportLLMClient = Depends(
        get_phantom_passport_llm_client
    ),
) -> CopilotChatResponse:
    service = CopilotService(
        session,
        copilot_llm_client=copilot_llm_client,
        passport_matching_llm_client=passport_matching_llm_client,
        phantom_passport_llm_client=phantom_passport_llm_client,
    )
    return await service.chat(candidate=candidate, body=body)
