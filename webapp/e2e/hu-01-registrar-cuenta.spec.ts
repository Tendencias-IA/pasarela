import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { RegisterPage } from "./pages/register.page";

test("HU-01 CA-1 crea una cuenta accesible", async ({ page }) => {
  await page.route("**/api/v1/accounts", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ account_id: 1, wallet: { balance: "0.00" } }),
    });
  });
  const registration = new RegisterPage(page);
  await registration.goto();
  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((issue) => ["serious", "critical"].includes(issue.impact ?? "")),
  ).toEqual([]);
  await registration.submit({
    name: "Lía Test",
    phone: "3000000001",
    nationalId: "TEST001",
    email: "lia@example.test",
    password: "clave123",
  });
  await expect(page.locator('ion-toast[role="status"]')).toHaveAttribute(
    "aria-label",
    /Tu cuenta y billetera fueron creadas/,
  );
});

test("HU-01 CA-3/CA-4 rechaza datos inválidos y duplicados sin perder accesibilidad", async ({
  page,
}) => {
  const registration = new RegisterPage(page);
  await registration.goto();

  await page.getByRole("button", { name: "Crear cuenta" }).click();
  await expect(page.getByText("El nombre es obligatorio.")).toBeVisible();
  await expect(page.getByText("El teléfono es obligatorio.")).toBeVisible();

  await page.route("**/api/v1/accounts", async (route) => {
    await route.fulfill({
      status: 409,
      contentType: "application/problem+json",
      body: JSON.stringify({
        status: 409,
        type: "https://pasarela.local/problems/duplicate_identity",
        title: "Cuenta ya registrada",
        code: "duplicate_identity",
        detail: "Ya existe una cuenta con alguno de esos datos.",
      }),
    });
  });
  await registration.submit({
    name: "Lía Test",
    phone: "3000000001",
    nationalId: "TEST001",
    email: "lia@example.test",
    password: "clave123",
  });
  await expect(page.getByRole("alert")).toContainText(
    "Ya existe una cuenta con alguno de esos datos.",
  );

  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((issue) => ["serious", "critical"].includes(issue.impact ?? "")),
  ).toEqual([]);
});
