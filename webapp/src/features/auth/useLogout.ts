import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import { ApiError } from "../../shared/api/client";
import { logout } from "./api";

/** HU-03: no anunciar cierre hasta que el servidor confirme revocación. */
export function useLogout(onClosed: () => void) {
  const client = useQueryClient();
  const sending = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = useCallback(async () => {
    if (sending.current) return;
    sending.current = true;
    setPending(true);
    setError(null);
    try {
      await logout();
      await client.cancelQueries();
      client.clear();
      onClosed();
    } catch (cause: unknown) {
      if (cause instanceof ApiError && cause.code === "invalid_session") {
        await client.cancelQueries();
        client.clear();
        onClosed();
      } else {
        setError("No se pudo cerrar la sesión. Intenta de nuevo.");
      }
    } finally {
      sending.current = false;
      setPending(false);
    }
  }, [client, onClosed]);
  return { pending, error, submit };
}
