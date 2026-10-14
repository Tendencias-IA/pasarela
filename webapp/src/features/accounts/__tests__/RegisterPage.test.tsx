import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../../test/server";
import { RegisterPage } from "../RegisterPage";

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <RegisterPage />
    </QueryClientProvider>,
  );
}

async function completeForm() {
  const input = (name: string) =>
    waitFor(() => {
      const element = screen.getByLabelText(name);
      if (!(element instanceof HTMLInputElement)) throw new Error(`Ionic no hidrató ${name}.`);
      return element;
    });
  const type = async (name: string, value: string) => {
    const nativeInput = await input(name);
    fireEvent.input(nativeInput, { target: { value } });
  };
  await type("Nombre completo", "Lía Test");
  await type("Número de teléfono", "3000000001");
  await type("Número de identificación", "TEST001");
  await type("Correo electrónico", "lia@example.test");
  await type("Contraseña", "clave123");
}

function submitForm(container: HTMLElement) {
  const form = container.querySelector("form");
  if (form === null) throw new Error("No se encontró el formulario de registro.");
  fireEvent.submit(form);
}

function ionicInputs(container: HTMLElement) {
  return Array.from(container.querySelectorAll("ion-input"));
}

describe("RegisterPage", () => {
  it("HU-01 CA-3/CA-5 identifies every required field and links to login", async () => {
    const requestStarted = vi.fn();
    server.use(
      http.post("/api/v1/accounts", () => {
        requestStarted();
        return HttpResponse.json({}, { status: 201 });
      }),
    );
    const { container } = renderPage();
    submitForm(container);

    await waitFor(() => {
      expect(ionicInputs(container)).toHaveLength(5);
      for (const input of ionicInputs(container)) {
        expect(input).toHaveClass("ion-invalid", "ion-touched");
      }
    });
    expect(container.querySelector("ion-router-link")).toHaveAttribute("href", "/login");
    expect(requestStarted).not.toHaveBeenCalled();
  });

  it("HU-01 CA-3/CA-5 rejects invalid formats before calling the API", async () => {
    const requestStarted = vi.fn();
    server.use(
      http.post("/api/v1/accounts", () => {
        requestStarted();
        return HttpResponse.json({}, { status: 201 });
      }),
    );
    const { container } = renderPage();
    const invalidValues = ["1", "200", "!", "correo", "sololetras"];
    const labels = [
      "Nombre completo",
      "Número de teléfono",
      "Número de identificación",
      "Correo electrónico",
      "Contraseña",
    ];
    for (const [index, label] of labels.entries()) {
      fireEvent.input(await screen.findByLabelText(label), {
        target: { value: invalidValues[index] ?? "" },
      });
    }
    submitForm(container);

    await waitFor(() => {
      for (const input of ionicInputs(container)) {
        expect(input).toHaveClass("ion-invalid", "ion-touched");
      }
    });
    expect(requestStarted).not.toHaveBeenCalled();
  });

  it("HU-01 CA-1/CA-2 creates the account once and confirms without login", async () => {
    server.use(
      http.post("/api/v1/accounts", () =>
        HttpResponse.json({ account_id: 1, wallet: { balance: "0.00" } }, { status: 201 }),
      ),
    );
    const { container } = renderPage();
    await completeForm();
    submitForm(container);
    const successToast = await screen.findByRole<HTMLIonToastElement>("status", {
      name: /Tu cuenta y billetera fueron creadas/,
    });
    expect(successToast).toBeInTheDocument();
    await successToast.dismiss();
    expect(successToast).not.toHaveAttribute("is-open");
  });

  it("HU-01 CA-4 shows a generic duplicate message", async () => {
    server.use(
      http.post("/api/v1/accounts", () =>
        HttpResponse.json(
          {
            type: "https://pasarela.test/problems/duplicate_identity",
            title: "Cuenta ya registrada",
            status: 409,
            detail: "Ya existe una cuenta con alguno de esos datos.",
            instance: "/api/v1/accounts",
            code: "duplicate_identity",
            request_id: "request-2",
          },
          { status: 409 },
        ),
      ),
    );
    const { container } = renderPage();
    await completeForm();
    submitForm(container);
    const errorToast = await screen.findByRole<HTMLIonToastElement>("alert", {
      name: "Ya existe una cuenta con alguno de esos datos.",
    });
    expect(errorToast).toBeInTheDocument();
    await errorToast.dismiss();
    await waitFor(() => {
      expect(errorToast).not.toHaveAttribute("is-open");
    });
  });

  it("HU-01 CA-3 maps server field errors to their accessible input", async () => {
    server.use(
      http.post("/api/v1/accounts", () =>
        HttpResponse.json(
          {
            status: 422,
            type: "https://pasarela.local/problems/validation",
            title: "Datos inválidos",
            code: "validation",
            detail: "Corrige los campos indicados.",
            errors: [{ field: "email", message: "El correo no es válido." }],
          },
          { status: 422 },
        ),
      ),
    );
    const { container } = renderPage();
    await completeForm();
    submitForm(container);

    await waitFor(() => {
      expect(ionicInputs(container)[3]).toHaveClass("ion-invalid", "ion-touched");
    });
  });

  it("HU-01 CA-1 sends only one request while registration is pending", async () => {
    let resolveRequest: (() => void) | undefined;
    const requestStarted = vi.fn();
    server.use(
      http.post("/api/v1/accounts", async () => {
        requestStarted();
        await new Promise<void>((resolve) => {
          resolveRequest = resolve;
        });
        return HttpResponse.json({ account_id: 1, wallet: { balance: "0.00" } }, { status: 201 });
      }),
    );
    const { container } = renderPage();
    await completeForm();
    submitForm(container);
    submitForm(container);

    await waitFor(() => {
      expect(requestStarted).toHaveBeenCalledTimes(1);
    });
    resolveRequest?.();
  });
});
