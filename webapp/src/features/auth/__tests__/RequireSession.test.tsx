import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { Link, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { setSessionExpiredHandler } from "../../../shared/api/client";
import { renderWithProviders } from "../../../test/render";
import { server } from "../../../test/server";
import { RequireSession } from "../RequireSession";

const SESSION = "/api/v1/auth/session";

function Harness() {
  return (
    <Routes>
      <Route path="/login" element={<p>Pantalla de login</p>} />
      <Route
        path="/*"
        element={
          <RequireSession>
            <p>Contenido privado</p>
          </RequireSession>
        }
      />
    </Routes>
  );
}

function NavigatingHarness() {
  return (
    <Routes>
      <Route path="/login" element={<p>Pantalla de login</p>} />
      <Route
        path="/*"
        element={
          <RequireSession>
            <p>Contenido privado</p>
            <Link to="/transferir">Ir a transferir</Link>
          </RequireSession>
        }
      />
    </Routes>
  );
}

function unauthorized() {
  return HttpResponse.json(
    { type: "t", title: "Sesión", status: 401, code: "invalid_session" },
    { status: 401, headers: { "Content-Type": "application/problem+json" } },
  );
}

describe("RequireSession (HU-04 CA-2, RNF-01.1)", () => {
  it("muestra verificando y luego el contenido cuando la sesión es válida", async () => {
    server.use(http.get(SESSION, () => HttpResponse.json({ expires_at: "2026-10-14T21:45:00Z" })));

    renderWithProviders(<Harness />, { route: "/recargar" });

    expect(screen.getByRole("status")).toHaveTextContent("Verificando sesión…");
    expect(await screen.findByText("Contenido privado")).toBeInTheDocument();
    expect(screen.queryByText("Pantalla de login")).not.toBeInTheDocument();
  });

  it("redirige a /login sin mostrar el contenido cuando no hay sesión", async () => {
    server.use(http.get(SESSION, unauthorized));

    renderWithProviders(<Harness />, { route: "/movimientos" });

    expect(await screen.findByText("Pantalla de login")).toBeInTheDocument();
    expect(screen.queryByText("Contenido privado")).not.toBeInTheDocument();
  });

  it("no usa el manejador global de sesión expirada: la redirección es interna", async () => {
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);
    server.use(http.get(SESSION, unauthorized));

    renderWithProviders(<Harness />, { route: "/" });

    await screen.findByText("Pantalla de login");
    expect(onExpired).not.toHaveBeenCalled();
  });

  it("ante un fallo distinto de 401 ofrece reintentar y no expulsa al usuario", async () => {
    let calls = 0;
    server.use(
      http.get(SESSION, () => {
        calls += 1;
        return calls === 1
          ? HttpResponse.text("gateway timeout", { status: 504 })
          : HttpResponse.json({ expires_at: "2026-10-14T21:45:00Z" });
      }),
    );

    renderWithProviders(<Harness />, { route: "/" });

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo verificar la sesión");
    screen.getByText("Reintentar").click();
    await waitFor(() => {
      expect(screen.getByText("Contenido privado")).toBeInTheDocument();
    });
    expect(screen.queryByText("Pantalla de login")).not.toBeInTheDocument();
  });

  it("revalida al cambiar de ruta: con la sesión vencida el menú no sigue visible (HU-04 CA-2)", async () => {
    let calls = 0;
    server.use(
      http.get(SESSION, () => {
        calls += 1;
        return calls === 1
          ? HttpResponse.json({ expires_at: "2026-10-14T21:45:00Z" })
          : unauthorized();
      }),
    );
    renderWithProviders(<NavigatingHarness />, { route: "/recargar" });
    expect(await screen.findByText("Contenido privado")).toBeInTheDocument();

    screen.getByText("Ir a transferir").click();

    expect(await screen.findByText("Pantalla de login")).toBeInTheDocument();
    expect(screen.queryByText("Contenido privado")).not.toBeInTheDocument();
  });
});
