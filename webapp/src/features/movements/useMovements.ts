import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { getMovements, type MovementsQueryValues } from "./api";
import { rangeError } from "./filters";

/** Clave raíz: HU-08 (y HU-07) la invalidan tras una operación exitosa (webapp.md). */
export const MOVEMENTS_QUERY_KEY = ["movements"] as const;

/**
 * Página `page` del historial con filtros opcionales (HU-10). Al cambiar de página o de filtro
 * se conserva la lista anterior hasta que llega la nueva. Mientras `from > to` no se consulta
 * (CA-2): la pantalla muestra el error y la lista previa. `isOutOfRange` indica que la página
 * pedida supera la última y la pantalla debe corregir la URL (HU-09 FR-009).
 */
export function useMovements(values: MovementsQueryValues) {
  const { page, from, to, type } = values;
  const query = useQuery({
    queryKey: [...MOVEMENTS_QUERY_KEY, { page, from, to, type }],
    queryFn: ({ signal }) => getMovements({ page, from, to, type }, signal),
    placeholderData: keepPreviousData,
    enabled: rangeError({ from, to, type }) === null,
  });
  const total = query.data?.total ?? 0;
  const pageSize = query.data?.page_size ?? 20;
  const lastPage = Math.max(1, Math.ceil(total / pageSize));
  const isOutOfRange = query.data !== undefined && query.data.page > lastPage;
  return { ...query, lastPage, isOutOfRange };
}
