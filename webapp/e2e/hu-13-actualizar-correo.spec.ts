import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const profile = {
  full_name: "Persona Prueba",
  phone: "3001110001",
  national_id: "PRUEBA001",
  email: "anterior@example.test",
};
test("HU-13 CA-3/CA-4 guarda el correo y persiste al reabrir", async ({ page }) => {
  let email = profile.email;
  await page.route("**/api/v1/profile", async (route) => {
    if (route.request().method() === "PATCH") {
      const payload = route.request().postDataJSON() as { email: string };
      email = payload.email.toLowerCase();
    }
    await route.fulfill({ json: { ...profile, email } });
  });
  await page.goto("/perfil");
  await page.getByRole("button", { name: "Editar correo", exact: true }).click();
  await page.getByLabel("Nuevo correo").fill("nuevo@example.test");
  await page.getByRole("button", { name: "Guardar correo", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Correo actualizado");
  await page.reload();
  await expect(page.getByText("nuevo@example.test", { exact: true })).toBeVisible();
  await expect(page.getByText(profile.phone, { exact: true })).toBeVisible();
  const axe = await new AxeBuilder({ page }).analyze();
  expect(
    axe.violations.filter((item) => ["serious", "critical"].includes(item.impact ?? "")),
  ).toEqual([]);
});

test("HU-13 CA-1/CA-2/CA-6 rechaza y cancela conservando el correo", async ({ page }) => {
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
  await page.getByRole("button", { name: "Editar correo", exact: true }).click();
  await page.getByLabel("Nuevo correo").fill("abc");
  await page.getByRole("button", { name: "Guardar correo", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("correo válido");
  expect(attempts).toBe(0);
  await page.getByLabel("Nuevo correo").fill("otra@example.test");
  await page.getByRole("button", { name: "Guardar correo", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("ya está registrado");
  await page.getByRole("button", { name: "Cancelar correo", exact: true }).click();
  await expect(page.getByText(profile.email, { exact: true })).toBeVisible();
  expect(attempts).toBe(1);
});
