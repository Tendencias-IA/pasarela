import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderWithProviders } from "../../../test/render";
import { LoginPage } from "../LoginPage";

/** Ionic no se hidrata en jsdom: aquí solo el render; la interacción vive en Playwright. */
describe("LoginPage (HU-02, HU-04)", () => {
  it("avisa que la sesión expiró cuando se llega con ?motivo=expirada (HU-04 CA-2)", () => {
    renderWithProviders(<LoginPage />, { route: "/login?motivo=expirada" });

    expect(screen.getByRole("status")).toHaveTextContent(
      "Tu sesión expiró. Inicia sesión de nuevo.",
    );
  });

  it("no muestra aviso de expiración en un ingreso normal", () => {
    renderWithProviders(<LoginPage />, { route: "/login" });

    expect(screen.queryByText(/Tu sesión expiró/)).not.toBeInTheDocument();
  });
});
