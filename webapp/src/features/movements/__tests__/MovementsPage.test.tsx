import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { formatDateTime } from "../../../shared/dates";
import { renderWithProviders } from "../../../test/render";
import { server } from "../../../test/server";
import { MovementsPage } from "../MovementsPage";
import { movement, pageOf } from "./fixtures";

const PATH = "/api/v1/movements";

/** Muestra la query string actual del router para comprobar qué guarda la URL. */
function LocationProbe() {
  return <span data-testid="search">{useLocation().search}</span>;
}

function renderPage(route: string) {
  return renderWithProviders(
    <>
      <MovementsPage />
      <LocationProbe />
    </>,
    { route },
  );
}

function search() {
  return screen.getByTestId("search").textContent;
}

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

  describe("filtros (HU-10)", () => {
    function respondWithQueryLog(log: string[], total = 2) {
      server.use(
        http.get(PATH, ({ request }) => {
          log.push(new URL(request.url).search);
          const page = Number(new URL(request.url).searchParams.get("page"));
          return HttpResponse.json(pageOf(page, total));
        }),
      );
    }

    const EMPTY = { items: [], page: 1, page_size: 20, total: 0 };

    it("ofrece Desde, Hasta y Tipo con las cuatro opciones de tipo (CA-1, CA-3)", async () => {
      respondWithQueryLog([]);

      renderPage("/movimientos");

      await screen.findAllByRole("listitem");
      expect(screen.getByRole("search", { name: "Filtros del historial" })).toBeInTheDocument();
      expect(document.querySelectorAll("ion-input")).toHaveLength(2);
      const options = Array.from(document.querySelectorAll("ion-select-option")).map(
        (o) => o.textContent,
      );
      expect(options).toEqual([
        "Todas",
        "Transferencias enviadas",
        "Transferencias recibidas",
        "Recargas",
      ]);
    });

    it("consulta la API con los filtros de la URL combinados (CA-4)", async () => {
      const log: string[] = [];
      respondWithQueryLog(log, 45);

      renderPage("/movimientos?type=sent&from=2026-10-01&to=2026-10-31&page=2");

      await screen.findAllByRole("listitem");
      expect(log).toEqual(["?from=2026-10-01&to=2026-10-31&type=sent&page=2"]);
    });

    it("un tipo o fecha inválidos en la URL se ignoran (CA-3)", async () => {
      const log: string[] = [];
      respondWithQueryLog(log);

      renderPage("/movimientos?type=foo&from=hoy");

      await screen.findAllByRole("listitem");
      expect(log).toEqual(["?page=1"]);
    });

    it("con desde > hasta no llama a la API ni queda cargando (CA-2)", async () => {
      const log: string[] = [];
      respondWithQueryLog(log);

      renderPage("/movimientos?from=2026-10-20&to=2026-10-10");
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(log).toEqual([]);
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });

    it("sin coincidencias con filtros muestra el vacío de filtros y conserva la URL (CA-7)", async () => {
      server.use(http.get(PATH, () => HttpResponse.json(EMPTY)));

      renderPage("/movimientos?type=sent&from=2026-10-01");

      const empty = await screen.findByText("No hay movimientos con esos filtros");
      expect(empty.closest("[role=status]")).not.toBeNull();
      expect(screen.getByText("Quitar filtros").closest("ion-button")).not.toBeNull();
      expect(screen.queryByText("Aún no tienes movimientos")).not.toBeInTheDocument();
      expect(screen.queryAllByRole("listitem")).toHaveLength(0);
      expect(search()).toBe("?type=sent&from=2026-10-01");
    });

    it("'Quitar filtros' vacía la URL y pide el historial completo (CA-7)", async () => {
      const log: string[] = [];
      server.use(
        http.get(PATH, ({ request }) => {
          const query = new URL(request.url).search;
          log.push(query);
          return HttpResponse.json(query.includes("type=sent") ? EMPTY : pageOf(1, 2));
        }),
      );
      renderPage("/movimientos?type=sent");
      const clear = await screen.findByText("Quitar filtros");

      fireEvent.click(clear.closest("ion-button") as HTMLElement);

      expect(await screen.findAllByRole("listitem")).toHaveLength(2);
      expect(log).toEqual(["?type=sent&page=1", "?page=1"]);
      expect(search()).toBe("");
    });

    it("sin filtros y sin movimientos conserva el vacío de HU-09 (HU-09 CA-7)", async () => {
      server.use(http.get(PATH, () => HttpResponse.json(EMPTY)));

      renderPage("/movimientos");

      expect(await screen.findByText("Aún no tienes movimientos")).toBeInTheDocument();
      expect(screen.queryByText("Quitar filtros")).not.toBeInTheDocument();
    });

    it("una página fuera de rango se corrige conservando los filtros (FR-009)", async () => {
      const log: string[] = [];
      respondWithQueryLog(log, 45);

      renderPage("/movimientos?type=recharge&page=9");

      await waitFor(() => {
        expect(screen.getByRole("navigation", { name: "Paginación" })).toHaveTextContent(
          "Página 3 de 3",
        );
      });
      expect(search()).toBe("?type=recharge&page=3");
    });

    it("avanzar de página conserva los filtros (CA-5)", async () => {
      respondWithQueryLog([], 45);
      renderPage("/movimientos?type=recharge");
      await screen.findByText("Página 1 de 3");

      fireEvent.click(screen.getByText("Siguiente").closest("ion-button") as HTMLElement);

      await screen.findByText("Página 2 de 3");
      expect(search()).toBe("?type=recharge&page=2");
    });
  });
});
