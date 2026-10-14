import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/** Pantalla de HU-02 (features/auth/LoginPage.tsx). */
export class LoginPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/login");
  }

  async signIn(phone: string, password: string) {
    await this.page.getByLabel("Teléfono").fill(phone);
    await this.page.getByLabel("Contraseña").fill(password);
    await this.page.getByRole("button", { name: "Iniciar sesión" }).click();
    await expect(this.page.getByRole("status")).toContainText("Acceso verificado.");
  }
}
