import type { Page } from "@playwright/test";

/** Panel principal con la tarjeta de saldo (HU-05, app/HomePage.tsx). */
export class HomePage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/");
  }

  balanceCard() {
    return this.page.getByRole("region", { name: "Saldo disponible" });
  }

  /** Elemento con el saldo; su atributo `data-balance` trae la cadena decimal exacta. */
  balance() {
    return this.balanceCard().locator("[data-balance]");
  }

  /** Saldo en centavos (BigInt) leído de `data-balance`, sin aritmética con Number. */
  async balanceCents(): Promise<bigint> {
    const raw = await this.balance().getAttribute("data-balance");
    const [units = "0", cents = "00"] = (raw ?? "0.00").split(".");
    return BigInt(units) * 100n + BigInt(cents.padEnd(2, "0"));
  }
}
