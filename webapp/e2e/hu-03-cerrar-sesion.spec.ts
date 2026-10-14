import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("HU-03 CA-1/CA-2/CA-3 cierra y exige login al volver atrás o recargar", async ({ page }) => {
  let active = true;
  let closed = 0;
  await page.route("**/api/v1/auth/session", async (route) => {
    await route.fulfill({
      status: active ? 200 : 401,
      contentType: "application/json",
      body: JSON.stringify(
        active
          ? { expires_at: "2099-01-01T00:00:00Z" }
          : {
              type: "https://pasarela.local/problems/invalid_session",
              title: "Sin sesión",
              status: 401,
              code: "invalid_session",
              instance: "/api/v1/auth/session",
            },
      ),
    });
  });
  await page.route("**/health", (route) => route.fulfill({ json: { status: "ok", db: "ok" } }));
  await page.route("**/api/v1/auth/logout", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().headers()["x-requested-with"]).toBe("fetch");
    active = false;
    closed++;
    await route.fulfill({ status: 204 });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Billetera Digital" })).toBeVisible();
  await page.getByRole("link", { name: "Recargar saldo" }).click();
  await expect(page.getByRole("heading", { name: "Recargar saldo", exact: true })).toBeVisible();
  const close = page.getByRole("button", { name: "Cerrar sesión", exact: true });
  if (!(await close.isVisible())) {
    await page
      .getByRole("banner")
      .filter({ hasText: "Recargar" })
      .getByRole("button", { name: "menu" })
      .click();
  }
  await close.click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Bienvenido de nuevo" })).toBeVisible();
  expect(closed).toBe(1);
  await page.goBack();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/recargar");
  await expect(page).toHaveURL(/\/login$/);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Bienvenido de nuevo" })).toBeVisible();
  const audit = await new AxeBuilder({ page }).analyze();
  expect(
    audit.violations.filter((issue) => ["serious", "critical"].includes(issue.impact ?? "")),
  ).toEqual([]);
});

test("HU-03 CA-1 fallo reintentable no finge un cierre", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/v1/auth/session", (route) =>
    route.fulfill({ json: { expires_at: "2099-01-01T00:00:00Z" } }),
  );
  await page.route("**/api/v1/auth/logout", async (route) => {
    attempts++;
    await route.fulfill({ status: attempts === 1 ? 503 : 204 });
  });
  await page.goto("/recargar");
  const close = page.getByRole("button", { name: "Cerrar sesión", exact: true });
  if (!(await close.isVisible())) {
    await page
      .getByRole("banner")
      .filter({ hasText: "Recargar" })
      .getByRole("button", { name: "menu" })
      .click();
  }
  await close.click();
  await expect(page.getByRole("alert")).toHaveText(/No se pudo cerrar/);
  await expect(page).toHaveURL(/\/recargar$/);
  await page.getByRole("button", { name: "Reintentar cierre" }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(attempts).toBe(2);
});
