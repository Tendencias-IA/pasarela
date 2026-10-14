const FORMATTER = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });

/** ISO 8601 UTC del servidor → fecha y hora en la zona del navegador (es-CO). Solo para mostrar. */
export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : FORMATTER.format(date);
}
