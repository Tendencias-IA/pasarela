/**
 * Dinero en la webapp (ADR-0003, RNF-04.3): los montos son cadenas decimales con dos
 * decimales y nunca se decide con `Number`. Las comparaciones usan enteros de centavos (BigInt).
 */
export const RECHARGE_MIN = "5000.00";
export const RECHARGE_MAX = "5000000.00";
export const TRANSFER_MIN = "100.00";
export const TRANSFER_MAX = "3000000.00";

const MAX_INTEGER_DIGITS = 13;

/** Centavos como BigInt a partir de una cadena canónica `dddd.dd`. */
function toCents(amount: string): bigint {
  const [units = "0", cents = "00"] = amount.split(".");
  return BigInt(units) * 100n + BigInt(cents.padEnd(2, "0"));
}

/**
 * Normaliza lo que escribe el usuario ("50.000", "50000,50", " 50000.5 ") a `"50000.50"`.
 * Devuelve `null` si no es un número positivo con hasta dos decimales.
 */
export function parseAmountInput(raw: string): string | null {
  const text = raw.trim().replace(/\s/g, "");
  if (text === "" || !/^[0-9.,]+$/.test(text)) return null;

  // Último separador: si tiene 1-2 dígitos detrás es decimal; si tiene 3, es de miles.
  const lastSep = Math.max(text.lastIndexOf("."), text.lastIndexOf(","));
  let units = text;
  let cents = "";
  if (lastSep !== -1) {
    const tail = text.slice(lastSep + 1);
    const separator = text[lastSep] ?? "";
    if (tail.length === 3 && /^\d{3}$/.test(tail)) {
      units = text;
    } else if (/^\d{1,2}$/.test(tail)) {
      units = text.slice(0, lastSep);
      // El separador decimal no puede ser el mismo que el de miles ("1.234.5" es ambiguo).
      if (units.includes(separator)) return null;
      cents = tail;
    } else {
      return null;
    }
  }
  // Los grupos de miles, si los hay, deben ser de exactamente tres dígitos ("50.000", "5.000.000").
  const groups = units.split(/[.,]/);
  if (groups.length > 1 && !groups.slice(1).every((g) => /^\d{3}$/.test(g))) return null;
  units = groups.join("");
  if (!/^\d+$/.test(units) || units.length > MAX_INTEGER_DIGITS) return null;
  const canonical = `${BigInt(units).toString()}.${cents.padEnd(2, "0")}`;
  return toCents(canonical) > 0n ? canonical : null;
}

/** Comparación inclusiva sobre cadenas canónicas. */
export function isWithinRange(amount: string, min: string, max: string): boolean {
  const value = toCents(amount);
  return value >= toCents(min) && value <= toCents(max);
}

/** `"50000.00"` → `"$ 50.000,00"` (es-CO). Solo para mostrar. */
export function formatCOP(amount: string): string {
  const cents = toCents(amount);
  const units = cents / 100n;
  const rest = (cents % 100n).toString().padStart(2, "0");
  const grouped = units.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `$ ${grouped},${rest}`;
}
