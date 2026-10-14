import type { MovementOut, MovementsPageOut } from "../api";

export function movement(overrides: Partial<MovementOut> = {}): MovementOut {
  return {
    id: 1,
    direction: "recarga",
    type: "recarga",
    status: "exitosa",
    amount: "50000.00",
    created_at: "2026-10-14T21:40:00Z",
    rejection_reason: null,
    counterparty: null,
    ...overrides,
  };
}

/** Página `page` de un historial con `total` recargas, 20 por página. */
export function pageOf(page: number, total: number): MovementsPageOut {
  const start = (page - 1) * 20;
  const count = Math.max(0, Math.min(20, total - start));
  return {
    items: Array.from({ length: count }, (_, i) => movement({ id: total - start - i })),
    page,
    page_size: 20,
    total,
  };
}
