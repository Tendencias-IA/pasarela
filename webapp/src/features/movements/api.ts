import { request } from "../../shared/api/client";
import type { components } from "../../shared/api/types.gen";

export type MovementOut = components["schemas"]["MovementOut"];
export type MovementsPageOut = components["schemas"]["MovementsPageOut"];
export type Counterparty = components["schemas"]["Counterparty"];

/** GET /api/v1/movements?page=N (HU-09). Página fija de 20 (RF-05). */
export function getMovements(page: number, signal?: AbortSignal) {
  return request<MovementsPageOut>(`/api/v1/movements?page=${String(page)}`, { signal });
}
