from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.candidate_auth.dependencies import (
    get_current_candidate,
    require_candidate_mfa_enrolled,
)
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidates.dependencies import get_file_storage
from app.modules.candidates.storage import FileStorage
from app.modules.phantom_passport.dependencies import get_llm_client
from app.modules.phantom_passport.llm_client import LLMClient
from app.modules.phantom_passport.schemas import (
    CvDocumentRead,
    CvParseResult,
    IndustriesSuggestionRequest,
    IndustriesSuggestionResponse,
    PassportRead,
    PassportUpdate,
    PassportVerificationRead,
    PassportVersionRead,
    SkillsSuggestionRequest,
    SkillsSuggestionResponse,
    SummaryImprovementRequest,
    SummaryImprovementResponse,
    VisibilityUpdate,
)
from app.modules.phantom_passport.service import PhantomPassportService

router = APIRouter(
    prefix="/phantom-passport",
    tags=["phantom-passport"],
    dependencies=[Depends(require_candidate_mfa_enrolled)],
)

public_router = APIRouter(prefix="/phantom-passport", tags=["phantom-passport"])


@public_router.get("/verify/{callsign}", response_model=PassportVerificationRead)
async def verify_passport(
    callsign: str, session: AsyncSession = Depends(get_db)
) -> PassportVerificationRead:
    result = await PhantomPassportService(session).get_verification_by_callsign(callsign)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passport not found")
    return result


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


@router.patch("/me/visibility", response_model=PassportRead)
async def update_my_passport_visibility(
    body: VisibilityUpdate,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> PassportRead:
    return await PhantomPassportService(session).update_visibility(
        candidate=candidate, visibility=body.visibility
    )


@router.post("/parse-cv", response_model=CvParseResult)
async def parse_cv(
    file: UploadFile = File(...),
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    storage: FileStorage = Depends(get_file_storage),
) -> CvParseResult:
    content = await file.read()
    return await PhantomPassportService(session, llm_client=llm_client, storage=storage).parse_cv(
        candidate=candidate,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "cv",
    )


@router.get("/original-cv", response_model=CvDocumentRead)
async def get_original_cv_status(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CvDocumentRead:
    return await PhantomPassportService(session).get_original_cv_status(candidate=candidate)


@router.get("/original-cv/download")
async def download_original_cv(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
) -> Response:
    content, content_type, filename = await PhantomPassportService(
        session, storage=storage
    ).download_original_cv(candidate=candidate)
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/original-cv", status_code=status.HTTP_204_NO_CONTENT)
async def delete_original_cv(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
) -> None:
    await PhantomPassportService(session, storage=storage).delete_original_cv(candidate=candidate)


@router.post("/me/approve", response_model=PassportVersionRead)
async def approve_my_passport(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> PassportVersionRead:
    return await PhantomPassportService(session).approve_passport(candidate=candidate)


@router.get("/versions", response_model=list[PassportVersionRead])
async def list_my_passport_versions(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> list[PassportVersionRead]:
    return await PhantomPassportService(session).list_versions(candidate=candidate)


@router.post("/suggest-summary", response_model=SummaryImprovementResponse)
async def suggest_summary(
    body: SummaryImprovementRequest,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> SummaryImprovementResponse:
    return await PhantomPassportService(session, llm_client=llm_client).suggest_summary_improvement(
        headline=body.headline, summary=body.summary, skills=body.skills
    )


@router.post("/suggest-skills", response_model=SkillsSuggestionResponse)
async def suggest_skills(
    body: SkillsSuggestionRequest,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> SkillsSuggestionResponse:
    return await PhantomPassportService(session, llm_client=llm_client).suggest_skills(
        headline=body.headline, summary=body.summary, existing_skills=body.existing_skills
    )


@router.post("/suggest-industries", response_model=IndustriesSuggestionResponse)
async def suggest_industries(
    body: IndustriesSuggestionRequest,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> IndustriesSuggestionResponse:
    return await PhantomPassportService(session, llm_client=llm_client).suggest_industries(
        headline=body.headline, summary=body.summary, existing_industries=body.existing_industries
    )
