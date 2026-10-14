import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const profile = {
  full_name: "Persona Prueba",
  phone: "3001110001",
  national_id: "PRUEBA001",
  email: "persona@example.test",
};
test("HU-12 CA-3/CA-4 guarda y conserva el teléfono al reabrir", async ({ page }) => {
  let phone = profile.phone;
  await page.route("**/api/v1/profile", async (route) => {
    if (route.request().method() === "PATCH") {
      const body = route.request().postDataJSON() as { phone: string };
      phone = body.phone;
    }
    await route.fulfill({ json: { ...profile, phone } });
  });
  await page.goto("/perfil");
  await page.getByRole("button", { name: "Editar teléfono" }).click();
  await page.getByLabel("Nuevo teléfono").fill("3001110002");
  await page.getByRole("button", { name: "Guardar teléfono", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Teléfono actualizado");
  await page.reload();
  await expect(page.getByText("3001110002", { exact: true })).toBeVisible();
  const axe = await new AxeBuilder({ page }).analyze();
  expect(
    axe.violations.filter((item) => ["serious", "critical"].includes(item.impact ?? "")),
  ).toEqual([]);
});

test("HU-12 CA-1/CA-2/CA-8 rechaza y permite cancelar sin guardar", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/v1/profile", async (route) => {
    if (route.request().method() === "GET") return route.fulfill({ json: profile });
    attempts++;
    await route.fulfill({
      status: 409,
      json: {
        type: "https://pasarela.local/problems/duplicate_identity",
        title: "Duplicado",
        status: 409,
        code: "duplicate_identity",
      },
    });
  });
  await page.goto("/perfil");
  await page.getByRole("button", { name: "Editar teléfono" }).click();
  await page.getByLabel("Nuevo teléfono").fill("123");
  await page.getByRole("button", { name: "Guardar teléfono", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("10 dígitos");
  expect(attempts).toBe(0);
  await page.getByLabel("Nuevo teléfono").fill("3001110002");
  await page.getByRole("button", { name: "Guardar teléfono", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("ya está registrado");
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page.getByText(profile.phone, { exact: true })).toBeVisible();
  expect(attempts).toBe(1);
});
