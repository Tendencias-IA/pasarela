import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../../test/server";
import { useLogout } from "../useLogout";

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(["private"], { balance: "12345.00" });
  const done = vi.fn();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, done, ...renderHook(() => useLogout(done), { wrapper }) };
}

describe("HU-03 cerrar sesión", () => {
  it("CA-1/CA-3 limpia la caché y notifica solo después de revocar", async () => {
    let calls = 0;
    server.use(
      http.post("/api/v1/auth/logout", ({ request }) => {
        calls++;
        expect(request.headers.get("X-Requested-With")).toBe("fetch");
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { result, client, done } = setup();
    await act(async () => {
      await Promise.all([result.current.submit(), result.current.submit()]);
    });
    expect(calls).toBe(1);
    expect(client.getQueryCache().getAll()).toHaveLength(0);
    expect(done).toHaveBeenCalledOnce();
  });

  it("CA-1 conserva estado y permite reintentar si el servidor falla", async () => {
    server.use(http.post("/api/v1/auth/logout", () => new HttpResponse(null, { status: 503 })));
    const { result, client, done } = setup();
    await act(async () => {
      await result.current.submit();
    });
    await waitFor(() => {
      expect(result.current.error).toMatch(/No se pudo cerrar/);
    });
    expect(client.getQueryData(["private"])).toEqual({ balance: "12345.00" });
    expect(done).not.toHaveBeenCalled();
    server.use(http.post("/api/v1/auth/logout", () => new HttpResponse(null, { status: 204 })));
    await act(async () => {
      await result.current.submit();
    });
    expect(done).toHaveBeenCalledOnce();
  });
});
