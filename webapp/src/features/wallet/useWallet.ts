import { useQuery } from "@tanstack/react-query";

import { getWallet } from "./api";

/** Clave raíz: HU-08 (y HU-07) la invalidan tras mover saldo (webapp.md, HU-05 CA-3). */
export const WALLET_QUERY_KEY = ["wallet"] as const;

/** Saldo persistido de la billetera del usuario autenticado (HU-05). */
export function useWallet() {
  return useQuery({
    queryKey: WALLET_QUERY_KEY,
    queryFn: ({ signal }) => getWallet(signal),
  });
}
