import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

/** Respuestas por defecto, acordes a api/openapi.yaml. Cada test puede sobreescribirlas con server.use(). */
export const handlers = [
  http.get("/health", () => HttpResponse.json({ status: "ok", db: "ok" })),
  http.get("/api/v1/auth/session", () => HttpResponse.json({ expires_at: "2099-01-01T00:00:00Z" })),
];

export const server = setupServer(...handlers);
