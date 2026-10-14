import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { LoginPage } from "./pages/login.page";

const USER = { phone: "3009876543", password: "Clave1234" };

test.describe("Esqueleto", () => {
  test("la webapp carga y la API responde a través del mismo origen", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER.phone, USER.password);

    await expect(page.getByRole("heading", { level: 1, name: "Billetera Digital" })).toBeVisible();
    await expect(page.getByText("API ok, base de datos ok")).toBeVisible();
  });

  test("la pantalla inicial no tiene violaciones serias de accesibilidad", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER.phone, USER.password);
    await expect(page.getByText("API ok, base de datos ok")).toBeVisible();

    const results = await new AxeBuilder({ page })
      .disableRules(["scrollable-region-focusable"])
      .analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(serious).toEqual([]);
  });
});
