import { ApiError } from "@/lib/api-client";

/** Many "get the latest generated artifact" endpoints 404 until something has been generated —
 * treat that as a normal "not yet" state (null) rather than a query error. */
export async function fetchOrNull<T>(fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn();
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}
