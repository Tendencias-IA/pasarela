import { useCallback, useRef, useState } from "react";

import { ApiError } from "../../shared/api/client";
import {
  RECHARGE_MAX,
  RECHARGE_MIN,
  formatCOP,
  isWithinRange,
  parseAmountInput,
} from "../../shared/money";
import { postRecharge, type RechargeOut } from "./api";

export const RANGE_MESSAGE = `El monto debe estar entre ${formatCOP(RECHARGE_MIN)} y ${formatCOP(RECHARGE_MAX)} COP.`;
export const FORMAT_MESSAGE = "Ingresa un monto en pesos colombianos (hasta dos decimales).";

export type RechargeState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; result: RechargeOut }
  | { kind: "rejected"; message: string };

/**
 * Estado del flujo de recarga. La `Idempotency-Key` se crea al abrir el formulario y solo se
 * renueva cuando cambia el monto: un doble clic o un reintento reutilizan la misma (FR-011).
 */
export function useRecharge() {
  const [amount, setAmountRaw] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [state, setState] = useState<RechargeState>({ kind: "idle" });
  const keyRef = useRef<string>(crypto.randomUUID());

  const setAmount = useCallback((value: string) => {
    setAmountRaw(value);
    setFieldError(null);
    keyRef.current = crypto.randomUUID();
  }, []);

  const submit = useCallback(async () => {
    if (state.kind === "submitting") return;
    const canonical = parseAmountInput(amount);
    if (canonical === null) {
      setFieldError(FORMAT_MESSAGE);
      return;
    }
    if (!isWithinRange(canonical, RECHARGE_MIN, RECHARGE_MAX)) {
      setFieldError(RANGE_MESSAGE);
      return;
    }
    setFieldError(null);
    setState({ kind: "submitting" });
    try {
      const result = await postRecharge(canonical, keyRef.current);
      setState({ kind: "success", result });
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        const byField = error.messagesByField();
        if (byField.amount !== undefined) setFieldError(byField.amount);
        setState({ kind: "rejected", message: error.message });
      } else {
        setState({ kind: "rejected", message: "No se pudo conectar con el servicio." });
      }
    }
  }, [amount, state.kind]);

  const reset = useCallback(() => {
    setAmountRaw("");
    setFieldError(null);
    setState({ kind: "idle" });
    keyRef.current = crypto.randomUUID();
  }, []);

  return { amount, setAmount, fieldError, state, submit, reset };
}
