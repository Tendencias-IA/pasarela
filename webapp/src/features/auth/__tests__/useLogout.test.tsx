import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { createQueryClient } from "../../../app/queryClient";
import { server } from "../../../test/server";
import { useLogout } from "../useLogout";

const LOGOUT = "/api/v1/auth/logout";

function setup() {
  const client = createQueryClient();
  client.setQueryData(["wallet"], { balance: "150000.00" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/recargar"]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
  const hook = renderHook(() => ({ auth: useLogout(), location: useLocation() }), { wrapper });
  return { client, ...hook };
}

describe("useLogout (HU-03 CA-1, CA-3)", () => {
  it("revoca la sesión en el servidor, vacía la caché y va a /login", async () => {
    const seen: Headers[] = [];
    server.use(
      http.post(LOGOUT, ({ request }) => {
        seen.push(request.headers);
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { client, result } = setup();

    await act(() => result.current.auth.logout());

    expect(seen[0]?.get("X-Requested-With")).toBe("fetch");
    expect(client.getQueryData(["wallet"])).toBeUndefined();
    await waitFor(() => {
      expect(result.current.location.pathname).toBe("/login");
    });
  });

  it("también sale de la pantalla privada si el servidor ya no reconoce la sesión", async () => {
    server.use(
      http.post(LOGOUT, () =>
        HttpResponse.json(
          { type: "t", title: "Sesión", status: 401, code: "invalid_session" },
          { status: 401, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );
    const { client, result } = setup();

    await act(() => result.current.auth.logout());

    expect(client.getQueryData(["wallet"])).toBeUndefined();
    expect(result.current.location.pathname).toBe("/login");
  });

  it("no oculta el menú si no se pudo revocar: se queda y avisa (error de red)", async () => {
    server.use(http.post(LOGOUT, () => HttpResponse.error()));
    const { client, result } = setup();

    await act(() => result.current.auth.logout());

    expect(result.current.location.pathname).toBe("/recargar");
    expect(client.getQueryData(["wallet"])).toBeDefined();
    expect(result.current.auth.failed).toBe(true);
  });
});
