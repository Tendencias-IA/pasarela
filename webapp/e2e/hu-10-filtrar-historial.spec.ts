import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { LoginPage } from "./pages/login.page";
import { MovementsPage } from "./pages/movements.page";
import { RechargePage } from "./pages/recharge.page";

// Usuario creado por api/scripts/seed_test_user.py (ver quickstart.md de HU-09/HU-10).
const USER = { phone: "3009876543", password: "Clave1234" };

async function expectNoSeriousViolations(page: Page) {
  // Mismo motivo que en HU-09: `scrollable-region-focusable` apunta al contenedor interno de
  // <ion-content> (shadow DOM de Ionic), no a marcado propio.
  const results = await new AxeBuilder({ page })
    .disableRules(["scrollable-region-focusable"])
    .analyze();
  const serious = results.violations.filter(
    (v) => v.impact === "serious" || v.impact === "critical",
  );
  expect(serious).toEqual([]);
}

/** Deja al usuario con al menos una recarga (la BD de CI empieza vacía). */
async function rechargeOnce(page: Page) {
  const recharge = new RechargePage(page);
  await recharge.goto();
  await recharge.fillAmount("20000");
  await recharge.submit();
  await expect(recharge.result()).toContainText("Recarga exitosa de $ 20.000,00.");
}

async function signInWithHistory(page: Page) {
  const login = new LoginPage(page);
  await login.goto();
  await login.signIn(USER.phone, USER.password);
  await rechargeOnce(page);
}

test.describe("HU-10 Filtrar el historial", () => {
  test("CA-3: filtrar por recargas muestra filas y deja la URL con el filtro", async ({ page }) => {
    await signInWithHistory(page);
    const movements = new MovementsPage(page);
    await movements.goto();

    await movements.selectType("Recargas");

    await expect(page).toHaveURL(/\/movimientos\?type=recharge$/);
    await expect(movements.rows().first()).toContainText("Recarga");
    await expect(movements.rows().first()).toContainText("Exitosa");
    await expectNoSeriousViolations(page);
  });

  test("CA-7: filtrar por enviadas sin coincidencias muestra el vacío y conserva el filtro", async ({
    page,
  }) => {
    await signInWithHistory(page);
    const movements = new MovementsPage(page);
    await movements.goto();

    await movements.selectType("Transferencias enviadas");

    await expect(movements.filteredEmptyState()).toBeVisible();
    await expect(page).toHaveURL(/type=sent/);
    await expect(movements.typeSelect()).toContainText("Transferencias enviadas");
    await expectNoSeriousViolations(page);

    await movements.clearFiltersButton().click();

    await expect(page).toHaveURL(/\/movimientos$/);
    await expect(movements.rows().first()).toBeVisible();
    await expect(movements.typeSelect()).toContainText("Todas");
  });

  test("CA-2: desde posterior a hasta muestra el error junto al campo sin llamar a la API", async ({
    page,
  }) => {
    await signInWithHistory(page);
    const movements = new MovementsPage(page);
    await movements.goto();
    await expect(movements.rows().first()).toBeVisible();
    let requests = 0;
    await page.route("**/api/v1/movements*", async (route) => {
      requests += 1;
      await route.continue();
    });

    await movements.fillRange("2026-10-20", "2026-10-10");

    await expect(movements.rangeError()).toBeVisible();
    expect(requests).toBe(0);
    await expectNoSeriousViolations(page);
  });

  test("CA-1, CA-4: un rango que incluye hoy combinado con recargas devuelve la recarga", async ({
    page,
  }) => {
    await signInWithHistory(page);
    const movements = new MovementsPage(page);
    const today = new Date().toISOString().slice(0, 10);
    await movements.goto();

    await movements.fillRange(today, today);
    await movements.selectType("Recargas");

    await expect(page).toHaveURL(new RegExp(`from=${today}&to=${today}&type=recharge`));
    await expect(movements.rows().first()).toContainText("Recarga");
  });

  test("CA-7: recargar la pantalla conserva los filtros de la URL", async ({ page }) => {
    await signInWithHistory(page);
    const movements = new MovementsPage(page);
    await page.goto("/movimientos?type=sent&from=2026-01-01");

    await expect(movements.filteredEmptyState()).toBeVisible();
    await page.reload();

    await expect(movements.filteredEmptyState()).toBeVisible();
    await expect(movements.fromField()).toHaveValue("2026-01-01");
    await expect(movements.typeSelect()).toContainText("Transferencias enviadas");
  });

  test("CA-6: cambiar un filtro quita la página de la URL", async ({ page }) => {
    await signInWithHistory(page);
    const movements = new MovementsPage(page);
    await page.goto("/movimientos?page=1&type=sent");

    await movements.selectType("Recargas");

    await expect(page).toHaveURL(/\/movimientos\?type=recharge$/);
  });
});
