import { request } from "../../shared/api/client";
import type { components } from "../../shared/api/types.gen";

export type LoginRequest = components["schemas"]["LoginIn"];

/** Éxito es 204 sin cuerpo: la sesión queda en la cookie (ver api-design.md). */
export async function login(payload: LoginRequest, signal?: AbortSignal): Promise<void> {
  await request<undefined>("/api/v1/auth/login", { method: "POST", body: payload, signal });
}

export type SessionOut = components["schemas"]["SessionOut"];

/**
 * GET /api/v1/auth/session (HU-04): sesión vigente. Consultarla cuenta como actividad.
 * El 401 no redirige aquí: el guardián de rutas decide.
 */
export function getSession(signal?: AbortSignal) {
  return request<SessionOut>("/api/v1/auth/session", { signal, redirectOnUnauthorized: false });
}
