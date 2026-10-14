import { describe, expect, it } from "vitest";

import { ApiError, isProblem, toApiError } from "../problem";

describe("problem", () => {
  it("reconoce un problem RFC 9457", () => {
    expect(isProblem({ type: "t", title: "T", status: 422, code: "validation" })).toBe(true);
    expect(isProblem({ message: "no" })).toBe(false);
    expect(isProblem(null)).toBe(false);
    expect(isProblem("texto")).toBe(false);
  });

  it("expone los errores por campo", () => {
    const error = new ApiError({
      type: "t",
      title: "Datos inválidos",
      status: 422,
      code: "validation",
      errors: [{ field: "phone", message: "Debe tener 10 dígitos" }],
    });

    expect(error.message).toBe("Datos inválidos");
    expect(error.messagesByField()).toEqual({ phone: "Debe tener 10 dígitos" });
  });

  it("convierte una respuesta sin cuerpo JSON en unknown_error", async () => {
    const response = new Response("<html/>", { status: 502, statusText: "Bad Gateway" });

    const error = await toApiError(response);

    expect(error.code).toBe("unknown_error");
    expect(error.status).toBe(502);
    expect(error.message).toBe("Bad Gateway");
    expect(error.fieldErrors).toEqual([]);
  });

  it("usa 'Error' como título cuando la respuesta no trae statusText", async () => {
    const error = await toApiError(new Response(null, { status: 500 }));

    expect(error.message).toBe("Error");
    expect(error.code).toBe("unknown_error");
  });

  it("convierte un problem en ApiError con request_id", async () => {
    const response = new Response(
      JSON.stringify({
        type: "t",
        title: "No",
        status: 404,
        code: "not_found",
        request_id: "abc",
        detail: "x",
      }),
      { status: 404 },
    );

    const error = await toApiError(response);

    expect(error.code).toBe("not_found");
    expect(error.requestId).toBe("abc");
    expect(error.message).toBe("x");
  });
});
