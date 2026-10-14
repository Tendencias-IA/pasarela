import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { LoginPage } from "./pages/login.page";

// `/` consulta el saldo (HU-05), que es privado: el esqueleto se verifica con sesión.
async function signIn(page: import("@playwright/test").Page) {
  const login = new LoginPage(page);
  await login.goto();
  await login.signIn("3009876543", "Clave1234");
}

test.describe("Esqueleto", () => {
  test("la webapp carga y la API responde a través del mismo origen", async ({ page }) => {
    await signIn(page);
    await page.goto("/");

    await expect(page.getByRole("heading", { level: 1, name: "Billetera Digital" })).toBeVisible();
    await expect(page.getByText("API ok, base de datos ok")).toBeVisible();
  });

  test("la pantalla inicial no tiene violaciones serias de accesibilidad", async ({ page }) => {
    await signIn(page);
    await page.goto("/");
    await expect(page.getByText(/^API /)).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(serious).toEqual([]);
  });
});
