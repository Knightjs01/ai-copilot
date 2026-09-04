import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Restricts Phantom Command (/platform-admin/*) to a fixed set of visitor IPs, so the portal is
// unreachable to the general public even though the rest of the site stays live on the same
// deployment. Mirrors the backend's PlatformAdminIPAllowlistMiddleware exactly: only enforced in
// production, fail-closed (an empty/misconfigured list blocks everyone), and a plain 404 for a
// disallowed request rather than a visible rejection, so the portal looks like it doesn't exist
// to anyone outside the allowlist.
//
// PLATFORM_ADMIN_ALLOWED_IPS is read directly from process.env (no NEXT_PUBLIC_ prefix) --
// middleware runs server-side only, so this value is never sent to the browser. It must be set
// as its own environment variable on this (frontend) Railway service, separately from the
// backend's copy of the same value, since they're separate containers.
//
// Trusts the x-forwarded-for header's first entry as the real visitor IP -- safe here for the
// same reason as the backend: Railway's edge proxy is the only thing that can reach this
// container at all, so trusting that one hop is the standard pattern for this deployment shape.
//
// The literal value "disabled" (case-insensitive) mirrors the backend's own escape hatch -- a
// deliberate, explicit way to turn this check off (e.g. no stable IP to allowlist yet) without
// relying on "empty means allow everyone", which is exactly the silent-misconfiguration failure
// mode this feature exists to avoid.
export function middleware(request: NextRequest) {
  if (process.env.NODE_ENV !== "production") {
    return NextResponse.next();
  }

  const rawAllowedIps = process.env.PLATFORM_ADMIN_ALLOWED_IPS ?? "";
  if (rawAllowedIps.trim().toLowerCase() === "disabled") {
    return NextResponse.next();
  }

  const allowedIps = rawAllowedIps
    .split(",")
    .map((ip) => ip.trim())
    .filter(Boolean);

  const forwardedFor = request.headers.get("x-forwarded-for");
  const clientIp = forwardedFor?.split(",")[0]?.trim();

  if (allowedIps.length === 0 || !clientIp || !allowedIps.includes(clientIp)) {
    return new NextResponse(null, { status: 404 });
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/platform-admin/:path*"],
};
