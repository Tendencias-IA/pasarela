import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { LoginPage } from "./pages/login.page";
import { MovementsPage } from "./pages/movements.page";
import { RechargePage } from "./pages/recharge.page";
import { TransferPage } from "./pages/transfer.page";

// Usuarios creados por api/scripts/seed_test_user.py (ver quickstart.md).
const SENDER = { phone: "3009876543", password: "Clave1234" };
const RECIPIENT = { phone: "3009876544", password: "Clave1234" };

async function signIn(page: Page, user: { phone: string; password: string }) {
  const login = new LoginPage(page);
  await login.goto();
  await login.signIn(user.phone, user.password);
}

async function rechargeOnce(page: Page) {
  const recharge = new RechargePage(page);
  await recharge.goto();
  await recharge.fillAmount("20000");
  await recharge.submit();
  await expect(recharge.result()).toContainText("Recarga exitosa de $ 20.000,00.");
}

test.describe("HU-06 Preparar una transferencia", () => {
  test("RNF-03.1: Transferir está en el menú y abre el formulario en un clic", async ({ page }) => {
    await signIn(page, SENDER);
    await page.goto("/");
    await page.getByRole("link", { name: "Transferir" }).first().click();

    await expect(page).toHaveURL(/\/transferir$/);
    await expect(page.getByRole("heading", { level: 1, name: "Transferir dinero" })).toBeVisible();
  });

  test("SC-006: la pantalla no tiene violaciones serias de accesibilidad", async ({ page }) => {
    await signIn(page, SENDER);
    const transfer = new TransferPage(page);
    await transfer.goto();
    await expect(transfer.phoneField()).toBeVisible();

    // `scrollable-region-focusable` se dispara sobre el contenedor interno de <ion-content>
    // (shadow DOM de Ionic, no marcado nuestro).
    const results = await new AxeBuilder({ page })
      .disableRules(["scrollable-region-focusable"])
      .analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(serious).toEqual([]);
  });

  test("CA-3, CA-4: abc, 99 y un teléfono corto se rechazan sin llamar a la API", async ({
    page,
  }) => {
    await signIn(page, SENDER);
    const transfer = new TransferPage(page);
    let requests = 0;
    await page.route("**/api/v1/transfers/preview", async (route) => {
      requests += 1;
      await route.continue();
    });
    await transfer.goto();

    await transfer.prepare("12", "abc");
    await expect(transfer.fieldError(/celular de diez dígitos/)).toBeVisible();
    await expect(transfer.fieldError(/pesos colombianos/)).toBeVisible();

    await transfer.prepare(RECIPIENT.phone, "99");
    await expect(transfer.fieldError(/entre \$ 100,00 y \$ 3\.000\.000,00/).first()).toBeVisible();

    expect(requests).toBe(0);
  });

  test("CA-1, CA-7, CA-8: con sesión real el resumen enmascara al destinatario y Editar vuelve", async ({
    page,
  }) => {
    await signIn(page, SENDER);
    await rechargeOnce(page);
    const transfer = new TransferPage(page);
    await transfer.goto();

    await transfer.prepare(RECIPIENT.phone, "150");

    await expect(transfer.summary()).toContainText("***6544");
    await expect(transfer.summary()).toContainText("$ 150,00");
    await expect(transfer.summary()).toContainText("Saldo después");
    await expect(transfer.summary()).not.toContainText(RECIPIENT.phone);

    await transfer.edit();
    await expect(transfer.phoneField()).toHaveValue(RECIPIENT.phone);
  });

  test("CA-5: el propio teléfono muestra un aviso", async ({ page }) => {
    await signIn(page, SENDER);
    const transfer = new TransferPage(page);
    await transfer.goto();

    await transfer.prepare(SENDER.phone, "1000");

    await expect(transfer.alert()).toContainText("No puedes transferirte a tu propia cuenta.");
  });

  test("CA-4: un teléfono sin cuenta muestra un aviso", async ({ page }) => {
    await signIn(page, SENDER);
    const transfer = new TransferPage(page);
    await transfer.goto();

    await transfer.prepare("3999999999", "1000");

    await expect(transfer.alert()).toContainText("no corresponde a un usuario registrado");
  });

  test("CA-6, CA-8: sin saldo se rechaza y el historial sigue vacío", async ({ page }) => {
    await signIn(page, RECIPIENT);
    const transfer = new TransferPage(page);
    await transfer.goto();

    await transfer.prepare(SENDER.phone, "100");

    await expect(transfer.alert()).toContainText("Tu saldo es menor");
    const movements = new MovementsPage(page);
    await movements.goto();
    await expect(movements.emptyState()).toBeVisible();
  });

  test("HU-04 CA-2: ante 401 invalid_session la webapp redirige a /login", async ({ page }) => {
    const transfer = new TransferPage(page);
    await page.route("**/api/v1/transfers/preview", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/problem+json",
        body: JSON.stringify({ type: "t", title: "Sesión", status: 401, code: "invalid_session" }),
      }),
    );
    await transfer.goto();
    await transfer.prepare(RECIPIENT.phone, "1000");

    await expect(page).toHaveURL(/\/login$/);
  });
});
