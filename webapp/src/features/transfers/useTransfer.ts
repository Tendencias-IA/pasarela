import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import { ApiError } from "../../shared/api/client";
import {
  TRANSFER_MAX,
  TRANSFER_MIN,
  formatCOP,
  isWithinRange,
  parseAmountInput,
} from "../../shared/money";
import { MOVEMENTS_QUERY_KEY } from "../movements/useMovements";
import { WALLET_QUERY_KEY } from "../wallet/useWallet";
import {
  postTransfer,
  postTransferPreview,
  type TransferIn,
  type TransferOut,
  type TransferPreviewOut,
} from "./api";

export const PHONE_MESSAGE = "Ingresa un celular de diez dígitos que empiece por 3.";
export const FORMAT_MESSAGE = "Ingresa un monto en pesos colombianos (hasta dos decimales).";
export const RANGE_MESSAGE = `El monto debe estar entre ${formatCOP(TRANSFER_MIN)} y ${formatCOP(TRANSFER_MAX)} COP.`;

/** Mensajes por `code` del problem: la interfaz nunca decide por `detail` (api-design.md). */
const MESSAGES_BY_CODE: Record<string, string> = {
  recipient_not_found: "El teléfono no corresponde a un usuario registrado.",
  self_transfer: "No puedes transferirte a tu propia cuenta.",
  insufficient_balance: "Tu saldo es menor que el monto de la transferencia.",
  wallet_not_found: "Tu cuenta no tiene una billetera asociada.",
  amount_out_of_range: RANGE_MESSAGE,
};
const GENERIC_PREVIEW_MESSAGE = "No se pudo preparar la transferencia. Intenta de nuevo.";
const GENERIC_CONFIRM_MESSAGE = "No se pudo completar la transferencia. Intenta de nuevo.";
const CONNECTION_MESSAGE = "No se pudo conectar con el servicio.";
const RETRY_MESSAGE = `${CONNECTION_MESSAGE} Puedes reintentar: no se duplicará.`;

export interface FieldErrors {
  recipientPhone?: string;
  amount?: string;
}

export type TransferState =
  | { kind: "form"; message: string | null }
  | { kind: "previewing" }
  | { kind: "summary"; preview: TransferPreviewOut; message: string | null }
  | { kind: "confirming"; preview: TransferPreviewOut }
  | { kind: "success"; result: TransferOut }
  | { kind: "rejected"; message: string };

const PHONE_PATTERN = /^3\d{9}$/;

/** Teléfono tal como lo pide la API: solo dígitos (se quitan espacios y guiones). */
function normalizePhone(raw: string): string {
  return raw.replace(/[\s-]/g, "");
}

/**
 * Estado del flujo de transferencia. HU-06: formulario → resumen. La validación local solo da
 * feedback inmediato; el servidor decide (RNF-01.4).
 */
export function useTransfer() {
  const [recipientPhone, setPhoneRaw] = useState("");
  const [amount, setAmountRaw] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [state, setState] = useState<TransferState>({ kind: "form", message: null });
  // Guarda síncrona: dos envíos en el mismo tick pasarían antes de re-renderizar.
  const inFlightRef = useRef(false);
  // La clave nace al mostrar el resumen y se conserva hasta confirmar: un doble clic o un
  // reintento tras un corte reutilizan la misma y el servidor no duplica (ADR-0005).
  const keyRef = useRef<string>("");
  const requestRef = useRef<TransferIn | null>(null);
  const queryClient = useQueryClient();

  const setRecipientPhone = useCallback((value: string) => {
    setPhoneRaw(value);
    setFieldErrors((current) => ({ ...current, recipientPhone: undefined }));
  }, []);

  const setAmount = useCallback((value: string) => {
    setAmountRaw(value);
    setFieldErrors((current) => ({ ...current, amount: undefined }));
  }, []);

  const review = useCallback(async () => {
    if (inFlightRef.current) return;
    const phone = normalizePhone(recipientPhone);
    const canonical = parseAmountInput(amount);
    const errors: FieldErrors = {};
    if (!PHONE_PATTERN.test(phone)) errors.recipientPhone = PHONE_MESSAGE;
    if (canonical === null) errors.amount = FORMAT_MESSAGE;
    else if (!isWithinRange(canonical, TRANSFER_MIN, TRANSFER_MAX)) errors.amount = RANGE_MESSAGE;
    setFieldErrors(errors);
    if (errors.recipientPhone !== undefined || errors.amount !== undefined || canonical === null) {
      return;
    }
    inFlightRef.current = true;
    setState({ kind: "previewing" });
    try {
      const body = { recipient_phone: phone, amount: canonical };
      const preview = await postTransferPreview(body);
      requestRef.current = body;
      keyRef.current = crypto.randomUUID();
      setState({ kind: "summary", preview, message: null });
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        const byField = error.messagesByField();
        setFieldErrors({ recipientPhone: byField.recipient_phone, amount: byField.amount });
        const message =
          error.code === "validation"
            ? null
            : (MESSAGES_BY_CODE[error.code] ?? GENERIC_PREVIEW_MESSAGE);
        setState({ kind: "form", message });
      } else {
        setState({ kind: "form", message: CONNECTION_MESSAGE });
      }
    } finally {
      inFlightRef.current = false;
    }
  }, [recipientPhone, amount]);

  const edit = useCallback(() => {
    setState({ kind: "form", message: null });
  }, []);

  const confirm = useCallback(async () => {
    const body = requestRef.current;
    if (inFlightRef.current || state.kind !== "summary" || body === null) return;
    const { preview } = state;
    inFlightRef.current = true;
    setState({ kind: "confirming", preview });
    try {
      const result = await postTransfer(body, keyRef.current);
      setState({ kind: "success", result });
      // webapp.md: saldo e historial deben reflejar la transferencia en su siguiente consulta.
      void queryClient.invalidateQueries({ queryKey: WALLET_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: MOVEMENTS_QUERY_KEY });
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status < 500 && error.code !== "invalid_session") {
        if (error.status === 409) {
          setState({ kind: "summary", preview, message: RETRY_MESSAGE });
        } else {
          setState({
            kind: "rejected",
            message: MESSAGES_BY_CODE[error.code] ?? GENERIC_CONFIRM_MESSAGE,
          });
        }
      } else {
        // Corte de red, 5xx o sesión vencida: el resultado es incierto, se puede reintentar
        // con la misma clave sin riesgo de duplicar.
        setState({ kind: "summary", preview, message: RETRY_MESSAGE });
      }
    } finally {
      inFlightRef.current = false;
    }
  }, [state, queryClient]);

  const reset = useCallback(() => {
    setPhoneRaw("");
    setAmountRaw("");
    setFieldErrors({});
    requestRef.current = null;
    setState({ kind: "form", message: null });
  }, []);

  return {
    recipientPhone,
    setRecipientPhone,
    amount,
    setAmount,
    fieldErrors,
    state,
    review,
    edit,
    confirm,
    reset,
  };
}
