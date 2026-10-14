import type { operations } from "../../shared/api/types.gen";

export type MovementType = NonNullable<operations["listMovements"]["parameters"]["query"]>["type"] &
  string;

/** Valores del formulario; la cadena vacía significa "sin fecha". */
export interface MovementsFilterValues {
  from: string;
  to: string;
  type: MovementType;
}

export const DEFAULT_FILTERS: MovementsFilterValues = { from: "", to: "", type: "all" };
export const RANGE_MESSAGE = "La fecha inicial no puede ser posterior a la final.";

const TYPES: readonly MovementType[] = ["all", "sent", "received", "recharge"];
const DATE = /^\d{4}-\d{2}-\d{2}$/;

function dateParam(params: URLSearchParams, name: "from" | "to"): string {
  const raw = params.get(name) ?? "";
  return DATE.test(raw) ? raw : "";
}

/** Filtros desde la URL; lo que no pasa la lista blanca vuelve al valor por defecto (CA-3). */
export function parseFilters(params: URLSearchParams): MovementsFilterValues {
  const type = params.get("type");
  return {
    from: dateParam(params, "from"),
    to: dateParam(params, "to"),
    type: TYPES.find((t) => t === type) ?? "all",
  };
}

export function parsePage(params: URLSearchParams): number {
  const raw = Number(params.get("page") ?? "1");
  return Number.isInteger(raw) && raw >= 1 ? raw : 1;
}

/** URL limpia: solo lo que difiere del valor por defecto (CA-6: sin `page` al cambiar filtros). */
export function toSearchParams(filters: MovementsFilterValues, page: number): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.from !== "") params.set("from", filters.from);
  if (filters.to !== "") params.set("to", filters.to);
  if (filters.type !== "all") params.set("type", filters.type);
  if (page > 1) params.set("page", String(page));
  return params;
}

export function hasActiveFilters(filters: MovementsFilterValues): boolean {
  return filters.from !== "" || filters.to !== "" || filters.type !== "all";
}

/** CA-2: las fechas ISO se comparan como cadenas. La API revalida (RNF-01.4). */
export function rangeError(filters: MovementsFilterValues): string | null {
  return filters.from !== "" && filters.to !== "" && filters.from > filters.to
    ? RANGE_MESSAGE
    : null;
}
