import type { Page } from "@playwright/test";

export class RegisterPage {
  constructor(private readonly page: Page) {}
  async goto() {
    await this.page.goto("/registro");
  }
  async submit(values: {
    name: string;
    phone: string;
    nationalId: string;
    email: string;
    password: string;
  }) {
    await this.page.getByLabel("Nombre completo").fill(values.name);
    await this.page.getByLabel("Número de teléfono").fill(values.phone);
    await this.page.getByLabel("Número de identificación").fill(values.nationalId);
    await this.page.getByLabel("Correo electrónico").fill(values.email);
    await this.page.getByLabel("Contraseña").fill(values.password);
    await this.page.getByRole("button", { name: "Crear cuenta" }).click();
  }
}
