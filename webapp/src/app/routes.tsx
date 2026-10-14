import { IonReactRouter } from "@ionic/react-router";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { MovementsPage } from "../features/movements/MovementsPage";
import { RechargePage } from "../features/wallet/RechargePage";
import { AppShell } from "./AppShell";
import { ComingSoonPage } from "./ComingSoonPage";
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
          <Route path="/transferir" element={<ComingSoonPage title="Transferir" story="HU-06" />} />
          <Route path="/movimientos" element={<MovementsPage />} />
          <Route path="/perfil" element={<ComingSoonPage title="Perfil" story="HU-10" />} />
        </Routes>
      </AppShell>
    </IonReactRouter>
  );
}
