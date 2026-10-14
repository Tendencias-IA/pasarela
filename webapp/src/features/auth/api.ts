import { request } from "../../shared/api/client";
import type { components } from "../../shared/api/types.gen";

export type LoginRequest = components["schemas"]["LoginIn"];

/** Éxito es 204 sin cuerpo: la sesión queda en la cookie (ver api-design.md). */
export async function login(payload: LoginRequest, signal?: AbortSignal): Promise<void> {
  await request<undefined>("/api/v1/auth/login", { method: "POST", body: payload, signal });
}

export async function logout(): Promise<void> {
  await request<undefined>("/api/v1/auth/logout", { method: "POST" });
}

export function getSession(signal?: AbortSignal) {
  return request<components["schemas"]["SessionStatus"]>("/api/v1/auth/session", { signal });
}
