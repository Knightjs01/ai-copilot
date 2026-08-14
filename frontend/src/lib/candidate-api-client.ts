import { ApiError } from "@/lib/api-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// A candidate is a separate principal from a company User (see
// backend/app/modules/candidate_auth/__init__.py) — deliberately its own module-scoped token
// var and its own refresh endpoint, not shared with api-client.ts. A person could plausibly be
// logged in as a company User in one tab and a Shadow candidate in another; sharing one token
// variable or hitting /auth/refresh for a candidate token would silently break one or the other.
let candidateAccessToken: string | null = null;

export function setCandidateAccessToken(token: string | null): void {
  candidateAccessToken = token;
}

export function getCandidateAccessToken(): string | null {
  return candidateAccessToken;
}

let refreshPromise: Promise<string | null> | null = null;

export async function refreshCandidateAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/candidate-auth/refresh`, {
          method: "POST",
          credentials: "include",
        });
        if (!res.ok) {
          candidateAccessToken = null;
          return null;
        }
        const data = (await res.json()) as { access_token: string };
        candidateAccessToken = data.access_token;
        return candidateAccessToken;
      } catch {
        candidateAccessToken = null;
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
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, skipAuthRetry = false } = options;
  const headers: Record<string, string> = {};
  if (candidateAccessToken) headers.Authorization = `Bearer ${candidateAccessToken}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method,
    headers,
    credentials: "include",
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
  });

  if (res.status === 401 && !skipAuthRetry) {
    const newToken = await refreshCandidateAccessToken();
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

async function requestBlob(
  path: string,
  skipAuthRetry = false
): Promise<{ blob: Blob; filename: string | null }> {
  const headers: Record<string, string> = {};
  if (candidateAccessToken) headers.Authorization = `Bearer ${candidateAccessToken}`;

  const res = await fetch(`${API_URL}/api/v1${path}`, { headers, credentials: "include" });

  if (res.status === 401 && !skipAuthRetry) {
    const newToken = await refreshCandidateAccessToken();
    if (newToken) return requestBlob(path, true);
  }
  if (!res.ok) throw new ApiError(res.status, res.statusText);

  const disposition = res.headers.get("Content-Disposition");
  const match = disposition ? /filename="([^"]+)"/.exec(disposition) : null;
  return { blob: await res.blob(), filename: match?.[1] ?? null };
}

export const candidateApiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", formData }),
  getBlob: (path: string) => requestBlob(path),
};
