import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderWithProviders as render } from "../../../test/render";
import { RechargePage } from "../RechargePage";
import type { RechargeState } from "../useRecharge";

const hook = vi.hoisted((): { current: unknown } => ({ current: null }));
vi.mock("../useRecharge", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../useRecharge")>()),
  useRecharge: () => hook.current,
}));

const actions = { setAmount: vi.fn(), submit: vi.fn(), reset: vi.fn() };

function show(state: RechargeState, fieldError: string | null = null, amount = "50000") {
  hook.current = { amount, fieldError, state, ...actions };
  return render(<RechargePage />);
}

/** Ionic no se hidrata en jsdom: el hook se simula para recorrer cada estado de la pantalla. */
describe("RechargePage (estados)", () => {
  beforeEach(() => {
    Object.values(actions).forEach((fn) => fn.mockReset());
  });

  it("elige un monto sugerido con clic y con teclado", () => {
    show({ kind: "idle" }, null, "");

    const chip = screen.getByText("$ 20.000,00");
    fireEvent.click(chip);
    fireEvent.keyDown(chip, { key: "Enter" });
    fireEvent.keyDown(chip, { key: " " });
    fireEvent.keyDown(chip, { key: "a" });

    expect(actions.setAmount).toHaveBeenCalledTimes(3);
    expect(actions.setAmount).toHaveBeenCalledWith("20000");
  });

  it("muestra el rechazo del servidor cuando no es un error de campo (HU-08 CA-9)", () => {
    show({ kind: "rejected", message: "Sin billetera." });

    expect(screen.getByRole("alert")).toHaveTextContent("Recarga rechazada");
    expect(screen.getByRole("alert")).toHaveTextContent("Sin billetera.");
  });

  it("no repite el aviso cuando el error ya está junto al campo", () => {
    show({ kind: "rejected", message: "Fuera de rango." }, "Debe estar entre 5000.00 y 5000000.00");

    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("deshabilita Recargar mientras envía (FR-011)", () => {
    show({ kind: "submitting" });

    expect(screen.getByText("Recargando…", { selector: "ion-button" })).toHaveAttribute("disabled");
  });

  it("informa el éxito con el nuevo saldo y permite otra recarga (HU-08 CA-9)", () => {
    show({
      kind: "success",
      result: {
        id: 1,
        type: "recarga",
        status: "exitosa",
        amount: "50000.00",
        balance_after: "70000.00",
        created_at: "2026-10-14T21:40:00Z",
      },
    });

    expect(screen.getByRole("status")).toHaveTextContent("Recarga exitosa de $ 50.000,00.");
    expect(screen.getByRole("status")).toHaveTextContent("$ 70.000,00");
    fireEvent.click(screen.getByText("Hacer otra recarga", { selector: "ion-button" }));
    expect(actions.reset).toHaveBeenCalledTimes(1);
  });
});
