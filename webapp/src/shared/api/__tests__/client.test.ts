import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../../test/server";
import { ApiError, request, setSessionExpiredHandler } from "../client";

describe("request", () => {
  it("envía X-Requested-With e Idempotency-Key en las mutaciones", async () => {
    let seen: Headers | undefined;
    server.use(
      http.post("/api/v1/wallet/recharges", ({ request: req }) => {
        seen = req.headers;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );

    const result = await request<{ id: number }>("/api/v1/wallet/recharges", {
      method: "POST",
      body: { amount: "5000.00" },
      idempotencyKey: "00000000-0000-4000-8000-000000000001",
    });

    expect(result).toEqual({ id: 1 });
    expect(seen?.get("X-Requested-With")).toBe("fetch");
    expect(seen?.get("Idempotency-Key")).toBe("00000000-0000-4000-8000-000000000001");
    expect(seen?.get("Content-Type")).toBe("application/json");
  });

  it("devuelve undefined en 204 y no añade X-Requested-With a los GET", async () => {
    let seen: Headers | undefined;
    server.use(
      http.get("/api/v1/thing", ({ request: req }) => {
        seen = req.headers;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    await expect(request("/api/v1/thing")).resolves.toBeUndefined();
    expect(seen?.get("X-Requested-With")).toBeNull();
  });

  it("lanza ApiError con el code del problem", async () => {
    server.use(
      http.get("/api/v1/wallet", () =>
        HttpResponse.json(
          { type: "t", title: "No", status: 404, code: "wallet_not_found" },
          { status: 404 },
        ),
      ),
    );

    await expect(request("/api/v1/wallet")).rejects.toMatchObject({
      code: "wallet_not_found",
      status: 404,
    });
    await expect(request("/api/v1/wallet")).rejects.toBeInstanceOf(ApiError);
  });

  it("invoca el manejador de sesión expirada ante 401 unauthenticated", async () => {
    const handler = vi.fn();
    setSessionExpiredHandler(handler);
    server.use(
      http.get("/api/v1/profile", () =>
        HttpResponse.json(
          { type: "t", title: "Sesión", status: 401, code: "unauthenticated" },
          { status: 401 },
        ),
      ),
    );

    await expect(request("/api/v1/profile")).rejects.toMatchObject({ code: "unauthenticated" });
    expect(handler).toHaveBeenCalledOnce();
  });
});
