import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

/** Respuestas por defecto, acordes a api/openapi.yaml. Cada test puede sobreescribirlas con server.use(). */
export const handlers = [http.get("/health", () => HttpResponse.json({ status: "ok", db: "ok" }))];

export const server = setupServer(...handlers);
