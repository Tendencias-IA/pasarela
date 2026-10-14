import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderWithProviders as render } from "../../../test/render";
import { TransferPage } from "../TransferPage";

/** Ionic no se hidrata en jsdom: aquí solo se verifica el render; la interacción vive en Playwright. */
describe("TransferPage (render)", () => {
  it("muestra el título, el rango permitido y la acción de revisar", () => {
    render(<TransferPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Transferir dinero" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Entre \$ 100,00 y \$ 3\.000\.000,00 COP\./)).toBeInTheDocument();
    expect(screen.getByText("Revisar", { selector: "ion-button" })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Resumen de la transferencia" })).toBeNull();
  });
});
