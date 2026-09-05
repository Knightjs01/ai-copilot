/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [{ source: "/shadow/for-you", destination: "/shadow", permanent: true }];
  },
  // Proxies same-origin /api/v1/* calls through to the real backend server-side, so the browser
  // never talks directly to the backend's raw *.up.railway.app hostname. Before this, every
  // login form (company/candidate/platform-admin) submitted a password as a cross-origin request
  // to a generic, unrelated cloud subdomain -- exactly the shape phishing heuristics look for
  // (a page on one domain silently sending credentials to a different, disposable-looking one),
  // which is what got this site's login page flagged by NordVPN's Threat Protection.
  //
  // BACKEND_INTERNAL_URL (not NEXT_PUBLIC_API_URL) on purpose: this function runs server-side,
  // inside whatever container/process actually runs the Next.js server -- in local docker-compose
  // dev that's a *different* container from the one "localhost" refers to for a browser, so it
  // needs the backend's Compose service name (http://backend:8000), not the browser-facing
  // NEXT_PUBLIC_API_URL value. Falls back to NEXT_PUBLIC_API_URL (already the backend's real
  // public URL in production, which a normal outbound server-to-server HTTPS call reaches fine)
  // so production needs no new Railway variable to already work correctly.
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_INTERNAL_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000";
    return [{ source: "/api/v1/:path*", destination: `${backendUrl}/api/v1/:path*` }];
  },
};

module.exports = nextConfig;
