import { describe, expect, it } from "vitest";

import { formatDateTime } from "..";

describe("formatDateTime (HU-09 FR-002)", () => {
  it("muestra fecha y hora legibles en es-CO en la zona del navegador", () => {
    const iso = "2026-10-14T21:40:00Z";
    const expected = new Intl.DateTimeFormat("es-CO", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));

    expect(formatDateTime(iso)).toBe(expected);
    expect(formatDateTime(iso)).toMatch(/2026/);
  });

  it("devuelve la cadena original si no es una fecha válida", () => {
    expect(formatDateTime("no-es-fecha")).toBe("no-es-fecha");
  });
});
