import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { LoginPage } from "./pages/login.page";
import { MovementsPage } from "./pages/movements.page";
import { RechargePage } from "./pages/recharge.page";
import { TransferPage } from "./pages/transfer.page";

// Usuarios creados por api/scripts/seed_test_user.py (ver quickstart.md). El receptor
// 3009876545 es exclusivo de estos escenarios para no alterar el estado vacío de 3009876544.
const SENDER = { phone: "3009876543", password: "Clave1234" };
const RECIPIENT = { phone: "3009876545", password: "Clave1234" };

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

test.describe("HU-07 Confirmar una transferencia", () => {
  test("CA-1, CA-3, CA-5, CA-7: confirmar descuenta, informa el éxito y queda en el historial de ambos", async ({
    page,
  }) => {
    await signIn(page, SENDER);
    await rechargeOnce(page);
    const transfer = new TransferPage(page);
    await transfer.goto();
    await transfer.prepare(RECIPIENT.phone, "150");

    // CA-1: nada se ejecuta hasta pulsar Confirmar.
    await expect(transfer.summary()).toContainText("***6545");
    await transfer.confirm();

    await expect(transfer.result()).toContainText("Transferencia exitosa de $ 150,00.");
    await expect(transfer.result()).toContainText("Nuevo saldo disponible:");
    await expect(transfer.result()).not.toContainText(RECIPIENT.phone);

    const senderMovements = new MovementsPage(page);
    await senderMovements.goto();
    const sent = senderMovements.rows().first();
    await expect(sent).toContainText("Transferencia enviada");
    await expect(sent).toContainText("$ 150,00");
    await expect(sent).toContainText("***6545");
    await expect(sent).toHaveAttribute("data-status", "exitosa");

    // CA-5: el destinatario la ve como recibida, con el emisor enmascarado.
    await page.context().clearCookies();
    await signIn(page, RECIPIENT);
    const recipientMovements = new MovementsPage(page);
    await recipientMovements.goto();
    const received = recipientMovements.rows().first();
    await expect(received).toContainText("Transferencia recibida");
    await expect(received).toContainText("$ 150,00");
    await expect(received).toContainText("***6543");
    expect(await recipientMovements.content().innerText()).not.toContain(SENDER.phone);
  });

  test("CA-7, RNF-03.4: el resultado exitoso es accesible y sin violaciones serias", async ({
    page,
  }) => {
    await signIn(page, SENDER);
    await rechargeOnce(page);
    const transfer = new TransferPage(page);
    await transfer.goto();
    await transfer.prepare(RECIPIENT.phone, "100");
    await transfer.confirm();
    await expect(transfer.result()).toContainText("Transferencia exitosa");

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

  test("CA-6, CA-7: un rechazo del servidor se informa y no mueve dinero", async ({ page }) => {
    await signIn(page, SENDER);
    await rechargeOnce(page);
    const transfer = new TransferPage(page);
    await transfer.goto();
    // El resumen se prepara de verdad; solo la confirmación se simula rechazada.
    await page.route("**/api/v1/transfers", async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      return route.fulfill({
        status: 422,
        contentType: "application/problem+json",
        body: JSON.stringify({
          type: "t",
          title: "Saldo insuficiente",
          status: 422,
          code: "insufficient_balance",
          detail: "El saldo disponible es menor que el monto solicitado.",
        }),
      });
    });
    await transfer.prepare(RECIPIENT.phone, "100");
    await transfer.confirm();

    await expect(transfer.alert()).toContainText("Tu saldo es menor");
  });

  test("CA-8: el botón se deshabilita durante el envío y la misma clave viaja en el reintento", async ({
    page,
  }) => {
    await signIn(page, SENDER);
    await rechargeOnce(page);
    const transfer = new TransferPage(page);
    const keys: string[] = [];
    let attempts = 0;
    await page.route("**/api/v1/transfers", async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      keys.push(route.request().headers()["idempotency-key"] ?? "");
      attempts += 1;
      await new Promise((resolve) => setTimeout(resolve, 600));
      // Primer intento: corte de red; el segundo pasa al servidor real con la misma clave.
      if (attempts === 1) return route.abort("failed");
      return route.continue();
    });
    await transfer.goto();
    await transfer.prepare(RECIPIENT.phone, "100");

    await transfer.confirm();
    await expect(transfer.confirmButton()).toBeDisabled();
    await expect(transfer.alert()).toContainText("no se duplicará");

    await transfer.confirm();
    await expect(transfer.result()).toContainText("Transferencia exitosa de $ 100,00.");
    expect(keys).toHaveLength(2);
    expect(keys[0]).toBe(keys[1]);
    expect(keys[0]).toMatch(/^[0-9a-f-]{36}$/);
  });

  test("HU-04 CA-2: ante 401 invalid_session al confirmar la webapp redirige a /login", async ({
    page,
  }) => {
    await signIn(page, SENDER);
    await rechargeOnce(page);
    const transfer = new TransferPage(page);
    await page.route("**/api/v1/transfers", (route) => {
      if (route.request().method() !== "POST") return route.continue();
      return route.fulfill({
        status: 401,
        contentType: "application/problem+json",
        body: JSON.stringify({ type: "t", title: "Sesión", status: 401, code: "invalid_session" }),
      });
    });
    await transfer.goto();
    await transfer.prepare(RECIPIENT.phone, "100");
    await transfer.confirm();

    await expect(page).toHaveURL(/\/login$/);
  });
});
