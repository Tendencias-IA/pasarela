import type { Page } from "@playwright/test";

export class TransferPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/transferir");
  }

  phoneField() {
    return this.page.getByLabel("Teléfono del destinatario");
  }

  amountField() {
    return this.page.getByLabel("Monto (COP)");
  }

  async prepare(phone: string, amount: string) {
    await this.phoneField().fill(phone);
    await this.amountField().fill(amount);
    await this.page.getByRole("button", { name: "Revisar" }).click();
  }

  summary() {
    return this.page.getByRole("region", { name: "Resumen de la transferencia" });
  }

  async edit() {
    await this.page.getByRole("button", { name: "Editar" }).click();
  }

  async confirm() {
    await this.page.getByRole("button", { name: /^Confirmar/ }).click();
  }

  confirmButton() {
    return this.page.getByRole("button", { name: /^Confirmar/ });
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
