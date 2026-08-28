from pydantic import BaseModel


class LocationSuggestion(BaseModel):
    formatted: str
    city: str | None
    country: str | None
    lat: float
    lon: float
