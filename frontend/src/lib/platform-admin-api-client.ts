import { ApiError } from "@/lib/api-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Phantom staff are a third, separate principal from company Users and candidates — its own
// module-scoped token var, matching candidate-api-client.ts's exact reasoning. No refresh route
// exists yet (see backend platform_admin/__init__.py) -- a real, stated Phase 1 limitation, not
// an oversight: the token just lives in memory and a session ends on reload or expiry.
let platformAdminAccessToken: string | null = null;

export function setPlatformAdminAccessToken(token: string | null): void {
  platformAdminAccessToken = token;
}

export function getPlatformAdminAccessToken(): string | null {
  return platformAdminAccessToken;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body } = options;
  const headers: Record<string, string> = {};
  if (platformAdminAccessToken) headers.Authorization = `Bearer ${platformAdminAccessToken}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = (await res.json()) as { detail?: string };
      detail = data.detail ?? detail;
    } catch {
      // Response body wasn't JSON — fall back to statusText.
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const platformAdminApiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
};
