import logging

import httpx

from app.core.config import get_settings
from app.modules.geocoding.schemas import LocationSuggestion

logger = logging.getLogger("app.geocoding")

_AUTOCOMPLETE_URL = "https://api.geoapify.com/v1/geocode/autocomplete"


class GeocodingService:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def autocomplete(self, text: str) -> list[LocationSuggestion]:
        # No key configured (e.g. local dev without GEOAPIFY_API_KEY) -- degrade to "no
        # suggestions" rather than error, so the location field still accepts free-typed input.
        if not self._settings.geoapify_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    _AUTOCOMPLETE_URL,
                    params={
                        "text": text,
                        "type": "city",
                        "format": "json",
                        "limit": 8,
                        "apiKey": self._settings.geoapify_api_key,
                    },
                )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            # A flaky/rate-limited geocoder must never break the Passport wizard -- same
            # graceful-degrade reasoning as the missing-key case above.
            logger.warning("Geoapify autocomplete request failed", exc_info=True)
            return []

        results = payload.get("results", [])
        suggestions = []
        for result in results:
            lat = result.get("lat")
            lon = result.get("lon")
            formatted = result.get("formatted")
            if lat is None or lon is None or not formatted:
                continue
            suggestions.append(
                LocationSuggestion(
                    formatted=formatted,
                    city=result.get("city"),
                    country=result.get("country"),
                    lat=lat,
                    lon=lon,
                )
            )
        return suggestions
