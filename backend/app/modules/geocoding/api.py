from fastapi import APIRouter, Depends, Query

from app.modules.candidate_auth.dependencies import get_current_candidate
from app.modules.candidate_auth.models import CandidateUser
from app.modules.geocoding.schemas import LocationSuggestion
from app.modules.geocoding.service import GeocodingService

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


@router.get("/autocomplete", response_model=list[LocationSuggestion])
async def autocomplete(
    text: str = Query(min_length=1),
    _candidate: CandidateUser = Depends(get_current_candidate),
) -> list[LocationSuggestion]:
    return await GeocodingService().autocomplete(text)
