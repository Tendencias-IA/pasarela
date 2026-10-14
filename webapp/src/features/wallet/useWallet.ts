import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../shared/api/client";
import { getWallet } from "./api";

/** Clave raíz: las operaciones que mueven saldo (recarga, transferencia) la invalidan. */
export const WALLET_QUERY_KEY = ["wallet"] as const;

/**
 * Saldo del usuario autenticado (HU-05). `isUnavailable` es el caso "la cuenta no tiene
 * billetera" (404 wallet_not_found): se informa sin tratarlo como caída del servicio.
 */
export function useWallet() {
  const query = useQuery({
    queryKey: WALLET_QUERY_KEY,
    queryFn: ({ signal }) => getWallet(signal),
  });
  const isUnavailable = query.error instanceof ApiError && query.error.code === "wallet_not_found";
  return { ...query, isUnavailable };
}
