import { ApiError, toApiError } from "./problem";

/**
 * Cliente HTTP único de la webapp (ver .claude/rules/webapp.md).
 * - Mismo origen: la cookie de sesión viaja sola; nunca se guarda en localStorage.
 * - Toda mutación lleva `X-Requested-With: fetch` (defensa CSRF, ver security.md).
 * - Un 401 `invalid_session` (sesión ausente, vencida o revocada) redirige al login; el
 *   resto se propaga como ApiError.
 */
export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  idempotencyKey?: string;
  signal?: AbortSignal;
  /** Con `false` el 401 solo se propaga (lo usa el guardián de rutas, que redirige por su cuenta). */
  redirectOnUnauthorized?: boolean;
}

export type SessionExpiredHandler = () => void;
let onSessionExpired: SessionExpiredHandler = () => {
  // HU-04 CA-2: la operación privada exige iniciar sesión de nuevo; el aviso lo muestra
  // la pantalla de login. Sin bucle si ya se está en /login.
  if (window.location.pathname !== "/login") window.location.assign("/login?motivo=expirada");
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
    if (
      error.status === 401 &&
      error.code === "invalid_session" &&
      options.redirectOnUnauthorized !== false
    ) {
      onSessionExpired();
    }
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export { ApiError };
