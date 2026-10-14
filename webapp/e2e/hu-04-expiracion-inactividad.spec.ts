import { expect, test } from "@playwright/test";

import { LoginPage } from "./pages/login.page";

const USER = { phone: "3009876543", password: "Clave1234" };

test.describe("HU-04 Sesión por inactividad", () => {
  test("CA-2: ante 401 invalid_session se pide iniciar sesión de nuevo con aviso", async ({
    page,
  }) => {
    await new LoginPage(page).signInAsSeededUser();
    await page.route("**/api/v1/wallet", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/problem+json",
        body: JSON.stringify({ type: "t", title: "Sesión", status: 401, code: "invalid_session" }),
      }),
    );

    await page.goto("/");

    await expect(page).toHaveURL(/\/login\?motivo=expirada$/);
    await expect(page.getByRole("status")).toContainText(
      "Tu sesión expiró. Inicia sesión de nuevo.",
    );
  });

  test("CA-4: con sesión real, consultar la sesión devuelve un vencimiento futuro y renueva la cookie", async ({
    page,
  }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.signIn(USER.phone, USER.password);

    const response = await page.request.get("/api/v1/auth/session");

    expect(response.status()).toBe(200);
    const { expires_at: expiresAt } = (await response.json()) as { expires_at: string };
    const remaining = new Date(expiresAt).getTime() - Date.now();
    expect(remaining).toBeGreaterThan(4 * 60 * 1000);
    expect(remaining).toBeLessThanOrEqual(5 * 60 * 1000 + 5000);
    expect(response.headers()["set-cookie"]).toContain("Max-Age=300");
  });

  test("CA-1, CA-2: una sesión sin cookie válida no accede al historial", async ({ page }) => {
    await new LoginPage(page).signInAsSeededUser();
    await expect(page.getByLabel("Saldo disponible")).toContainText("$");
    await page.context().clearCookies();

    await page.goto("/movimientos");

    await expect(page).toHaveURL(/\/login(\?.*)?$/);
  });

  test("CA-2: tras vencer la sesión, volver a la pestaña lleva a iniciar sesión", async ({
    page,
  }) => {
    await new LoginPage(page).signInAsSeededUser();
    await page.goto("/");
    await expect(page.getByLabel("Saldo disponible")).toContainText("$");
    await page.context().clearCookies();

    // TanStack Query revalida al volver a la pestaña (visibilitychange).
    await page.evaluate("document.dispatchEvent(new Event('visibilitychange', { bubbles: true }))");

    await expect(page).toHaveURL(/\/login/);
  });
});
