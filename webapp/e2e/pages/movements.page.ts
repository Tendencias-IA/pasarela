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

  // --- Filtros (HU-10) ---

  fromField() {
    return this.page.getByLabel("Desde");
  }

  toField() {
    return this.page.getByLabel("Hasta");
  }

  typeSelect() {
    return this.page.getByLabel("Tipo");
  }

  async fillRange(from: string, to: string) {
    if (from) await this.fromField().fill(from);
    if (to) await this.toField().fill(to);
  }

  /** Abre el selector (alert de Ionic), elige la opción y confirma. */
  async selectType(label: string) {
    await this.typeSelect().click();
    await this.page.getByRole("radio", { name: label }).click();
    await this.page.getByRole("button", { name: "Aceptar" }).click();
  }

  filteredEmptyState() {
    return this.page.getByText("No hay movimientos con esos filtros");
  }

  clearFiltersButton() {
    return this.page.getByRole("button", { name: "Quitar filtros" });
  }

  rangeError() {
    return this.page.getByText("La fecha inicial no puede ser posterior a la final.");
  }
}
