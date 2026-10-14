import type { Counterparty, MovementOut } from "./api";
import type { MovementType } from "./filters";

export function directionLabel(direction: MovementOut["direction"]): string {
  switch (direction) {
    case "recarga":
      return "Recarga";
    case "enviada":
      return "Transferencia enviada";
    case "recibida":
      return "Transferencia recibida";
  }
}

export function statusLabel(status: MovementOut["status"]): string {
  return status === "exitosa" ? "Exitosa" : "Rechazada";
}

/** "a ***4567" / "de Mar** G***** · ***1234". El servidor ya enmascaró (RNF-06). */
export function counterpartyLabel(
  direction: MovementOut["direction"],
  counterparty: Counterparty | null,
): string | null {
  if (counterparty === null || direction === "recarga") return null;
  const who =
    counterparty.name_masked === null
      ? counterparty.phone_masked
      : `${counterparty.name_masked} · ${counterparty.phone_masked}`;
  return `${direction === "enviada" ? "a" : "de"} ${who}`;
}

/** Opciones del filtro de tipo, en el orden de HU-10 CA-3. */
export const TYPE_OPTIONS: readonly { value: MovementType; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "sent", label: "Transferencias enviadas" },
  { value: "received", label: "Transferencias recibidas" },
  { value: "recharge", label: "Recargas" },
];

export function typeLabel(type: MovementType): string {
  return TYPE_OPTIONS.find((option) => option.value === type)?.label ?? "Todas";
}
