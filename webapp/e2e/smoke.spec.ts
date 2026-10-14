import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test.describe("Esqueleto", () => {
  test("la webapp carga y la API responde a través del mismo origen", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { level: 1, name: "Billetera Digital" })).toBeVisible();
    await expect(page.getByRole("status")).toHaveText("API ok, base de datos ok");
  });

  test("la pantalla inicial no tiene violaciones serias de accesibilidad", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("status")).toContainText("API");

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );

    expect(serious).toEqual([]);
  });
});
