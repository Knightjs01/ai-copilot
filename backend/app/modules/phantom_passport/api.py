from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.candidate_auth.dependencies import get_current_candidate
from app.modules.candidate_auth.models import CandidateUser
from app.modules.phantom_passport.dependencies import get_llm_client
from app.modules.phantom_passport.llm_client import LLMClient
from app.modules.phantom_passport.schemas import CvParseResult, PassportRead, PassportUpdate
from app.modules.phantom_passport.service import PhantomPassportService

router = APIRouter(prefix="/phantom-passport", tags=["phantom-passport"])


@router.get("/me", response_model=PassportRead)
async def get_my_passport(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> PassportRead:
    return await PhantomPassportService(session).get_passport(candidate=candidate)


@router.put("/me", response_model=PassportRead)
async def save_my_passport(
    body: PassportUpdate,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> PassportRead:
    return await PhantomPassportService(session).save_passport(candidate=candidate, body=body)


@router.post("/parse-cv", response_model=CvParseResult)
async def parse_cv(
    file: UploadFile = File(...),
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> CvParseResult:
    content = await file.read()
    return await PhantomPassportService(session, llm_client=llm_client).parse_cv(
        candidate=candidate,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
