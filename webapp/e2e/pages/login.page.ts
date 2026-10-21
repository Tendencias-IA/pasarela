import { readFileSync } from "node:fs";

import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/** Pantalla de HU-02 (features/auth/LoginPage.tsx). */
interface Credentials {
  phone: string;
  password: string;
}

/** Usuarios sembrados por api/scripts/seed_test_user.py; sus datos viven en fixtures/seeded-users.json. */
const seeded = JSON.parse(
  readFileSync(new URL("../fixtures/seeded-users.json", import.meta.url), "utf-8"),
) as Record<"main" | "withoutHistory", Credentials>;

export const SEEDED_USER = seeded.main;
export const SEEDED_USER_WITHOUT_HISTORY = seeded.withoutHistory;

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
