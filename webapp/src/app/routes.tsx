import { IonReactRouter } from "@ionic/react-router";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { RechargePage } from "../features/wallet/RechargePage";
import { AppShell } from "./AppShell";
import { HomePage } from "./HomePage";

/** Rutas de la webapp (ADR-0007: Ionic + react-router-dom 6). */
export function AppRoutes() {
  return (
    <IonReactRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/recargar" element={<RechargePage />} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </AppShell>
    </IonReactRouter>
  );
}
