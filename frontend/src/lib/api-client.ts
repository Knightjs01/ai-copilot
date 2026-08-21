export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

// Access token lives in module-level memory only (never localStorage) — the refresh token is
// an httponly cookie the backend sets, so a page reload re-establishes the access token via
// refreshAccessToken() rather than reading anything from client-side storage.
let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

let refreshPromise: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });
        if (!res.ok) {
          accessToken = null;
          return null;
        }
        const data = (await res.json()) as { access_token: string };
        accessToken = data.access_token;
        return accessToken;
      } catch {
        accessToken = null;
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
  formData?: FormData;
  skipAuthRetry?: boolean;
  extraHeaders?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, skipAuthRetry = false, extraHeaders } = options;
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (extraHeaders) Object.assign(headers, extraHeaders);

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method,
    headers,
    credentials: "include",
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
  });

  if (res.status === 401 && !skipAuthRetry) {
    const newToken = await refreshAccessToken();
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

// Step-up-gated actions (reveal identity, project purge, admin invite) pass the token obtained
// from POST /auth/step-up here — see src/lib/step-up.ts — since apiClient's normal methods have
// no way to attach a one-off header.
function stepUpHeaders(token?: string): Record<string, string> | undefined {
  return token ? { "X-Step-Up-Token": token } : undefined;
}

export const apiClient = {
  get: <T>(path: string, stepUpToken?: string) =>
    request<T>(path, { extraHeaders: stepUpHeaders(stepUpToken) }),
  post: <T>(path: string, body?: unknown, stepUpToken?: string) =>
    request<T>(path, { method: "POST", body, extraHeaders: stepUpHeaders(stepUpToken) }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  delete: <T>(path: string, stepUpToken?: string) =>
    request<T>(path, { method: "DELETE", extraHeaders: stepUpHeaders(stepUpToken) }),
  postForm: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", formData }),
};
