import { useCallback, useState } from "react";

import { ApiError } from "../../shared/api/client";
import { login, type LoginRequest } from "./api";

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
        const message =
          error instanceof ApiError && error.code === "invalid_credentials"
            ? "Teléfono o contraseña incorrectos."
            : error instanceof ApiError && error.code === "too_many_attempts"
              ? "Demasiados intentos. Intenta de nuevo en unos minutos."
              : "No se pudo iniciar sesión. Intenta de nuevo.";
        setState({ kind: "error", message });
      });
  }, []);

  return { state, submit };
}
