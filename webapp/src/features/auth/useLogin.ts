import { useCallback, useState } from "react";

import { ApiError } from "../../shared/api/client";
import { login, type LoginRequest } from "./api";

const LOGIN_MESSAGES: Record<string, string> = {
  invalid_credentials: "Teléfono o contraseña incorrectos.",
  too_many_attempts: "Demasiados intentos. Intenta de nuevo en unos minutos.",
};
const LOGIN_FALLBACK_MESSAGE = "No se pudo iniciar sesión. Intenta de nuevo.";

type LoginState =
  { kind: "idle" } | { kind: "pending" } | { kind: "success" } | { kind: "error"; message: string };

export function useLogin(): { state: LoginState; submit: (payload: LoginRequest) => void } {
  const [state, setState] = useState<LoginState>({ kind: "idle" });

  const submit = useCallback((payload: LoginRequest) => {
    setState({ kind: "pending" });
    login(payload)
      .then(() => {
        setState({ kind: "success" });
      })
      .catch((error: unknown) => {
        // HU-02 CA-3: un único mensaje, sin importar si falló el teléfono o la
        // contraseña; el `code` decide el texto, nunca el `detail` (api-design.md).
        const code = error instanceof ApiError ? error.code : "";
        const message = LOGIN_MESSAGES[code] ?? LOGIN_FALLBACK_MESSAGE;
        setState({ kind: "error", message });
      });
  }, []);

  return { state, submit };
}
