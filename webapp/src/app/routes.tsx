import { IonReactRouter } from "@ionic/react-router";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/accounts/RegisterPage";
import { RechargePage } from "../features/wallet/RechargePage";
import { AppShell } from "./AppShell";
import { ComingSoonPage } from "./ComingSoonPage";
import { HomePage } from "./HomePage";
import { RequireSession } from "./RequireSession";

/** Rutas de la webapp (ADR-0007: Ionic + react-router-dom 6). */
export function AppRoutes() {
  return (
    <IonReactRouter>
      <AppShell>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <RequireSession>
                <HomePage />
              </RequireSession>
            }
          />
          <Route
            path="/recargar"
            element={
              <RequireSession>
                <RechargePage />
              </RequireSession>
            }
          />
          <Route
            path="/transferir"
            element={
              <RequireSession>
                <ComingSoonPage title="Transferir" story="HU-06" />
              </RequireSession>
            }
          />
          <Route
            path="/movimientos"
            element={
              <RequireSession>
                <ComingSoonPage title="Movimientos" story="HU-09" />
              </RequireSession>
            }
          />
          <Route
            path="/perfil"
            element={
              <RequireSession>
                <ComingSoonPage title="Perfil" story="HU-10" />
              </RequireSession>
            }
          />
        </Routes>
      </AppShell>
    </IonReactRouter>
  );
}
