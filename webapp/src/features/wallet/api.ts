import { request } from "../../shared/api/client";
import type { components } from "../../shared/api/types.gen";

export type RechargeOut = components["schemas"]["RechargeOut"];

/** POST /api/v1/wallet/recharges (HU-08). La clave idempotente la genera el hook por intento. */
export function postRecharge(amount: string, idempotencyKey: string, signal?: AbortSignal) {
  return request<RechargeOut>("/api/v1/wallet/recharges", {
    method: "POST",
    body: { amount },
    idempotencyKey,
    signal,
  });
}

export type WalletOut = components["schemas"]["WalletOut"];

/** GET /api/v1/wallet (HU-05). El usuario sale de la sesión: la petición no lleva ids. */
export function getWallet(signal?: AbortSignal) {
  return request<WalletOut>("/api/v1/wallet", { signal });
}
