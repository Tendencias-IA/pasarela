import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { renderWithProviders } from "../../test/render";
import { server } from "../../test/server";
import { HomePage } from "../HomePage";

const PATH = "/api/v1/wallet";

describe("HomePage: tarjeta de saldo (HU-05)", () => {
  it("muestra consultando y luego el saldo en COP (CA-1, CA-2)", async () => {
    server.use(http.get(PATH, () => HttpResponse.json({ balance: "150000.00" })));

    renderWithProviders(<HomePage />);

    expect(screen.getByRole("heading", { level: 2, name: "Saldo disponible" })).toBeInTheDocument();
    expect(screen.getByText("Consultando saldo…")).toHaveAttribute("role", "status");
    expect(await screen.findByText("$ 150.000,00")).toBeInTheDocument();
    expect(screen.queryByText("Consultando saldo…")).not.toBeInTheDocument();
  });

  it("informa saldo no disponible, sin monto, cuando no hay billetera (CA-5)", async () => {
    server.use(
      http.get(PATH, () =>
        HttpResponse.json(
          { type: "t", title: "x", status: 404, code: "wallet_not_found" },
          { status: 404, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );

    renderWithProviders(<HomePage />);

    const alert = await screen.findByText("Saldo no disponible");
    expect(alert).toHaveAttribute("role", "alert");
    expect(document.body.textContent).not.toMatch(/\$ \d/);
  });

  it("informa el error ante un fallo inesperado sin inventar un saldo", async () => {
    server.use(http.get(PATH, () => HttpResponse.text("gateway timeout", { status: 504 })));

    renderWithProviders(<HomePage />);

    expect(await screen.findByText(/No se pudo consultar el saldo/)).toHaveAttribute(
      "role",
      "alert",
    );
    expect(document.body.textContent).not.toMatch(/\$ \d/);
  });

  it("conserva los accesos a recargar y a movimientos", async () => {
    server.use(http.get(PATH, () => HttpResponse.json({ balance: "0.00" })));

    renderWithProviders(<HomePage />);

    expect(await screen.findByText("$ 0,00")).toBeInTheDocument();
    expect(screen.getByText("Recargar saldo")).toBeInTheDocument();
    expect(screen.getByText("Ver movimientos")).toBeInTheDocument();
  });
});
