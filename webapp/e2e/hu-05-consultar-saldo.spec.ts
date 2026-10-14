import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { HomePage } from "./pages/home.page";
import { LoginPage } from "./pages/login.page";
import { RechargePage } from "./pages/recharge.page";

// Usuario creado por api/scripts/seed_test_user.py (ver quickstart.md).
const USER = { phone: "3009876543", password: "Clave1234" };

async function signIn(page: Page) {
  const login = new LoginPage(page);
  await login.goto();
  await login.signIn(USER.phone, USER.password);
}

test.describe("HU-05 Consultar el saldo", () => {
  test("CA-1, CA-2: el panel muestra la tarjeta Saldo disponible con un monto en COP", async ({
    page,
  }) => {
    await signIn(page);

    const home = new HomePage(page);
    await home.goto();

    await expect(home.balanceCard()).toBeVisible();
    await expect(home.balance()).toHaveText(/^\$ [\d.]+,\d{2}$/);
    await expect(home.balance()).toHaveAttribute("data-balance", /^\d+\.\d{2}$/);
  });

  test("CA-3: tras recargar en /recargar el panel muestra el saldo anterior más lo recargado", async ({
    page,
  }) => {
    await signIn(page);
    const home = new HomePage(page);
    await home.goto();
    await expect(home.balance()).toBeVisible();
    const before = await home.balanceCents();

    const recharge = new RechargePage(page);
    await recharge.goto();
    await recharge.fillAmount("20000");
    await recharge.submit();
    await expect(recharge.result()).toContainText("Recarga exitosa de $ 20.000,00.");
    await home.goto();

    await expect(home.balance()).toBeVisible();
    await expect.poll(() => home.balanceCents()).toBe(before + 2_000_000n);
  });

  test("RNF-01.1, HU-04 CA-2: sin sesión, / redirige a /login", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/login$/);
  });

  test("RNF-03.6: el panel con la tarjeta de saldo no tiene violaciones serias de accesibilidad", async ({
    page,
  }) => {
    await signIn(page);
    const home = new HomePage(page);
    await home.goto();
    await expect(home.balance()).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(serious).toEqual([]);
  });
});
