import { ApiError } from "@/lib/api-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Phantom staff are a third, separate principal from company Users and candidates — its own
// module-scoped token var, matching candidate-api-client.ts's exact reasoning. The refresh token
// is an httponly cookie the backend sets (see backend platform_admin/api.py), so a page reload
// re-establishes the access token via refreshPlatformAdminAccessToken() rather than reading
// anything from client-side storage.
let platformAdminAccessToken: string | null = null;

export function setPlatformAdminAccessToken(token: string | null): void {
  platformAdminAccessToken = token;
}

export function getPlatformAdminAccessToken(): string | null {
  return platformAdminAccessToken;
}

let refreshPromise: Promise<string | null> | null = null;

export async function refreshPlatformAdminAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/platform-admin/refresh`, {
          method: "POST",
          credentials: "include",
        });
        if (!res.ok) {
          platformAdminAccessToken = null;
          return null;
        }
        const data = (await res.json()) as { access_token: string };
        platformAdminAccessToken = data.access_token;
        return platformAdminAccessToken;
      } catch {
        platformAdminAccessToken = null;
        return null;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  skipAuthRetry?: boolean;
  extraHeaders?: Record<string, string>;
}

// Danger Zone actions pass the token obtained from POST /platform-admin/step-up here — see
// components/platform-admin/step-up-dialog.tsx — since the plain methods below have no other way
// to attach a one-off header. Mirrors api-client.ts's own stepUpHeaders exactly.
function stepUpHeaders(token?: string): Record<string, string> | undefined {
  return token ? { "X-Step-Up-Token": token } : undefined;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, skipAuthRetry = false, extraHeaders } = options;
  const headers: Record<string, string> = {};
  if (platformAdminAccessToken) headers.Authorization = `Bearer ${platformAdminAccessToken}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (extraHeaders) Object.assign(headers, extraHeaders);

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method,
    headers,
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !skipAuthRetry) {
    const newToken = await refreshPlatformAdminAccessToken();
    if (newToken) {
      return request<T>(path, { ...options, skipAuthRetry: true });
    }
  }

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
  post: <T>(path: string, body?: unknown, stepUpToken?: string) =>
    request<T>(path, { method: "POST", body, extraHeaders: stepUpHeaders(stepUpToken) }),
};
