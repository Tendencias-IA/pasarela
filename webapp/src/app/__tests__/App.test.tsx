import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { App } from "../App";

describe("App (panel inicial)", () => {
  it("muestra el estado de la API cuando /health responde ok", async () => {
    render(<App />);

    const status = await screen.findByText("API ok, base de datos ok", {}, { timeout: 5000 });

    expect(status).toHaveAttribute("role", "status");
    expect(status).toHaveAttribute("data-health", "ok");
    expect(
      screen.getByRole("heading", { level: 1, name: "Billetera Digital" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Recargar saldo")).toBeInTheDocument();
  });

  it("muestra una alerta con el código cuando la API responde un problem", async () => {
    server.use(
      http.get("/health", () =>
        HttpResponse.json(
          { type: "x", title: "Degradado", status: 503, code: "db_unavailable" },
          { status: 503, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("db_unavailable (503)");
  });

  it("muestra sin conexión cuando la respuesta no es un problem", async () => {
    server.use(http.get("/health", () => HttpResponse.text("gateway timeout", { status: 504 })));

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("unknown_error (504)");
  });

  it("muestra el saldo disponible del usuario en el panel (HU-05 CA-1, CA-2)", async () => {
    server.use(http.get("/api/v1/wallet", () => HttpResponse.json({ balance: "150000.00" })));

    render(<App />);

    const card = await screen.findByLabelText("Saldo disponible");
    await waitFor(() => {
      expect(card).toHaveTextContent("$ 150.000,00");
    });
  });

  it("informa que el saldo no está disponible cuando no hay billetera (HU-05 CA-5)", async () => {
    server.use(
      http.get("/api/v1/wallet", () =>
        HttpResponse.json(
          { type: "t", title: "Billetera no encontrada", status: 404, code: "wallet_not_found" },
          { status: 404, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    render(<App />);

    expect(await screen.findByText("Saldo no disponible")).toBeInTheDocument();
  });

  it("sin sesión no renderiza el menú lateral, solo con sesión iniciada (HU-04 CA-2)", async () => {
    server.use(
      http.get("/api/v1/auth/session", () =>
        HttpResponse.json(
          { type: "t", title: "Sesión", status: 401, code: "invalid_session" },
          { status: 401, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    render(<App />);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/login");
    });
    expect(document.querySelector("ion-menu")).toBeNull();
    expect(screen.queryByText("Cerrar sesión")).not.toBeInTheDocument();
  });
});
