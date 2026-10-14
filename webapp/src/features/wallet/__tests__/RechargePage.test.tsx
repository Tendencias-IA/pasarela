import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderWithProviders as render } from "../../../test/render";
import { RechargePage } from "../RechargePage";

/** Ionic no se hidrata en jsdom: aquí solo se verifica el render; la interacción vive en Playwright. */
describe("RechargePage (render)", () => {
  it("muestra el título, el rango permitido y los montos sugeridos del diseño", () => {
    render(<RechargePage />);

    expect(screen.getByRole("heading", { level: 1, name: "Recargar saldo" })).toBeInTheDocument();
    expect(screen.getByText(/Entre \$ 5\.000,00 y \$ 5\.000\.000,00 COP\./)).toBeInTheDocument();
    expect(screen.getByText("$ 50.000,00")).toBeInTheDocument();
    expect(screen.getByText("Recargar", { selector: "ion-button" })).toBeInTheDocument();
  });
});
