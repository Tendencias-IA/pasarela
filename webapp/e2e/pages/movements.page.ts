import type { Page } from "@playwright/test";

/** Pantalla de HU-09 (features/movements/MovementsPage.tsx). */
export class MovementsPage {
  constructor(private readonly page: Page) {}

  async goto(pageNumber?: number) {
    await this.page.goto(pageNumber ? `/movimientos?page=${String(pageNumber)}` : "/movimientos");
  }

  heading() {
    return this.page.getByRole("heading", { level: 1, name: "Movimientos" });
  }

  list() {
    return this.page.getByRole("list", { name: "Movimientos" });
  }

  rows() {
    return this.list().getByRole("listitem");
  }

  /** Contenido de la página (el menú lateral también tiene un ion-content). */
  content() {
    return this.page.locator("#main ion-content");
  }

  emptyState() {
    return this.page.getByText("Aún no tienes movimientos");
  }

  pagination() {
    return this.page.getByRole("navigation", { name: "Paginación" });
  }

  prevButton() {
    return this.page.getByRole("button", { name: "Anterior" });
  }

  nextButton() {
    return this.page.getByRole("button", { name: "Siguiente" });
  }
}
