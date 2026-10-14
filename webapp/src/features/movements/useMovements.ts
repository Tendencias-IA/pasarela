import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { getMovements } from "./api";

/** Clave raíz: HU-08 (y HU-07) la invalidan tras una operación exitosa (webapp.md). */
export const MOVEMENTS_QUERY_KEY = ["movements"] as const;

/**
 * Página `page` del historial. Al cambiar de página se conserva la anterior visible hasta
 * que llega la nueva (no se vacía la lista). `isOutOfRange` indica que la página pedida
 * supera la última y la pantalla debe corregir la URL (FR-009).
 */
export function useMovements(page: number) {
  const query = useQuery({
    queryKey: [...MOVEMENTS_QUERY_KEY, page],
    queryFn: ({ signal }) => getMovements(page, signal),
    placeholderData: keepPreviousData,
  });
  const total = query.data?.total ?? 0;
  const pageSize = query.data?.page_size ?? 20;
  const lastPage = Math.max(1, Math.ceil(total / pageSize));
  const isOutOfRange = query.data !== undefined && query.data.page > lastPage;
  return { ...query, lastPage, isOutOfRange };
}
