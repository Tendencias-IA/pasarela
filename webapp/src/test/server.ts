import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

/** Respuestas por defecto, acordes a api/openapi.yaml. Cada test puede sobreescribirlas con server.use(). */
export const handlers = [
  http.get("/health", () => HttpResponse.json({ status: "ok", db: "ok" })),
  http.get("/api/v1/wallet", () => HttpResponse.json({ balance: "0.00" })),
];

export const server = setupServer(...handlers);
