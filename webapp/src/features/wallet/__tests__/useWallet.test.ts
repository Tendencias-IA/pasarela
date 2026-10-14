import { act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { setSessionExpiredHandler } from "../../../shared/api/client";
import { renderHookWithProviders } from "../../../test/render";
import { server } from "../../../test/server";
import { useWallet } from "../useWallet";

const PATH = "/api/v1/wallet";

function problem(status: number, code: string) {
  return HttpResponse.json(
    { type: "t", title: code, status, code },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}

describe("useWallet (HU-05)", () => {
  it("consulta GET /api/v1/wallet sin X-Requested-With y expone el saldo exacto (CA-1, CA-2)", async () => {
    const headers: string[] = [];
    server.use(
      http.get(PATH, ({ request }) => {
        headers.push(request.headers.get("X-Requested-With") ?? "none");
        return HttpResponse.json({ balance: "150000.00" });
      }),
    );

    const { result } = renderHookWithProviders(() => useWallet());

    await waitFor(() => {
      expect(result.current.data?.balance).toBe("150000.00");
    });
    expect(headers).toEqual(["none"]);
  });

  it("expone wallet_not_found como error cuando no hay billetera (CA-5)", async () => {
    server.use(http.get(PATH, () => problem(404, "wallet_not_found")));

    const { result } = renderHookWithProviders(() => useWallet());

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    expect(result.current.error).toMatchObject({ code: "wallet_not_found", status: 404 });
    expect(result.current.data).toBeUndefined();
  });

  it("invoca el manejador de sesión expirada ante 401 invalid_session (HU-04 CA-2)", async () => {
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);
    server.use(http.get(PATH, () => problem(401, "invalid_session")));

    const { result } = renderHookWithProviders(() => useWallet());

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("expone isError ante un fallo de red y refetch lo recupera", async () => {
    let calls = 0;
    server.use(
      http.get(PATH, () => {
        calls += 1;
        return calls === 1 ? HttpResponse.error() : HttpResponse.json({ balance: "0.00" });
      }),
    );

    const { result } = renderHookWithProviders(() => useWallet());
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    await act(() => result.current.refetch().then(() => undefined));

    await waitFor(() => {
      expect(result.current.data?.balance).toBe("0.00");
    });
  });
});
