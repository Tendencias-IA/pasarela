import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { App } from "../App";

describe("App", () => {
  it("muestra el estado de la API cuando /health responde ok", async () => {
    render(<App />);

    const status = await screen.findByText("API ok, base de datos ok");

    expect(status).toHaveAttribute("role", "status");
    expect(status).toHaveAttribute("data-health", "ok");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Billetera Digital");
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
});
