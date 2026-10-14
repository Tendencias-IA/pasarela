import { waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { setSessionExpiredHandler } from "../../../shared/api/client";
import { renderHookWithProviders } from "../../../test/render";
import { server } from "../../../test/server";
import { useWallet } from "../useWallet";

const PATH = "/api/v1/wallet";

describe("useWallet (HU-05)", () => {
  it("expone el saldo persistido como cadena decimal (CA-1, CA-2)", async () => {
    server.use(http.get(PATH, () => HttpResponse.json({ balance: "150000.00" })));

    const { result } = renderHookWithProviders(() => useWallet());

    await waitFor(() => {
      expect(result.current.data?.balance).toBe("150000.00");
    });
  });

  it("marca 'no disponible' ante 404 wallet_not_found (CA-5)", async () => {
    server.use(
      http.get(PATH, () =>
        HttpResponse.json(
          { type: "t", title: "Billetera no encontrada", status: 404, code: "wallet_not_found" },
          { status: 404, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    const { result } = renderHookWithProviders(() => useWallet());

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    expect(result.current.isUnavailable).toBe(true);
  });

  it("invoca el manejador de sesión expirada ante 401 invalid_session (HU-04 CA-2)", async () => {
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);
    server.use(
      http.get(PATH, () =>
        HttpResponse.json(
          { type: "t", title: "Sesión", status: 401, code: "invalid_session" },
          { status: 401, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    const { result } = renderHookWithProviders(() => useWallet());

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    expect(result.current.isUnavailable).toBe(false);
    expect(onExpired).toHaveBeenCalledTimes(1);
  });
});
