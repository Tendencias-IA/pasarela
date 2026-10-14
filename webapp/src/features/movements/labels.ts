import type { Counterparty, MovementOut } from "./api";

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
