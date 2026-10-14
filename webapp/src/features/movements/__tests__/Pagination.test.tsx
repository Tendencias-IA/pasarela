import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Pagination } from "../Pagination";

describe("Pagination (HU-09 CA-6, RNF-03.6)", () => {
  it("en la primera de tres páginas deshabilita Anterior y habilita Siguiente", () => {
    render(<Pagination page={1} lastPage={3} onPageChange={() => undefined} />);

    const nav = screen.getByRole("navigation", { name: "Paginación" });
    expect(nav).toHaveTextContent("Página 1 de 3");
    expect(screen.getByText("Anterior").closest("ion-button")).toHaveAttribute("disabled");
    expect(screen.getByText("Siguiente").closest("ion-button")).not.toHaveAttribute("disabled");
  });

  it("en la última página deshabilita Siguiente", () => {
    render(<Pagination page={3} lastPage={3} onPageChange={() => undefined} />);

    expect(screen.getByText("Siguiente").closest("ion-button")).toHaveAttribute("disabled");
    expect(screen.getByText("Anterior").closest("ion-button")).not.toHaveAttribute("disabled");
  });

  it("con una sola página no habilita ningún control", () => {
    render(<Pagination page={1} lastPage={1} onPageChange={() => undefined} />);

    expect(screen.getByText("Anterior").closest("ion-button")).toHaveAttribute("disabled");
    expect(screen.getByText("Siguiente").closest("ion-button")).toHaveAttribute("disabled");
  });

  it("Siguiente y Anterior llaman onPageChange con la página vecina", () => {
    const onPageChange = vi.fn();
    render(<Pagination page={2} lastPage={3} onPageChange={onPageChange} />);

    fireEvent.click(screen.getByText("Siguiente").closest("ion-button") as HTMLElement);
    fireEvent.click(screen.getByText("Anterior").closest("ion-button") as HTMLElement);

    expect(onPageChange).toHaveBeenNthCalledWith(1, 3);
    expect(onPageChange).toHaveBeenNthCalledWith(2, 1);
  });

  it("anuncia la página actual a lectores de pantalla", () => {
    render(<Pagination page={2} lastPage={3} onPageChange={() => undefined} />);

    expect(screen.getByText("Página 2 de 3")).toHaveAttribute("aria-live", "polite");
  });
});
