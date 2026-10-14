import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../shared/api/client";
import { getSession } from "./api";

export const SESSION_QUERY_KEY = ["session"] as const;

/**
 * Estado de la sesión del servidor. Sin caché al desmontar (`gcTime: 0`): al salir del
 * área privada y volver a entrar se consulta de nuevo, y al volver a la pestaña se
 * revalida para sacar al usuario en cuanto la sesión venció por inactividad (HU-04).
 */
export function useSession() {
  const query = useQuery({
    queryKey: SESSION_QUERY_KEY,
    queryFn: ({ signal }) => getSession(signal),
    gcTime: 0,
    refetchOnWindowFocus: true,
  });
  const isUnauthorized = query.error instanceof ApiError && query.error.status === 401;
  return { ...query, isUnauthorized };
}
