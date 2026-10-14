import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { LoginPage } from "./pages/login.page";
import { MovementsPage } from "./pages/movements.page";
import { RechargePage } from "./pages/recharge.page";

// Usuarios creados por api/scripts/seed_test_user.py (ver quickstart.md).
const USER_WITH_HISTORY = { phone: "3009876543", password: "Clave1234" };
const USER_WITHOUT_HISTORY = { phone: "3009876544", password: "Clave1234" };

async function expectNoSeriousViolations(page: Page) {
  // `scrollable-region-focusable` se dispara sobre el contenedor interno de <ion-content>
  // (shadow DOM de Ionic, no marcado nuestro) en cuanto la lista supera la altura visible;
  // el contenido sigue siendo navegable por teclado a través de sus controles.
  const results = await new AxeBuilder({ page })
    .disableRules(["scrollable-region-focusable"])
    .analyze();
  const serious = results.violations.filter(
    (v) => v.impact === "serious" || v.impact === "critical",
  );
  expect(serious).toEqual([]);
}

/** Deja al usuario con al menos un movimiento (la BD de CI empieza vacía). */
async function rechargeOnce(page: Page) {
  const recharge = new RechargePage(page);
  await recharge.goto();
  await recharge.fillAmount("20000");
  await recharge.submit();
  await expect(recharge.result()).toContainText("Recarga exitosa de $ 20.000,00.");
}

test.describe("HU-09 Historial de movimientos", () => {
  test("desde el panel se llega a Movimientos en un clic (RNF-03.1, FR-013)", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER_WITH_HISTORY.phone, USER_WITH_HISTORY.password);

    await page.goto("/");
    await page.getByRole("link", { name: "Ver movimientos" }).click();

    await expect(page).toHaveURL(/\/movimientos$/);
    await expect(new MovementsPage(page).heading()).toBeVisible();
  });

  test("HU-04 CA-2, RNF-01.1: sin sesión, /movimientos redirige a /login", async ({ page }) => {
    await new MovementsPage(page).goto();

    await expect(page).toHaveURL(/\/login(\?.*)?$/);
  });

  test("CA-1, CA-2, SC-007: una recarga recién hecha aparece en el historial con su monto y estado", async ({
    page,
  }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER_WITH_HISTORY.phone, USER_WITH_HISTORY.password);

    // Monto único: otras specs recargan al mismo usuario en paralelo, y el orden exacto
    // (CA-4) ya lo verifican las pruebas de integración y de API.
    const recharge = new RechargePage(page);
    await recharge.goto();
    await recharge.fillAmount("23456");
    await recharge.submit();
    await expect(recharge.result()).toContainText("Recarga exitosa de $ 23.456,00.");

    const movements = new MovementsPage(page);
    await movements.goto();
    const row = movements.rows().filter({ hasText: "$ 23.456,00" }).first();
    await expect(row).toContainText("Recarga");
    await expect(row).toContainText("Exitosa");
    await expect(row).toHaveAttribute("data-status", "exitosa");
  });

  test("SC-002: ningún texto del historial contiene un teléfono de 10 dígitos", async ({
    page,
  }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER_WITH_HISTORY.phone, USER_WITH_HISTORY.password);
    await rechargeOnce(page);
    const movements = new MovementsPage(page);
    await movements.goto();
    await expect(movements.rows().first()).toBeVisible();

    const text = await movements.content().innerText();

    expect(text).not.toMatch(/\d{10}/);
  });

  test("CA-6: la paginación está presente y Anterior deshabilitado en la primera página", async ({
    page,
  }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER_WITH_HISTORY.phone, USER_WITH_HISTORY.password);
    await rechargeOnce(page);
    const movements = new MovementsPage(page);
    await movements.goto();

    await expect(movements.pagination()).toContainText(/Página 1 de \d+/);
    await expect(movements.prevButton()).toBeDisabled();
    await expectNoSeriousViolations(page);
  });

  test("CA-7: un usuario sin movimientos ve el estado vacío con acceso a recargar", async ({
    page,
  }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER_WITHOUT_HISTORY.phone, USER_WITHOUT_HISTORY.password);
    const movements = new MovementsPage(page);
    await movements.goto();

    await expect(movements.emptyState()).toBeVisible();
    await expect(movements.rows()).toHaveCount(0);
    await expectNoSeriousViolations(page);

    await page.getByRole("link", { name: "Recargar saldo" }).click();
    await expect(page).toHaveURL(/\/recargar$/);
  });
});
