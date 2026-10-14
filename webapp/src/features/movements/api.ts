import { request } from "../../shared/api/client";
import type { components } from "../../shared/api/types.gen";
import { toSearchParams, type MovementsFilterValues } from "./filters";

export type MovementOut = components["schemas"]["MovementOut"];
export type MovementsPageOut = components["schemas"]["MovementsPageOut"];
export type Counterparty = components["schemas"]["Counterparty"];

export interface MovementsQueryValues extends MovementsFilterValues {
  page: number;
}

/**
 * GET /api/v1/movements?page=N&from=&to=&type= (HU-09, HU-10). Página fija de 20 (RF-05).
 * Solo se envían los filtros con valor; `page=1` se envía siempre.
 */
export function getMovements({ page, ...filters }: MovementsQueryValues, signal?: AbortSignal) {
  const params = toSearchParams(filters, 1);
  params.set("page", String(page));
  return request<MovementsPageOut>(`/api/v1/movements?${params.toString()}`, { signal });
}
