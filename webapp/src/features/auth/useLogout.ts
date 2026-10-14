import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../shared/api/client";
import { logout as postLogout } from "./api";

/**
 * Cierra la sesión (HU-03): revoca en el servidor, vacía la caché para que "atrás" no muestre
 * datos y va a /login, donde no hay menú. Si el servidor ya no reconocía la sesión (401) el
 * resultado es el mismo. Con un fallo de red no se sale: la sesión seguiría viva (`failed`).
 */
export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [failed, setFailed] = useState(false);

  const logout = useCallback(async () => {
    setFailed(false);
    try {
      await postLogout();
    } catch (error: unknown) {
      if (!(error instanceof ApiError && error.status === 401)) {
        setFailed(true);
        return;
      }
    }
    queryClient.clear();
    navigate("/login", { replace: true });
  }, [queryClient, navigate]);

  return { logout, failed };
}
