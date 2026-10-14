import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { LoginPage } from "./pages/login.page";
import { RechargePage } from "./pages/recharge.page";

// Usuario creado por api/scripts/seed_test_user.py (ver quickstart de HU-08).
const USER = { phone: "3009876543", password: "Clave1234" };

test.describe("HU-05 Consultar el saldo", () => {
  test("CA-1, CA-3: el panel muestra el saldo y refleja una recarga", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER.phone, USER.password);
    await page.goto("/");
    const card = page.getByLabel("Saldo disponible");
    await expect(card).toContainText("$");
    const before = await card.innerText();

    const recharge = new RechargePage(page);
    await recharge.goto();
    await recharge.fillAmount("20000");
    await recharge.submit();
    await expect(recharge.result()).toContainText("Recarga exitosa de $ 20.000,00.");
    await page.goto("/");

    await expect(card).toBeVisible();
    await expect.poll(async () => card.innerText()).not.toBe(before);
  });

  test("HU-04 CA-2, RNF-01.1: sin sesión el panel redirige a /login al consultar el saldo", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/login$/);
  });

  test("SC-006: el panel con saldo no tiene violaciones serias de accesibilidad", async ({
    page,
  }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER.phone, USER.password);
    await page.goto("/");
    await expect(page.getByLabel("Saldo disponible")).toContainText("$");

    const results = await new AxeBuilder({ page })
      .disableRules(["scrollable-region-focusable"])
      .analyze();

    expect(
      results.violations.filter((v) => v.impact === "serious" || v.impact === "critical"),
    ).toEqual([]);
  });
});
