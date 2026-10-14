import { request } from "../../shared/api/client";
import type { components } from "../../shared/api/types.gen";

export type TransferIn = components["schemas"]["TransferIn"];
export type TransferPreviewOut = components["schemas"]["TransferPreviewOut"];

/** POST /api/v1/transfers/preview (HU-06): consulta pura, sin Idempotency-Key. */
export function postTransferPreview(body: TransferIn, signal?: AbortSignal) {
  return request<TransferPreviewOut>("/api/v1/transfers/preview", {
    method: "POST",
    body,
    signal,
  });
}

export type TransferOut = components["schemas"]["TransferOut"];

/** POST /api/v1/transfers (HU-07). La clave idempotente nace al mostrar el resumen. */
export function postTransfer(body: TransferIn, idempotencyKey: string, signal?: AbortSignal) {
  return request<TransferOut>("/api/v1/transfers", {
    method: "POST",
    body,
    idempotencyKey,
    signal,
  });
}
