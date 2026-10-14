import { ApiError, toApiError } from "./problem";

/**
 * Cliente HTTP único de la webapp (ver .claude/rules/webapp.md).
 * - Mismo origen: la cookie de sesión viaja sola; nunca se guarda en localStorage.
 * - Toda mutación lleva `X-Requested-With: fetch` (defensa CSRF, ver security.md).
 * - Un 401 `session_expired` redirige al login; el resto se propaga como ApiError.
 */
export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  idempotencyKey?: string;
  signal?: AbortSignal;
}

export type SessionExpiredHandler = () => void;
let onSessionExpired: SessionExpiredHandler = () => {
  window.location.assign("/login");
};

export function setSessionExpiredHandler(handler: SessionExpiredHandler): void {
  onSessionExpired = handler;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method !== "GET") headers["X-Requested-With"] = "fetch";
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.idempotencyKey !== undefined) headers["Idempotency-Key"] = options.idempotencyKey;

  const response = await fetch(path, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  if (!response.ok) {
    const error = await toApiError(response);
    if (error.status === 401 && error.code === "session_expired") onSessionExpired();
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export { ApiError };
