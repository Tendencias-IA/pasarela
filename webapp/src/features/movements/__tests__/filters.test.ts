import { describe, expect, it } from "vitest";

import {
  DEFAULT_FILTERS,
  RANGE_MESSAGE,
  hasActiveFilters,
  parseFilters,
  parsePage,
  rangeError,
  toSearchParams,
} from "../filters";

describe("filters (HU-10)", () => {
  it("sin parámetros devuelve los valores por defecto (CA-3)", () => {
    expect(parseFilters(new URLSearchParams())).toEqual(DEFAULT_FILTERS);
    expect(DEFAULT_FILTERS).toEqual({ from: "", to: "", type: "all" });
  });

  it("lee fecha inicial, final y tipo de la URL (CA-1, CA-3, CA-4)", () => {
    const params = new URLSearchParams("from=2026-10-01&to=2026-10-31&type=recharge");

    expect(parseFilters(params)).toEqual({
      from: "2026-10-01",
      to: "2026-10-31",
      type: "recharge",
    });
  });

  it.each(["all", "sent", "received", "recharge"])("acepta el tipo %s (CA-3)", (type) => {
    expect(parseFilters(new URLSearchParams({ type })).type).toBe(type);
  });

  it("descarta tipo desconocido y fechas mal formadas (la pantalla vuelve a Todas)", () => {
    const params = new URLSearchParams("type=foo&from=hoy&to=2026-1-1");

    expect(parseFilters(params)).toEqual(DEFAULT_FILTERS);
  });

  it("la página sale de la URL y es 1 si es inválida", () => {
    expect(parsePage(new URLSearchParams("page=3"))).toBe(3);
    expect(parsePage(new URLSearchParams("page=0"))).toBe(1);
    expect(parsePage(new URLSearchParams("page=abc"))).toBe(1);
    expect(parsePage(new URLSearchParams())).toBe(1);
  });

  it("serializa solo lo que difiere del valor por defecto (URL limpia)", () => {
    expect(toSearchParams(DEFAULT_FILTERS, 1).toString()).toBe("");
    expect(toSearchParams({ from: "2026-10-01", to: "", type: "sent" }, 1).toString()).toBe(
      "from=2026-10-01&type=sent",
    );
    expect(
      toSearchParams({ from: "2026-10-01", to: "2026-10-31", type: "received" }, 3).toString(),
    ).toBe("from=2026-10-01&to=2026-10-31&type=received&page=3");
  });

  it("cambiar un filtro vuelve a la primera página: la URL nueva no lleva page (CA-6)", () => {
    const current = parseFilters(new URLSearchParams("type=sent&page=3"));

    const next = toSearchParams({ ...current, type: "recharge" }, 1);

    expect(next.toString()).toBe("type=recharge");
    expect(next.has("page")).toBe(false);
  });

  it("detecta filtros activos (CA-7)", () => {
    expect(hasActiveFilters(DEFAULT_FILTERS)).toBe(false);
    expect(hasActiveFilters({ ...DEFAULT_FILTERS, type: "sent" })).toBe(true);
    expect(hasActiveFilters({ ...DEFAULT_FILTERS, from: "2026-10-01" })).toBe(true);
    expect(hasActiveFilters({ ...DEFAULT_FILTERS, to: "2026-10-01" })).toBe(true);
  });

  it("rangeError: desde posterior a hasta es error junto al campo (CA-2)", () => {
    expect(rangeError({ from: "2026-10-20", to: "2026-10-10", type: "all" })).toBe(RANGE_MESSAGE);
    expect(RANGE_MESSAGE).toBe("La fecha inicial no puede ser posterior a la final.");
  });

  it("rangeError: mismo día, un solo extremo o ninguno son válidos (CA-1)", () => {
    expect(rangeError({ from: "2026-10-10", to: "2026-10-10", type: "all" })).toBeNull();
    expect(rangeError({ from: "2026-10-10", to: "", type: "all" })).toBeNull();
    expect(rangeError({ from: "", to: "2026-10-10", type: "all" })).toBeNull();
    expect(rangeError(DEFAULT_FILTERS)).toBeNull();
  });
});
