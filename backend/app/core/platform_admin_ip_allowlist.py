from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

_PROTECTED_PREFIX = "/api/v1/platform-admin"


class PlatformAdminIPAllowlistMiddleware(BaseHTTPMiddleware):
    """Restricts Phantom Command's backend surface to a fixed set of visitor IPs, so the portal
    is unreachable to the general public even though the rest of the site stays live on the same
    deployment. Only enforced in production -- local dev (and any other environment) is never
    blocked, since there's no real exposure to guard against there.

    Returns a plain 404, never 403, for a disallowed request: the goal is for the portal to look
    like it doesn't exist to anyone outside the allowlist, not to visibly reject them.

    Relies on request.client.host reflecting the real visitor IP, which requires the production
    uvicorn process to trust Railway's edge proxy's X-Forwarded-For header (see the
    --forwarded-allow-ips flag on the production CMD in Dockerfile) -- Railway's proxy is the
    only thing that can reach this container's public port at all, so trusting that one hop is
    the standard, safe pattern for this class of deployment."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        settings = get_settings()
        if settings.environment != "production":
            return await call_next(request)
        if not request.url.path.startswith(_PROTECTED_PREFIX):
            return await call_next(request)

        allowed_ips = settings.platform_admin_allowed_ip_list
        client_ip = request.client.host if request.client else None
        # Fail-closed: an empty list (unset env var) or an unrecognized client IP both result in
        # the same 404 -- a misconfigured allowlist must never silently mean "allow everyone."
        if not allowed_ips or client_ip not in allowed_ips:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        return await call_next(request)
