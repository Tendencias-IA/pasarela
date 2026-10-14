import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { LoginPage } from "./pages/login.page";
import { RechargePage } from "./pages/recharge.page";

test.describe("HU-08 Recargar saldo", () => {
  test("desde el panel se llega a Recargar en un clic (RNF-03.1)", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn("3009876543", "Clave1234");
    await page.goto("/");
    await page.getByRole("link", { name: "Recargar saldo" }).click();

    await expect(page).toHaveURL(/\/recargar$/);
    await expect(page.getByRole("heading", { level: 1, name: "Recargar saldo" })).toBeVisible();
  });

  test("la pantalla no tiene violaciones serias de accesibilidad (SC-006)", async ({ page }) => {
    const recharge = new RechargePage(page);
    await recharge.goto();
    await expect(recharge.amountField()).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(serious).toEqual([]);
  });

  test("CA-2: 4999 y abc se rechazan en el formulario sin llamar a la API", async ({ page }) => {
    const recharge = new RechargePage(page);
    let requests = 0;
    await page.route("**/api/v1/wallet/recharges", async (route) => {
      requests += 1;
      await route.continue();
    });
    await recharge.goto();

    await recharge.fillAmount("4999");
    await recharge.submit();
    await expect(recharge.fieldError(/entre \$ 5\.000,00 y \$ 5\.000\.000,00/)).toBeVisible();

    await recharge.fillAmount("abc");
    await recharge.submit();
    await expect(recharge.fieldError(/pesos colombianos/)).toBeVisible();

    expect(requests).toBe(0);
  });

  test("CA-9: el botón se deshabilita durante el envío", async ({ page }) => {
    const recharge = new RechargePage(page);
    await page.route("**/api/v1/wallet/recharges", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 800));
      await route.fulfill({
        status: 404,
        contentType: "application/problem+json",
        body: JSON.stringify({
          type: "t",
          title: "Billetera no encontrada",
          status: 404,
          code: "wallet_not_found",
          detail: "Sin billetera.",
        }),
      });
    });
    await recharge.goto();
    await recharge.fillAmount("50000");
    await recharge.submit();

    await expect(recharge.submitButton()).toBeDisabled();
    await expect(recharge.alert()).toBeVisible();
    await expect(recharge.submitButton()).toBeEnabled();
  });

  test("HU-04 CA-2: ante 401 invalid_session la webapp redirige a /login", async ({ page }) => {
    const recharge = new RechargePage(page);
    await page.route("**/api/v1/wallet/recharges", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/problem+json",
        body: JSON.stringify({ type: "t", title: "Sesión", status: 401, code: "invalid_session" }),
      }),
    );
    await recharge.goto();
    await recharge.fillAmount("50000");
    await recharge.submit();

    await expect(page).toHaveURL(/\/login(\?.*)?$/);
  });

  test("CA-3, CA-4, CA-9: con sesión real la recarga aumenta el saldo y muestra el resultado", async ({
    page,
  }) => {
    // Usuario de prueba creado por api/scripts/seed_test_user.py (ver quickstart.md).
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn("3009876543", "Clave1234");

    const recharge = new RechargePage(page);
    await recharge.goto();
    await recharge.fillAmount("50000");
    await recharge.submit();

    await expect(recharge.result()).toContainText("Recarga exitosa de $ 50.000,00.");
    await expect(recharge.result()).toContainText("Nuevo saldo disponible:");
  });
});
