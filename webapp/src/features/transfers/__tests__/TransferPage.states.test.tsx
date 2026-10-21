import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderWithProviders as render } from "../../../test/render";
import { TransferPage } from "../TransferPage";
import type { TransferState } from "../useTransfer";

type Hook = ReturnType<typeof import("../useTransfer").useTransfer>;

const hook = vi.hoisted((): { current: unknown } => ({ current: null }));
vi.mock("../useTransfer", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../useTransfer")>()),
  useTransfer: () => hook.current,
}));

const PREVIEW = {
  amount: "150000.00",
  recipient: { name_masked: null, phone_masked: "***4567" },
  balance_after: "350000.00",
};

const actions = {
  review: vi.fn(),
  edit: vi.fn(),
  confirm: vi.fn(),
  reset: vi.fn(),
  setAmount: vi.fn(),
  setRecipientPhone: vi.fn(),
};

function show(state: TransferState, fieldErrors: Hook["fieldErrors"] = {}) {
  hook.current = { recipientPhone: "3001234567", amount: "150000", fieldErrors, state, ...actions };
  return render(<TransferPage />);
}

/** Ionic no se hidrata en jsdom: el hook se simula para recorrer cada estado de la pantalla. */
describe("TransferPage (estados)", () => {
  beforeEach(() => {
    Object.values(actions).forEach((fn) => fn.mockReset());
  });

  it("muestra el aviso de rechazo del formulario y los errores de campo (CA-3, CA-4)", () => {
    show(
      { kind: "form", message: "No puedes transferirte a tu propia cuenta." },
      { recipientPhone: "Teléfono no válido.", amount: "Monto no válido." },
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "No puedes transferirte a tu propia cuenta.",
    );
    expect(screen.getByText("Revisar", { selector: "ion-button" })).toBeInTheDocument();
  });

  it("deshabilita Revisar mientras consulta", () => {
    show({ kind: "previewing" });

    expect(screen.getByText("Revisando…", { selector: "ion-button" })).toHaveAttribute("disabled");
  });

  it("el resumen enmascara al destinatario y ofrece Confirmar y Editar (HU-06 CA-7)", () => {
    show({ kind: "summary", preview: PREVIEW, message: null });

    const region = screen.getByRole("region", { name: "Resumen de la transferencia" });
    expect(region).toHaveTextContent("***4567");
    expect(region).toHaveTextContent("$ 150.000,00");
    expect(region).toHaveTextContent("$ 350.000,00");
    fireEvent.click(screen.getByText("Confirmar", { selector: "ion-button" }));
    fireEvent.click(screen.getByText("Editar", { selector: "ion-button" }));
    expect(actions.confirm).toHaveBeenCalledTimes(1);
    expect(actions.edit).toHaveBeenCalledTimes(1);
  });

  it("el resumen muestra el nombre enmascarado cuando existe y el aviso de reintento", () => {
    show({
      kind: "summary",
      preview: { ...PREVIEW, recipient: { name_masked: "Mar** G*****", phone_masked: "***4567" } },
      message: "No se pudo conectar con el servicio. Puedes reintentar: no se duplicará.",
    });

    expect(screen.getByText("Mar** G*****", { exact: false })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("no se duplicará");
  });

  it("deshabilita Confirmar y Editar mientras confirma (HU-07 CA-8)", () => {
    show({ kind: "confirming", preview: PREVIEW });

    expect(screen.getByText("Confirmando…", { selector: "ion-button" })).toHaveAttribute(
      "disabled",
    );
    expect(screen.getByText("Editar", { selector: "ion-button" })).toHaveAttribute("disabled");
  });

  it("informa el éxito con el nuevo saldo y permite otra transferencia (HU-07 CA-7)", () => {
    show({
      kind: "success",
      result: {
        id: 8812,
        type: "transferencia",
        status: "exitosa",
        amount: "150000.00",
        recipient: { name_masked: null, phone_masked: "***4567" },
        balance_after: "350000.00",
        created_at: "2026-10-14T21:40:00Z",
      },
    });

    expect(screen.getByRole("status")).toHaveTextContent("Transferencia exitosa de $ 150.000,00.");
    expect(screen.getByRole("status")).toHaveTextContent("$ 350.000,00");
    fireEvent.click(screen.getByText("Hacer otra transferencia", { selector: "ion-button" }));
    expect(actions.reset).toHaveBeenCalledTimes(1);
  });

  it("informa el rechazo sin mover dinero y permite editar los datos (HU-07 CA-6, CA-7)", () => {
    show({ kind: "rejected", message: "Tu saldo es menor que el monto de la transferencia." });

    expect(screen.getByRole("alert")).toHaveTextContent("Transferencia rechazada");
    expect(screen.getByRole("alert")).toHaveTextContent("No se movió dinero");
    fireEvent.click(screen.getByText("Editar datos", { selector: "ion-button" }));
    expect(actions.edit).toHaveBeenCalledTimes(1);
  });
});
