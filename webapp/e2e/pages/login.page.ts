import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/** Pantalla de HU-02 (features/auth/LoginPage.tsx). */
/** Usuarios sembrados por api/scripts/seed_test_user.py. */
export const SEEDED_USER = { phone: "3009876543", password: "Clave1234" };
export const SEEDED_USER_WITHOUT_HISTORY = { phone: "3009876544", password: "Clave1234" };

export class LoginPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/login");
  }

  async signIn(phone: string, password: string) {
    await this.page.getByLabel("Teléfono").fill(phone);
    await this.page.getByLabel("Contraseña").fill(password);
    await this.page.getByRole("button", { name: "Iniciar sesión" }).click();
    // Tras iniciar sesión la webapp navega al panel.
    await expect(this.page).toHaveURL(/\/$/);
  }

  /** Inicia sesión con el usuario sembrado principal. */
  async signInAsSeededUser() {
    await this.goto();
    await this.signIn(SEEDED_USER.phone, SEEDED_USER.password);
  }
}
