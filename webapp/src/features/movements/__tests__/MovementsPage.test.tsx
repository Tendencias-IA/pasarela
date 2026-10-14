import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { formatDateTime } from "../../../shared/dates";
import { renderWithProviders } from "../../../test/render";
import { server } from "../../../test/server";
import { MovementsPage } from "../MovementsPage";
import { movement, pageOf } from "./fixtures";

const PATH = "/api/v1/movements";

describe("MovementsPage (HU-09)", () => {
  it("muestra cargando y luego una fila por movimiento con fecha, monto, tipo y estado (CA-2)", async () => {
    server.use(
      http.get(PATH, () =>
        HttpResponse.json({
          items: [
            movement({
              id: 2,
              amount: "4999.00",
              status: "rechazada",
              rejection_reason: "amount_out_of_range",
            }),
            movement({ id: 1, amount: "50000.00" }),
          ],
          page: 1,
          page_size: 20,
          total: 2,
        }),
      ),
    );

    renderWithProviders(<MovementsPage />, { route: "/movimientos" });

    expect(screen.getByRole("heading", { level: 1, name: "Movimientos" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Cargando…");
    const rows = await screen.findAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent("Recarga");
    expect(rows[0]).toHaveTextContent("$ 4.999,00");
    expect(rows[0]).toHaveTextContent("Rechazada");
    expect(rows[0]).toHaveAttribute("data-status", "rechazada");
    expect(rows[1]).toHaveTextContent("$ 50.000,00");
    expect(rows[1]).toHaveTextContent("Exitosa");
    expect(rows[1]).toHaveTextContent(formatDateTime("2026-10-14T21:40:00Z"));
  });

  it("muestra la contraparte enmascarada de una transferencia y nunca un teléfono completo (CA-3)", async () => {
    server.use(
      http.get(PATH, () =>
        HttpResponse.json({
          items: [
            movement({
              id: 3,
              direction: "enviada",
              type: "transferencia",
              counterparty: { name_masked: null, phone_masked: "***4567" },
            }),
            movement({
              id: 2,
              direction: "recibida",
              type: "transferencia",
              counterparty: { name_masked: "Mar** G*****", phone_masked: "***1234" },
            }),
          ],
          page: 1,
          page_size: 20,
          total: 2,
        }),
      ),
    );

    renderWithProviders(<MovementsPage />, { route: "/movimientos" });

    const rows = await screen.findAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("Transferencia enviada");
    expect(rows[0]).toHaveTextContent("a ***4567");
    expect(rows[1]).toHaveTextContent("Transferencia recibida");
    expect(rows[1]).toHaveTextContent("de Mar** G***** · ***1234");
    expect(document.body.textContent).not.toMatch(/\d{10}/);
  });

  it("muestra el estado vacío con acceso a recargar cuando no hay movimientos (CA-7)", async () => {
    server.use(
      http.get(PATH, () => HttpResponse.json({ items: [], page: 1, page_size: 20, total: 0 })),
    );

    renderWithProviders(<MovementsPage />, { route: "/movimientos" });

    const empty = await screen.findByText("Aún no tienes movimientos");
    expect(empty.closest("[role=status]")).not.toBeNull();
    const link = screen.getByText("Recargar saldo").closest("ion-button");
    expect(link).toHaveAttribute("router-link", "/recargar");
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
    expect(screen.queryByRole("navigation", { name: "Paginación" })).not.toBeInTheDocument();
  });

  it("pagina con 45 movimientos: página 1 de 3, Anterior deshabilitado (CA-6)", async () => {
    server.use(
      http.get(PATH, ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get("page"));
        return HttpResponse.json(pageOf(page, 45));
      }),
    );

    renderWithProviders(<MovementsPage />, { route: "/movimientos" });

    await screen.findAllByRole("listitem");
    const nav = screen.getByRole("navigation", { name: "Paginación" });
    expect(nav).toHaveTextContent("Página 1 de 3");
    expect(screen.getByText("Anterior").closest("ion-button")).toHaveAttribute("disabled");
    expect(screen.getByText("Siguiente").closest("ion-button")).not.toHaveAttribute("disabled");
  });

  it("corrige una página fuera de rango llevando a la última (FR-009)", async () => {
    server.use(
      http.get(PATH, ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get("page"));
        return HttpResponse.json(pageOf(page, 45));
      }),
    );

    renderWithProviders(<MovementsPage />, { route: "/movimientos?page=9" });

    await waitFor(() => {
      expect(screen.getByRole("navigation", { name: "Paginación" })).toHaveTextContent(
        "Página 3 de 3",
      );
    });
    expect(screen.getByText("Siguiente").closest("ion-button")).toHaveAttribute("disabled");
  });

  it("muestra una alerta con reintento cuando la API falla", async () => {
    server.use(http.get(PATH, () => HttpResponse.text("gateway timeout", { status: 504 })));

    renderWithProviders(<MovementsPage />, { route: "/movimientos" });

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cargar el historial");
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });
});
