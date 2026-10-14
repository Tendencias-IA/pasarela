/** Error de la API en formato RFC 9457 (ver .claude/rules/api-design.md). */
export interface FieldError {
  field: string;
  message: string;
}

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  code: string;
  request_id?: string;
  errors?: FieldError[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | undefined;
  readonly fieldErrors: FieldError[];

  constructor(problem: Problem) {
    super(problem.detail ?? problem.title);
    this.name = "ApiError";
    this.status = problem.status;
    this.code = problem.code;
    this.requestId = problem.request_id;
    this.fieldErrors = problem.errors ?? [];
  }

  /** Mensajes por campo, listos para mostrarlos junto a cada control del formulario. */
  messagesByField(): Record<string, string> {
    return Object.fromEntries(this.fieldErrors.map((e) => [e.field, e.message]));
  }
}

export function isProblem(value: unknown): value is Problem {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.code === "string" && typeof v.status === "number" && typeof v.title === "string";
}

/** Convierte una respuesta no exitosa en ApiError, con un fallback cuando el cuerpo no es un problem. */
export async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (isProblem(body)) return new ApiError(body);
  return new ApiError({
    type: "about:blank",
    title: response.statusText || "Error",
    status: response.status,
    code: "unknown_error",
  });
}
