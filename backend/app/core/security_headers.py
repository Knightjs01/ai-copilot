from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Swagger UI (served at docs_url) pulls its JS/CSS from a CDN by default — a strict CSP here
# would break the docs page itself, so it's exempted. Every other response (the actual JSON API)
# gets the full policy; JSON responses don't execute page content anyway, but this is
# defense-in-depth for anything ever served as HTML from this API in the future.
_CSP_EXEMPT_PREFIXES = ("/api/docs", "/api/openapi.json", "/api/redoc")

_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Headers with no per-request cost and no legitimate reason to ever be absent — clickjacking,
    MIME-sniffing, and referrer-leak protections that every response should carry regardless of
    route. HSTS is gated on cookie_secure (only meaningful once the app is actually served over
    HTTPS; forcing it in local HTTP dev would make browsers refuse to load the app at all)."""

    def __init__(self, app, *, hsts_enabled: bool) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._hsts_enabled = hsts_enabled

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        if not request.url.path.startswith(_CSP_EXEMPT_PREFIXES):
            response.headers["Content-Security-Policy"] = _CSP

        if self._hsts_enabled:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        return response
