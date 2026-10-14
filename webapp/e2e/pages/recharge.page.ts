import type { Page } from "@playwright/test";

export class RechargePage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/recargar");
  }

  amountField() {
    return this.page.getByLabel("Monto a recargar (COP)");
  }

  async fillAmount(value: string) {
    await this.amountField().fill(value);
  }

  submitButton() {
    return this.page.getByRole("button", { name: /^Recargar|Recargando/ });
  }

  async submit() {
    await this.page.getByRole("button", { name: "Recargar", exact: true }).click();
  }

  result() {
    return this.page.getByRole("status");
  }

  alert() {
    return this.page.getByRole("alert");
  }

  fieldError(text: RegExp) {
    return this.page.getByText(text);
  }
}
